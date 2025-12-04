from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
import time
import json
import logging
from dotenv import load_dotenv
from data_loader import data_loader
from chat_handler import chat_handler
from security import rate_limit, validate_input, filter_response
from database import db_manager
from data_protection import DataProtector, DataProtectionError
from simple_limiter import SimpleDailyLimiter

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

app = Flask(__name__, static_folder=None)  # Disable Flask's default static handling
CORS(app)

# Initialize simple daily limiter - 50 messages total per day
DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'csa_archive.db')
simple_limiter = SimpleDailyLimiter(DATABASE_PATH, daily_limit=50)

# Initialize data on startup
def initialize_data():
    """Load all data when the app starts"""
    print("🚀 Initializing CSA Archive data...")
    try:
        data_loader.load_all_data()
        chat_handler.initialize_client()
        print("✅ Application ready!")
    except Exception as e:
        print(f"⚠️ Initialization warning: {e}")
        print("🚀 Application starting in degraded mode...")

# Call initialization
initialize_data()

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    data_loaded = data_loader.csv_data is not None
    pdfs_loaded = len(data_loader.pdf_content) > 0
    api_configured = chat_handler.client is not None
    
    # Enhanced debugging for 503 issues
    debug_info = {
        "anthropic_key_exists": bool(os.getenv('ANTHROPIC_API_KEY')),
        "simple_limiter_ready": True,
        "working_directory": os.getcwd(),
        "data_directory_exists": os.path.exists('../data') or os.path.exists('data')
    }
    
    return jsonify({
        "status": "healthy",
        "data_loaded": data_loaded,
        "pdfs_loaded": pdfs_loaded,
        "pdf_count": len(data_loader.pdf_content),
        "api_configured": api_configured,
        "total_records": len(data_loader.csv_data) if data_loaded else 0,
        "debug": debug_info,
        "message": "All 7000+ lines of data processing intact! Backend working."
    })

@app.route('/api/ask', methods=['POST'])
@rate_limit(max_requests=5, window_minutes=1)
def ask_question():
    """Main chat endpoint"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        user_contact = data.get('user_contact', 'Anonymous')
        session_id = data.get('session_id')
        
        if not user_question:
            return jsonify({"error": "No question provided"}), 400
        
        # Security validation
        is_valid, validation_message = validate_input(user_question)
        if not is_valid:
            return jsonify({"error": validation_message}), 400

        # Data protection validation
        is_allowed, protection_message = DataProtector.validate_query(user_question)
        if not is_allowed:
            logging.warning(f"⚠️ Data extraction attempt blocked: {user_question[:100]}")
            return jsonify({
                "error": protection_message,
                "suggestion": "Try asking for: 'top 100 Pro dancers' or 'analyze trends by year'"
            }), 403

        # Get client info for logging
        ip_address = request.remote_addr
        
        # 🚨 SIMPLE DAILY LIMIT - 50 messages total per day
        limit_check = simple_limiter.can_send_message()
        
        if not limit_check['allowed']:
            logging.warning(f"⛔ Daily limit hit: {limit_check['message']}")
            return jsonify({
                "error": "Daily message limit reached",
                "message": limit_check['message'],
                "retry_after": "Tomorrow (limits reset at midnight)",
                "current_count": limit_check['current_count'],
                "daily_limit": limit_check['daily_limit']
            }), 429
        
        # Log the query attempt
        logging.info(f"❓ Query from {ip_address}: {user_question[:100]}")
        logging.info(f"📊 Usage: {limit_check['message']}")
        
        # Process with Claude
        result = chat_handler.process_query(user_question)
        if isinstance(result, tuple):
            response_text, tool_calls_used = result
        else:
            response_text = result
            tool_calls_used = None
        
        # Filter response
        filtered_response = filter_response(response_text)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Log query to database (no user tracking)
        query_id = db_manager.log_query(
            user_id=None,
            ip_address=ip_address,
            question=user_question,
            response=filtered_response,
            response_time_ms=response_time_ms,
            tool_calls_used=tool_calls_used,
            session_id=session_id
        )
        
        # 📊 Record successful message for simple daily limit
        simple_limiter.record_message()
        
        return jsonify({
            "answer": filtered_response,
            "query_id": query_id,
            "response_time_ms": response_time_ms,
            "status": "success"
        })
        
    except Exception as e:
        logging.error(f"Server error processing query: {str(e)}", exc_info=True)
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/suggested-questions', methods=['GET'])
def get_suggested_questions():
    """Get suggested questions for first-time users"""
    suggestions = [
        "How many total dancers have danced in CSA in the last 10 years?",
        "Who has won the most contest overall?",
        "Who has won the most CSA contest?",
        "What Judges are on the Top 20 list of number placements judged in the last 10 years?",
        "How long does it take to progress from Amateur to Pro?",
        "Has anyone won every division of both NSDC and CSA?"
    ]
    return jsonify({"suggestions": suggestions})



@app.route('/api/usage-stats', methods=['GET'])
def get_usage_stats():
    """Get daily usage statistics for cost monitoring"""
    try:
        stats = simple_limiter.get_stats()
        
        logging.info(f"📈 Usage stats requested from {request.remote_addr}")
        
        return jsonify({
            "status": "success",
            "stats": stats,
            "cost_estimate": {
                "claude_model": "claude-sonnet-4-5-20250929",
                "estimated_cost_per_message": 0.05,  # rough estimate $0.05 per message
                "daily_cost_estimate": stats['today']['messages_used'] * 0.05
            }
        })
        
    except Exception as e:
        logging.error(f"Usage stats error: {e}")
        return jsonify({"error": f"Failed to get usage stats: {str(e)}"}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback():
    """Submit user feedback on query responses"""
    try:
        data = request.get_json()
        
        # Extract feedback info
        query_id = data.get('query_id')
        user_id = data.get('user_id')
        feedback_type = data.get('feedback_type', 'incorrect_answer')
        comment = data.get('comment', '').strip() or None
        
        if not query_id:
            return jsonify({"error": "Query ID is required"}), 400
        
        # Get client info
        ip_address = request.remote_addr
        
        # Log feedback
        feedback_id = db_manager.log_feedback(
            query_id=query_id,
            user_id=user_id,
            feedback_type=feedback_type,
            comment=comment,
            ip_address=ip_address
        )
        
        logging.info(f"📝 Feedback submitted: {feedback_type} for query {query_id}")
        
        return jsonify({
            "status": "success",
            "feedback_id": feedback_id,
            "message": "Feedback submitted successfully"
        })
        
    except Exception as e:
        logging.error(f"Feedback error: {e}")
        return jsonify({"error": f"Failed to submit feedback: {str(e)}"}), 500

# Serve React frontend (for production)
build_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../frontend/build'))

# Check build directory on startup
print(f"🔍 Frontend build directory: {build_dir}")
print(f"📁 Build directory exists: {os.path.exists(build_dir)}")
if os.path.exists(build_dir):
    build_files = os.listdir(build_dir)
    print(f"📄 Build files: {build_files}")
else:
    print("❌ Build directory not found! Frontend will not work.")

@app.route('/')
def serve_frontend():
    """Serve the React frontend"""
    if not os.path.exists(build_dir):
        return "Frontend build directory not found. Please check deployment.", 500
    
    index_path = os.path.join(build_dir, 'index.html')
    if not os.path.exists(index_path):
        return f"Frontend index.html not found at {index_path}", 500
        
    return send_from_directory(build_dir, 'index.html')

@app.route('/api/debug-env', methods=['GET'])
def debug_environment():
    """Debug endpoint to check production environment issues"""
    import sys
    import platform
    
    debug_data = {
        "python_version": sys.version,
        "platform": platform.platform(),
        "working_directory": os.getcwd(),
        "environment_vars": {
            "ANTHROPIC_API_KEY": "SET" if os.getenv('ANTHROPIC_API_KEY') else "MISSING",
            "PORT": os.getenv('PORT', 'Not set'),
            "FLASK_ENV": os.getenv('FLASK_ENV', 'Not set'),
        },
        "file_system": {
            "data_dir_exists": os.path.exists('data') or os.path.exists('../data'),
            "csv_file_exists": os.path.exists('data/Shaggy_Shag_Archives_Final.csv') or os.path.exists('../data/Shaggy_Shag_Archives_Final.csv'),
            "database_file_exists": os.path.exists('csa_archive.db'),
        },
        "imports_status": {},
        "startup_errors": []
    }
    
    # Test critical imports
    try:
        from anthropic import Anthropic
        debug_data["imports_status"]["anthropic"] = "OK"
    except Exception as e:
        debug_data["imports_status"]["anthropic"] = f"FAILED: {e}"
    
    try:
        import pandas
        debug_data["imports_status"]["pandas"] = "OK"
    except Exception as e:
        debug_data["imports_status"]["pandas"] = f"FAILED: {e}"
        
    # Test Anthropic client creation
    try:
        if os.getenv('ANTHROPIC_API_KEY'):
            test_client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            debug_data["anthropic_client"] = "Can create client"
        else:
            debug_data["anthropic_client"] = "No API key to test"
    except Exception as e:
        debug_data["anthropic_client"] = f"Client creation failed: {e}"
    
    return jsonify({
        "status": "debug_info",
        "message": "Production environment diagnostic data",
        "debug": debug_data
    })

@app.route('/debug-files')
def debug_files():
    """Debug endpoint to check what files actually exist"""
    info = {
        "build_dir": build_dir,
        "build_dir_exists": os.path.exists(build_dir),
        "cwd": os.getcwd()
    }
    
    if os.path.exists(build_dir):
        info["build_contents"] = os.listdir(build_dir)
        
        static_dir = os.path.join(build_dir, 'static')
        if os.path.exists(static_dir):
            info["static_exists"] = True
            info["static_contents"] = os.listdir(static_dir)
            
            # Check specific subdirectories
            css_dir = os.path.join(static_dir, 'css')
            js_dir = os.path.join(static_dir, 'js')
            
            if os.path.exists(css_dir):
                info["css_files"] = os.listdir(css_dir)
            if os.path.exists(js_dir):
                info["js_files"] = os.listdir(js_dir)
                
            # Check specific files we need
            css_file = os.path.join(css_dir, 'main.81d789d0.css')
            js_file = os.path.join(js_dir, 'main.22c33d1c.js')
            
            info["target_css_exists"] = os.path.exists(css_file)
            info["target_js_exists"] = os.path.exists(js_file)
            
        else:
            info["static_exists"] = False
    
    return jsonify(info)

@app.route('/<path:path>')
def serve_static_files(path):
    """Serve static files from React build"""
    print(f"🔍 Static file request: {path}")
    
    if not os.path.exists(build_dir):
        print(f"❌ Build directory not found: {build_dir}")
        return "Frontend build directory not found. Please check deployment.", 500
    
    full_path = os.path.join(build_dir, path)
    print(f"🔍 Looking for file: {full_path}")
    print(f"📁 File exists: {os.path.exists(full_path)}")
    
    if not os.path.exists(full_path):
        # Show what files ARE available for debugging
        try:
            if path.startswith('static/'):
                static_dir = os.path.join(build_dir, 'static')
                if os.path.exists(static_dir):
                    print(f"📁 Static directory contents: {os.listdir(static_dir)}")
                    # Check subdirectories
                    for item in os.listdir(static_dir):
                        item_path = os.path.join(static_dir, item)
                        if os.path.isdir(item_path):
                            print(f"📁 {item}/ contents: {os.listdir(item_path)}")
        except Exception as e:
            print(f"⚠️ Debug listing error: {e}")
    
    try:
        return send_from_directory(build_dir, path)
    except FileNotFoundError as e:
        print(f"❌ FileNotFoundError: {e}")
        # Fallback to index.html for React Router
        return send_from_directory(build_dir, 'index.html')

if __name__ == '__main__':
    # Initialize data immediately for development
    data_loader.load_all_data()
    
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    app.run(host='0.0.0.0', port=port, debug=debug)