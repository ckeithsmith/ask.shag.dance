#!/usr/bin/env python3
"""
MINIMAL working version - just CSV + Claude + 50 message limit
Screw all the complex chart/analytics stuff - just make it work
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import sqlite3
import pandas as pd
from anthropic import Anthropic
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

app = Flask(__name__, static_folder='frontend/build', static_url_path='')
CORS(app)

# Simple daily limit tracker
class SimpleLimiter:
    def __init__(self, limit=50):
        self.limit = limit
        self.db_path = "simple_counter.db"
        self.init_db()
    
    def init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''CREATE TABLE IF NOT EXISTS daily_count (
                date TEXT PRIMARY KEY,
                count INTEGER DEFAULT 0
            )''')
    
    def can_send(self):
        today = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(self.db_path) as conn:
            result = conn.execute('SELECT count FROM daily_count WHERE date = ?', (today,)).fetchone()
            current = result[0] if result else 0
            return current < self.limit, current, self.limit - current
    
    def record_message(self):
        today = datetime.now().strftime('%Y-%m-%d')
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''INSERT INTO daily_count (date, count) VALUES (?, 1)
                           ON CONFLICT(date) DO UPDATE SET count = count + 1''', (today,))

# Initialize
limiter = SimpleLimiter(50)
claude_client = None

# Try to load CSV data
csv_data = None
try:
    csv_path = "data/Shaggy_Shag_Archives_Final.csv"
    if os.path.exists(csv_path):
        csv_data = pd.read_csv(csv_path)
        print(f"✅ Loaded CSV: {len(csv_data)} records")
    else:
        print(f"❌ CSV not found at {csv_path}")
except Exception as e:
    print(f"❌ Error loading CSV: {e}")

# Try to initialize Claude
try:
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        claude_client = Anthropic(api_key=api_key)
        print("✅ Claude client initialized")
    else:
        print("❌ ANTHROPIC_API_KEY not found")
except Exception as e:
    print(f"❌ Error initializing Claude: {e}")

@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "csv_loaded": csv_data is not None,
        "csv_records": len(csv_data) if csv_data is not None else 0,
        "claude_ready": claude_client is not None
    })

@app.route('/api/suggested-questions', methods=['GET'])
def suggested_questions():
    return jsonify({"suggestions": [
        "How many total dancers have danced in CSA in the last 10 years?",
        "Who has won the most contests overall?",
        "Who has won the most CSA contests?",
        "What judges are on the Top 20 list?",
        "How long does it take to progress from Amateur to Pro?",
        "Has anyone won every division of both NSDC and CSA?"
    ]})

@app.route('/api/ask', methods=['POST'])
def ask_question():
    try:
        # Check daily limit
        allowed, current, remaining = limiter.can_send()
        if not allowed:
            return jsonify({
                "error": "Daily limit reached",
                "message": f"Daily limit of {limiter.limit} messages reached. Try again tomorrow!",
                "current_count": current
            }), 429
        
        data = request.get_json()
        question = data.get('question', '').strip()
        
        if not question:
            return jsonify({"error": "No question provided"}), 400
        
        if not claude_client:
            return jsonify({"error": "AI service not available"}), 503
        
        if csv_data is None:
            return jsonify({"error": "Data not loaded"}), 503
        
        # Create context from CSV data
        data_info = f"""
You are a helpful assistant with access to CSA (Competitive Shaggers Association) contest data.
The data contains {len(csv_data)} contest records with columns: {', '.join(csv_data.columns.tolist())}

Sample records:
{csv_data.head(3).to_string()}

Answer questions about this shag dancing contest data based on what you can infer from the structure.
Be helpful and specific in your responses.
"""
        
        # Ask Claude
        response = claude_client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[{
                "role": "user", 
                "content": f"{data_info}\n\nQuestion: {question}"
            }]
        )
        
        # Record successful message
        limiter.record_message()
        
        return jsonify({
            "answer": response.content[0].text,
            "remaining_messages": remaining - 1
        })
        
    except Exception as e:
        logging.error(f"Error: {e}")
        return jsonify({"error": f"Error processing question: {str(e)}"}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)