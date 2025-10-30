from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os
from dotenv import load_dotenv
from data_loader import data_loader
from chat_handler import chat_handler
from security import rate_limit, validate_input, filter_response

# Load environment variables
load_dotenv()

app = Flask(__name__, static_folder=None)  # Disable Flask's default static handling
CORS(app)

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
    
    return jsonify({
        "status": "healthy",
        "data_loaded": data_loaded,
        "pdfs_loaded": pdfs_loaded,
        "pdf_count": len(data_loader.pdf_content),
        "api_configured": api_configured,
        "total_records": len(data_loader.csv_data) if data_loaded else 0
    })

@app.route('/api/ask', methods=['POST'])
@rate_limit(max_requests=10, window_minutes=1)
def ask_question():
    """Main chat endpoint"""
    try:
        data = request.get_json()
        user_question = data.get('question', '').strip()
        
        if not user_question:
            return jsonify({"error": "No question provided"}), 400
        
        # Security validation
        is_valid, validation_message = validate_input(user_question)
        if not is_valid:
            return jsonify({"error": validation_message}), 400
        
        # Process with Claude
        response_text = chat_handler.process_query(user_question)
        
        # Filter response
        filtered_response = filter_response(response_text)
        
        return jsonify({
            "answer": filtered_response,
            "status": "success"
        })
        
    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route('/api/suggested-questions', methods=['GET'])
def get_suggested_questions():
    """Get suggested questions for first-time users"""
    suggestions = [
        "Who has won the most CSA contests?",
        "What are the different competition divisions?", 
        "Show me the top 10 most successful couples",
        "What are the rules for advancing divisions?",
        "How many NSDC championships have been held?",
        "What contests happen most frequently?",
        "Who are the top judges in CSA competitions?",
        "Explain the CSA division system",
        "What is the NSDC required song list?",
        "Show me contest trends over the years"
    ]
    return jsonify({"suggestions": suggestions})

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