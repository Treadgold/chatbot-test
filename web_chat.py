from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from chatbot_component import ChatBot, ChatBotConfig
from stripe_payment import create_payment_intent, get_payment_intent, STRIPE_PUBLISHABLE_KEY
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid
from functools import wraps
import re
import logging
from logging.handlers import RotatingFileHandler
import threading
import time

# Try to import flask_limiter, but continue without it if not available
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    LIMITER_AVAILABLE = True
except ImportError:
    print("Warning: flask_limiter not installed. Rate limiting disabled.")
    LIMITER_AVAILABLE = False

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Configure logging
if not app.debug:
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Set up file logging
    file_handler = RotatingFileHandler('logs/chatbot_security.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    
    app.logger.setLevel(logging.INFO)
    app.logger.info('Chatbot application startup')

# Initialize rate limiter if available
if LIMITER_AVAILABLE:
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["1000 per day", "500 per hour"]  # Removed the restrictive "10 per minute"
    )
    limiter.init_app(app)
else:
    limiter = None

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

# Security middleware to block common attack patterns
@app.before_request
def block_malicious_requests():
    """Block common malicious request patterns"""
    path = request.path.lower()
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    user_agent = request.headers.get('User-Agent', 'Unknown')
    
    # Block WordPress-related paths
    wordpress_patterns = [
        'wp-', 'wordpress', 'xmlrpc.php', 'wp-admin', 'wp-content', 
        'wp-includes', 'wlwmanifest.xml', '.php', '/blog/', '/cms/'
    ]
    
    if any(pattern in path for pattern in wordpress_patterns):
        app.logger.warning(f'Blocked WordPress attack attempt from {client_ip}: {path} - User-Agent: {user_agent}')
        return jsonify({'error': 'Not found'}), 404
    
    # Block suspicious file extensions
    malicious_extensions = ['.asp', '.jsp', '.cgi', '.exe', '.bat']
    if any(path.endswith(ext) for ext in malicious_extensions):
        app.logger.warning(f'Blocked malicious file extension request from {client_ip}: {path} - User-Agent: {user_agent}')
        return jsonify({'error': 'Not found'}), 404

# Add security headers
@app.after_request
def add_security_headers(response):
    """Add security headers to all responses"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
    return response

# Input validation decorator
def validate_input(max_length=2048):
    """Decorator to validate and sanitize input"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if request.method == 'POST':
                data = request.get_json()
                if data and 'message' in data:
                    message = data['message']
                    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
                    
                    # Length check
                    if len(message) > max_length:
                        app.logger.warning(f'Message too long from {client_ip}: {len(message)} characters')
                        return jsonify({'error': 'Message too long'}), 400
                    
                    # Basic XSS prevention
                    if re.search(r'<[^>]*script|javascript:|data:|vbscript:', message, re.IGNORECASE):
                        app.logger.warning(f'XSS attempt blocked from {client_ip}: {message[:100]}...')
                        return jsonify({'error': 'Invalid input detected'}), 400
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# Initialize the chatbot with RunPod serverless configuration
cfg = ChatBotConfig(
    provider="runpod",  # Using RunPod serverless endpoint
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    runpod_endpoint=os.getenv('RUNPOD_ENDPOINT',
                            "https://api.runpod.ai/v2/vsgzvmdz6x1bei"),  # Base URL without /run
    runpod_api_key=os.getenv('RUNPOD_API_KEY'),
    max_iterations=3,
    min_joke_score=800,
    principles="""You are a Scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear""",
    timeout=0  # No timeout - wait indefinitely
)

chatbot = ChatBot(cfg)

# Global error handlers to ensure JSON responses
@app.errorhandler(500)
def internal_error(error):
    """Handle internal server errors with JSON response"""
    return jsonify({'error': 'Internal server error', 'details': str(error)}), 500

@app.errorhandler(400)
def bad_request(error):
    """Handle bad requests with JSON response"""
    return jsonify({'error': 'Bad request', 'details': str(error)}), 400

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors with JSON response for API endpoints"""
    if request.path.startswith('/api/') or request.path in ['/chat', '/simple-chat']:
        return jsonify({'error': 'Endpoint not found'}), 404
    # For other routes, return normal 404
    return render_template('404.html'), 404

@app.errorhandler(Exception)
def handle_exception(error):
    """Handle all other exceptions with JSON response for API endpoints"""
    if request.path.startswith('/api/') or request.path in ['/chat', '/simple-chat']:
        return jsonify({'error': 'Unexpected error', 'details': str(error)}), 500
    # For other routes, let Flask handle normally
    raise error

def get_session_conversation_history():
    """Get conversation history for current session, initialize if needed"""
    if 'session_id' not in session:
        session['session_id'] = str(uuid.uuid4())
        session['conversation_history'] = []
    return session.get('conversation_history', [])

def update_session_conversation_history(user_input, ai_response):
    """Update conversation history for current session"""
    history = get_session_conversation_history()
    history.append({
        'user': user_input,
        'ai': ai_response
    })
    # Keep only last 20 exchanges to prevent session bloat
    if len(history) > 20:
        history = history[-20:]
    session['conversation_history'] = history
    return history

# Add a global dictionary to store ongoing chat jobs
chat_jobs = {}

@app.route('/')
def index():
    """Serve the main chat page"""
    # Initialize session if needed
    get_session_conversation_history()
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
@validate_input()
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        
        print(f"[DEBUG] Received user_input: {user_input}")
        
        if not user_input.strip():
            print("[DEBUG] Empty message received.")
            return jsonify({'error': 'Empty message'}), 400
        
        # Get conversation history from session
        conversation_history = get_session_conversation_history()
        print(f"[DEBUG] Session conversation_history: {conversation_history}")
        
        # Get response from chatbot with session conversation history
        response = chatbot.chat(user_input, conversation_history)
        print(f"[DEBUG] Chatbot raw response: {response}")
        
        # Update session with new conversation exchange
        final_response = response.get('final_response', '')
        updated_history = update_session_conversation_history(user_input, final_response)
        
        # Ensure the frontend gets a 'response' key for display
        frontend_response = {
            'response': final_response,
            'debug': response,  # Send all debug info to frontend
            'session_id': session.get('session_id'),
            'conversation_history': updated_history
        }
        print(f"[DEBUG] Sending frontend_response: {frontend_response}")
        json_response = jsonify(frontend_response)
        print(f"[DEBUG] JSON response status: {json_response.status_code}")
        print(f"[DEBUG] JSON response headers: {dict(json_response.headers)}")
        return json_response
    
    except Exception as e:
        print(f"[DEBUG] Exception in /chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/simple-chat', methods=['POST'])
@validate_input()
def simple_chat():
    """Handle simple chat requests that return just the response text"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        
        if not user_input.strip():
            return jsonify({'error': 'Empty message'}), 400
        
        # Get conversation history from session
        conversation_history = get_session_conversation_history()
        
        # Get simple response from chatbot
        response = chatbot.get_simple_response(user_input, conversation_history)
        
        # Update session with new conversation exchange
        update_session_conversation_history(user_input, response)
        
        return jsonify({'response': response})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/clear-conversation', methods=['POST'])
def clear_conversation():
    """Clear conversation history for current session"""
    try:
        session['conversation_history'] = []
        return jsonify({'status': 'success', 'message': 'Conversation cleared'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get-conversation-history', methods=['GET'])
def get_conversation_history():
    """Get current conversation history for debugging"""
    try:
        history = get_session_conversation_history()
        return jsonify({
            'session_id': session.get('session_id'),
            'conversation_history': history,
            'history_length': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'chatbot': 'ready'})

# Stripe Payment Routes
@app.route('/payment')
def payment():
    """Show payment page"""
    amount = request.args.get('amount', 2000, type=int)  # Default $20.00
    return render_template('payment.html', 
                         amount=amount, 
                         publishable_key=STRIPE_PUBLISHABLE_KEY)

@app.route('/create-payment-intent', methods=['POST'])
def create_payment_intent_route():
    """Create a payment intent"""
    try:
        data = request.get_json()
        amount = data.get('amount', 2000)
        currency = data.get('currency', 'nzd')
        
        intent = create_payment_intent(amount, currency)
        
        if intent:
            return jsonify({
                'client_secret': intent.client_secret
            })
        else:
            return jsonify({'error': 'Failed to create payment intent'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/success')
def success():
    """Payment success page"""
    payment_intent_id = request.args.get('payment_intent_id')
    
    if payment_intent_id:
        intent = get_payment_intent(payment_intent_id)
        if intent:
            return render_template('success.html',
                                 payment_intent_id=payment_intent_id,
                                 amount=intent.amount,
                                 status=intent.status,
                                 created_at=datetime.fromtimestamp(intent.created).strftime('%Y-%m-%d %H:%M:%S'))
    
    # Fallback if no payment intent found
    return render_template('success.html',
                         payment_intent_id='Unknown',
                         amount=0,
                         status='Unknown',
                         created_at='Unknown')

@app.route('/cancel')
def cancel():
    """Payment cancelled page"""
    return render_template('cancel.html')

@app.route('/chat-async', methods=['POST'])
@validate_input()
def chat_async():
    """Start an async chat request and return job ID immediately"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        
        if not user_input.strip():
            return jsonify({'error': 'Empty message'}), 400
        
        # Generate a unique job ID
        job_id = str(uuid.uuid4())
        
        # Get conversation history from session (capture before background thread)
        conversation_history = get_session_conversation_history()
        current_session_id = session.get('session_id')
        
        # Initialize job status
        chat_jobs[job_id] = {
            'status': 'processing',
            'user_input': user_input,
            'conversation_history': conversation_history,
            'result': None,
            'error': None,
            'started_at': datetime.now(),
            'session_id': current_session_id
        }
        
        # Start processing in background thread
        def process_chat():
            try:
                response = chatbot.chat(user_input, conversation_history)
                
                # Store result (we'll update session when status is polled)
                final_response = response.get('final_response', '')
                
                # Store result
                chat_jobs[job_id]['status'] = 'completed'
                chat_jobs[job_id]['result'] = {
                    'response': final_response,
                    'debug': response,
                    'session_id': current_session_id,
                    'final_response': final_response,
                    'user_input': user_input
                }
                
            except Exception as e:
                chat_jobs[job_id]['status'] = 'failed'
                chat_jobs[job_id]['error'] = str(e)
        
        # Start background thread
        thread = threading.Thread(target=process_chat)
        thread.daemon = True
        thread.start()
        
        # Return job ID immediately
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Chat request started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/chat-status/<job_id>', methods=['GET'])
def chat_status(job_id):
    """Check the status of an async chat job"""
    try:
        if job_id not in chat_jobs:
            return jsonify({'error': 'Job not found'}), 404
        
        job = chat_jobs[job_id]
        
        response_data = {
            'job_id': job_id,
            'status': job['status'],
            'user_input': job['user_input'],
            'started_at': job['started_at'].isoformat()
        }
        
        if job['status'] == 'completed':
            result = job['result']
            response_data['result'] = result
            
            # Update session with the conversation exchange (now we have request context)
            if 'user_input' in result and 'final_response' in result:
                update_session_conversation_history(result['user_input'], result['final_response'])
                # Update the result with the current conversation history
                updated_history = get_session_conversation_history()
                response_data['result']['conversation_history'] = updated_history
            
            # Clean up completed job after 5 minutes
            def cleanup():
                time.sleep(300)  # 5 minutes
                if job_id in chat_jobs:
                    del chat_jobs[job_id]
            
            cleanup_thread = threading.Thread(target=cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
        elif job['status'] == 'failed':
            response_data['error'] = job['error']
            
        return jsonify(response_data)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Exempt the polling endpoint from rate limiting
if LIMITER_AVAILABLE:
    limiter.exempt(chat_status)

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Check if running in production
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        # Production configuration
        app.run(debug=False, host='127.0.0.1', port=8000)
    else:
        # Development configuration
        print("WARNING: Running in development mode. Set FLASK_ENV=production for production use.")
        app.run(debug=True, host='127.0.0.1', port=8000) 