from flask import Flask, render_template, request, jsonify, redirect, url_for
from chatbot_component import ChatBot, ChatBotConfig
from stripe_payment import create_payment_intent, get_payment_intent, STRIPE_PUBLISHABLE_KEY
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your-secret-key-here')

# Initialize the chatbot with default configuration
# You can customize these settings
config = ChatBotConfig(
    model_name="dolphin-mistral-nemo:latest",
    base_url="http://localhost:11434",
    max_iterations=3,
    min_joke_score=800,
    principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
)



cfg = ChatBotConfig(
    provider="runpod",  # Using standard RunPod vLLM endpoint
    runpod_endpoint=os.getenv('RUNPOD_ENDPOINT', "https://api.runpod.ai/v2/5hgggs410ddltq"),  # Base URL without /run
    runpod_api_key=os.getenv('RUNPOD_API_KEY'),
    principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
)
#chatbot = ChatBot(cfg)
#print(bot.get_simple_response("List 20 cities in Europe"))

chatbot = ChatBot(config)

@app.route('/')
def index():
    """Serve the main chat page"""
    return render_template('chat.html')

@app.route('/chat', methods=['POST'])
def chat():
    """Handle chat requests"""
    try:
        data = request.get_json()
        user_input = data.get('message', '')
        conversation_history = data.get('conversation_history', [])
        
        print(f"[DEBUG] Received user_input: {user_input}")
        print(f"[DEBUG] Received conversation_history: {conversation_history}")
        
        if not user_input.strip():
            print("[DEBUG] Empty message received.")
            return jsonify({'error': 'Empty message'}), 400
        
        # --- FIX: Convert OpenAI-style history to backend format ---
        def convert_history(history):
            converted = []
            i = 0
            while i < len(history):
                if history[i].get('role') == 'user':
                    user_msg = history[i].get('content', '')
                    ai_msg = ""
                    if i + 1 < len(history) and history[i+1].get('role') == 'assistant':
                        ai_msg = history[i+1].get('content', '')
                        i += 1
                    converted.append({'user': user_msg, 'ai': ai_msg})
                i += 1
            return converted
        conversation_history = convert_history(conversation_history)
        # --- END FIX ---
        
        # Get response from chatbot with conversation history
        response = chatbot.chat(user_input, conversation_history)
        print(f"[DEBUG] Chatbot raw response: {response}")
        
        # Ensure the frontend gets a 'response' key for display
        frontend_response = {
            'response': response.get('final_response', ''),
            'debug': response,  # Optionally send all debug info to frontend for now
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
        
        # Get simple response from chatbot
        response = chatbot.get_simple_response(user_input)
        
        return jsonify({'response': response})
    
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
    app.run(debug=True, host='0.0.0.0', port=80) 