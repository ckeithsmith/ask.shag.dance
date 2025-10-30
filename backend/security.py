import time
from functools import wraps
from flask import request, jsonify

# Rate limiting storage (in-memory for simplicity)
request_counts = {}

# Blocked query patterns
BLOCKED_PATTERNS = [
    "show all", "list all", "dump", "export", "download",
    "return all", "full dataset", "complete records", 
    "csv format", "raw data", "entire database",
    "all contests", "every contest", "complete list",
    "bulk export", "data dump", "full archive"
]

def rate_limit(max_requests=10, window_minutes=1):
    """Rate limiting decorator"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            client_ip = request.remote_addr
            current_time = time.time()
            window_start = current_time - (window_minutes * 60)
            
            # Initialize or clean old requests for this IP
            if client_ip not in request_counts:
                request_counts[client_ip] = []
            
            # Remove old requests outside the window
            request_counts[client_ip] = [
                req_time for req_time in request_counts[client_ip] 
                if req_time > window_start
            ]
            
            # Check if limit exceeded
            if len(request_counts[client_ip]) >= max_requests:
                return jsonify({
                    "error": "Rate limit exceeded. Please wait before making more requests.",
                    "status": "rate_limited"
                }), 429
            
            # Add current request
            request_counts[client_ip].append(current_time)
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_input(query):
    """Validate user input for security"""
    query_lower = query.lower()
    
    # Check for blocked patterns
    for pattern in BLOCKED_PATTERNS:
        if pattern in query_lower:
            return False, f"Query contains restricted pattern: '{pattern}'"
    
    # Check query length
    if len(query) > 1000:
        return False, "Query too long. Please keep questions concise."
    
    return True, "Valid"

def filter_response(response_text):
    """Filter and limit response content"""
    # Limit response length
    max_length = 5000
    if len(response_text) > max_length:
        response_text = response_text[:max_length] + "\n\n[Response truncated for length]"
    
    # Check for potential data dumps (simple heuristic)
    lines = response_text.split('\n')
    if len(lines) > 100:  # Too many lines suggests data dump
        response_text = '\n'.join(lines[:50]) + "\n\n[Response truncated - too many results]"
    
    return response_text