
from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from chatbot_component import ChatBot, ChatBotConfig
from stripe_payment import create_payment_intent, get_payment_intent, STRIPE_PUBLISHABLE_KEY
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import uuid
from functools import wraps
import re
import logging
from logging.handlers import RotatingFileHandler
import threading
import time
import json
from pathlib import Path
from collections import defaultdict

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

# Chat logging configuration
CHAT_LOGGING_ENABLED = os.getenv('CHAT_LOGGING_ENABLED', 'true').lower() == 'true'
CHAT_ARCHIVE_DIR = os.getenv('CHAT_ARCHIVE_DIR', 'chat_archive')
ARCHIVE_SUMMARY_FILE = os.path.join(CHAT_ARCHIVE_DIR, 'archive_summary.json')

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
    response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline'; connect-src 'self'"
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

# Chat Archive Functions
def ensure_chat_archive_directory():
    """Create chat archive directory if it doesn't exist"""
    if CHAT_LOGGING_ENABLED:
        Path(CHAT_ARCHIVE_DIR).mkdir(exist_ok=True)

def generate_chat_filename(session_id, created_at, message_count):
    """Generate filename with metadata: YYYYMMDD_HHMM_count_sessionid.json"""
    timestamp = created_at.strftime('%Y%m%d_%H%M')
    short_session = session_id.split('-')[0]  # Use first part of UUID
    return f"{timestamp}_{message_count:03d}_{short_session}.json"

def save_conversation_to_archive(session_id, conversation_history):
    """Save conversation history to archive with metadata filename"""
    if not CHAT_LOGGING_ENABLED or not conversation_history:
        return
    
    try:
        ensure_chat_archive_directory()
        
        # Create chat data
        now = datetime.now()
        chat_data = {
            'session_id': session_id,
            'created_at': now.isoformat(),
            'last_updated': now.isoformat(),
            'message_count': len(conversation_history),
            'conversation_history': conversation_history,
            'metadata': {
                'total_user_chars': sum(len(exchange['user']) for exchange in conversation_history),
                'total_ai_chars': sum(len(exchange['ai']) for exchange in conversation_history),
                'avg_user_length': sum(len(exchange['user']) for exchange in conversation_history) / len(conversation_history) if conversation_history else 0,
                'avg_ai_length': sum(len(exchange['ai']) for exchange in conversation_history) / len(conversation_history) if conversation_history else 0,
            }
        }
        
        # Find existing file for this exact session ID
        existing_file = None
        existing_data = None
        
        for file_path in Path(CHAT_ARCHIVE_DIR).glob("*.json"):
            if file_path.name == 'archive_summary.json':
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    file_data = json.load(f)
                if file_data.get('session_id') == session_id:
                    existing_file = file_path
                    existing_data = file_data
                    break
            except Exception as e:
                app.logger.warning(f"Error reading archive file {file_path}: {e}")
                continue  # Skip corrupted files
        
        if existing_file and existing_data:
            # Verify this is actually the same conversation by checking the first message
            if (existing_data.get('conversation_history') and 
                conversation_history and 
                existing_data['conversation_history'][0]['user'] == conversation_history[0]['user']):
                
                # Update existing file - preserve original creation time
                filepath = existing_file
                chat_data['created_at'] = existing_data['created_at']
                app.logger.info(f"Updating existing conversation file: {filepath.name}")
            else:
                # Same session ID but different conversation - create new file with timestamp
                filename = generate_chat_filename(session_id, now, len(conversation_history))
                filepath = os.path.join(CHAT_ARCHIVE_DIR, filename)
                app.logger.info(f"Same session ID but different conversation - creating new file: {filename}")
        else:
            # Generate new filename for first message
            filename = generate_chat_filename(session_id, now, len(conversation_history))
            filepath = os.path.join(CHAT_ARCHIVE_DIR, filename)
            app.logger.info(f"Creating new conversation file: {filename}")
        
        # Save to JSON file
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(chat_data, f, indent=2, ensure_ascii=False)
        
        # Update archive summary
        update_archive_summary()
        
        app.logger.info(f"Saved conversation to archive: {filepath.name}")
        
    except Exception as e:
        app.logger.error(f"Failed to save conversation for session {session_id}: {e}")

def update_archive_summary():
    """Update the archive summary file with current statistics"""
    if not CHAT_LOGGING_ENABLED:
        return
    
    try:
        ensure_chat_archive_directory()
        
        # Scan all archive files
        archive_files = list(Path(CHAT_ARCHIVE_DIR).glob("*.json"))
        archive_files = [f for f in archive_files if f.name != 'archive_summary.json']
        
        # Initialize summary data
        summary = {
            'last_updated': datetime.now().isoformat(),
            'total_conversations': len(archive_files),
            'total_messages': 0,
            'total_user_chars': 0,
            'total_ai_chars': 0,
            'conversations_by_date': defaultdict(int),
            'messages_by_date': defaultdict(int),
            'conversations_by_hour': defaultdict(int),
            'conversation_files': []
        }
        
        # Process each conversation file
        for file_path in archive_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    chat_data = json.load(f)
                
                # Extract metadata from filename and content
                filename = file_path.name
                created_at = datetime.fromisoformat(chat_data['created_at'])
                date_str = created_at.strftime('%Y-%m-%d')
                hour = created_at.hour
                
                # Update counters
                message_count = chat_data['message_count']
                summary['total_messages'] += message_count
                summary['conversations_by_date'][date_str] += 1
                summary['messages_by_date'][date_str] += message_count
                summary['conversations_by_hour'][str(hour)] += 1
                
                if 'metadata' in chat_data:
                    summary['total_user_chars'] += chat_data['metadata'].get('total_user_chars', 0)
                    summary['total_ai_chars'] += chat_data['metadata'].get('total_ai_chars', 0)
                
                # Add file info for conversation list
                conversation_info = {
                    'filename': filename,
                    'session_id': chat_data['session_id'],
                    'created_at': chat_data['created_at'],
                    'message_count': message_count,
                    'first_user_message': chat_data['conversation_history'][0]['user'][:100] + '...' if chat_data['conversation_history'] else '',
                    'preview': chat_data['conversation_history'][0]['user'][:200] + '...' if chat_data['conversation_history'] else ''
                }
                summary['conversation_files'].append(conversation_info)
                
            except Exception as e:
                app.logger.error(f"Error processing archive file {file_path}: {e}")
                continue
        
        # Convert defaultdicts to regular dicts and sort
        summary['conversations_by_date'] = dict(sorted(summary['conversations_by_date'].items()))
        summary['messages_by_date'] = dict(sorted(summary['messages_by_date'].items()))
        summary['conversations_by_hour'] = dict(summary['conversations_by_hour'])
        
        # Sort conversation files by creation date (newest first)
        summary['conversation_files'].sort(key=lambda x: x['created_at'], reverse=True)
        
        # Calculate averages
        if summary['total_conversations'] > 0:
            summary['avg_messages_per_conversation'] = summary['total_messages'] / summary['total_conversations']
            summary['avg_user_chars_per_conversation'] = summary['total_user_chars'] / summary['total_conversations']
            summary['avg_ai_chars_per_conversation'] = summary['total_ai_chars'] / summary['total_conversations']
        else:
            summary['avg_messages_per_conversation'] = 0
            summary['avg_user_chars_per_conversation'] = 0
            summary['avg_ai_chars_per_conversation'] = 0
        
        # Save summary file
        with open(ARCHIVE_SUMMARY_FILE, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        app.logger.info(f"Updated archive summary: {summary['total_conversations']} conversations, {summary['total_messages']} messages")
        
    except Exception as e:
        app.logger.error(f"Failed to update archive summary: {e}")

def load_archive_summary():
    """Load the archive summary file"""
    try:
        if Path(ARCHIVE_SUMMARY_FILE).exists():
            with open(ARCHIVE_SUMMARY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        app.logger.error(f"Failed to load archive summary: {e}")
    
    # Return empty summary if file doesn't exist or can't be loaded
    return {
        'last_updated': datetime.now().isoformat(),
        'total_conversations': 0,
        'total_messages': 0,
        'total_user_chars': 0,
        'total_ai_chars': 0,
        'conversations_by_date': {},
        'messages_by_date': {},
        'conversations_by_hour': {},
        'conversation_files': [],
        'avg_messages_per_conversation': 0,
        'avg_user_chars_per_conversation': 0,
        'avg_ai_chars_per_conversation': 0
    }

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
    
    # Save to archive (every update)
    session_id = session.get('session_id')
    if session_id:
        save_conversation_to_archive(session_id, history)
    
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

# Chat Archive Analysis Routes
@app.route('/admin/analytics')
def analytics():
    """Show chat analytics dashboard"""
    summary = load_archive_summary()
    return render_template('analytics.html', summary=summary)

@app.route('/admin/refresh-analytics', methods=['POST'])
def refresh_analytics():
    """Manually refresh the analytics data"""
    try:
        update_archive_summary()
        return jsonify({'status': 'success', 'message': 'Analytics refreshed'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/conversation/<filename>')
def get_conversation(filename):
    """Get a specific conversation by filename"""
    try:
        # Security: only allow alphanumeric, dashes, underscores, and .json
        if not re.match(r'^[\w\-_]+\.json$', filename):
            return jsonify({'error': 'Invalid filename'}), 400
        
        filepath = os.path.join(CHAT_ARCHIVE_DIR, filename)
        
        if not os.path.exists(filepath):
            return jsonify({'error': 'Conversation not found'}), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            conversation_data = json.load(f)
        
        return jsonify(conversation_data)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/analytics-data')
def analytics_data():
    """Get analytics data as JSON"""
    try:
        summary = load_archive_summary()
        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
    # Create necessary directories
    os.makedirs('templates', exist_ok=True)
    ensure_chat_archive_directory()
    
    # Initialize archive summary on startup
    if CHAT_LOGGING_ENABLED:
        update_archive_summary()
    
    # Check if running in production
    is_production = os.getenv('FLASK_ENV') == 'production'
    
    if is_production:
        # Production configuration
        app.run(debug=False, host='127.0.0.1', port=8000)
    else:
        # Development configuration
        print("WARNING: Running in development mode. Set FLASK_ENV=production for production use.")
        app.run(debug=True, host='127.0.0.1', port=8000) 