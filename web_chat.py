from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from chatbot_component import ChatBot, ChatBotConfig
from stripe_payment import create_payment_intent, get_payment_intent, STRIPE_PUBLISHABLE_KEY
import os
from dotenv import load_dotenv
from datetime import datetime
import uuid

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize the chatbot with default configuration
# You can customize these settings
# config = ChatBotConfig(
#     model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
#     base_url="http://localhost:11434",
#     max_iterations=3,
#     min_joke_score=800,
#     principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
# )

config = ChatBotConfig(
    model_name="nemo-custom:latest",
    base_url="https://vc9fx2v79484c9-11434.proxy.runpod.net/",
    max_iterations=3,
    min_joke_score=800,
    principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
)

# nemo-custom:latest

cfg = ChatBotConfig(
    provider="runpod",  # Using standard RunPod vLLM endpoint
    runpod_endpoint=os.getenv('RUNPOD_ENDPOINT', "https://api.runpod.ai/v2/5hgggs410ddltq"),  # Base URL without /run
    runpod_api_key=os.getenv('RUNPOD_API_KEY'),
    principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
)
#chatbot = ChatBot(cfg)
#print(bot.get_simple_response("List 20 cities in Europe"))

chatbot = ChatBot(config)

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

@app.route('/')
def index():
    """Serve the main chat page"""
    # Initialize session if needed
    get_session_conversation_history()
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
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
            'debug': response,  # Optionally send all debug info to frontend for now
            'session_id': session.get('session_id'),
            'conversation_history': updated_history  # Send updated history back to frontend
        }
        print(f"[DEBUG] Sending frontend_response: {frontend_response}")
        return jsonify(frontend_response)
    
    except Exception as e:
        print(f"[DEBUG] Exception in /chat: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/simple-chat', methods=['POST'])
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

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Run the Flask app
    app.run(debug=True, host='127.0.0.1', port=8000) 