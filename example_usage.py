#!/usr/bin/env python3
"""
Example usage of the ChatBot component

This script demonstrates different ways to use the chatbot component:
1. Basic usage with default configuration
2. Custom configuration
3. Simple text-only responses
4. Detailed responses with all data
5. Command-line interface
"""

from chatbot_component import ChatBot, ChatBotConfig

def example_basic_usage():
    """Example 1: Basic usage with default configuration"""
    print("=== Example 1: Basic Usage ===")
    
    # Create chatbot with default settings
    chatbot = ChatBot()
    
    # Get a simple response
    response = chatbot.get_simple_response("Tell me about the weather today")
    print(f"Simple Response: {response}")
    print()

def example_custom_config():
    """Example 2: Custom configuration"""
    print("=== Example 2: Custom Configuration ===")
    
    # Create custom configuration
    config = ChatBotConfig(
        model_name="llama2:latest",  # Different model
        base_url="http://localhost:11434",
        max_iterations=5,  # More joke iterations
        min_joke_score=900,  # Higher quality threshold
        principles="You are a helpful and friendly assistant who loves to tell educational jokes."
    )
    
    # Create chatbot with custom config
    chatbot = ChatBot(config)
    
    # Get detailed response
    response = chatbot.chat("Explain quantum physics")
    print(f"Final Response: {response['final_response']}")
    print(f"Generated Joke: {response['generated_joke']}")
    print(f"Joke Score: {response['joke_quality_score']}/1000")
    print()

def example_detailed_response():
    """Example 3: Detailed responses with all data"""
    print("=== Example 3: Detailed Response ===")
    
    chatbot = ChatBot()
    response = chatbot.chat("What's the meaning of life?")
    
    # Print all available data
    print(f"User Input: {response['user_input']}")
    print(f"AI Thoughts: {response['thoughts']}")
    print(f"Reasoning: {response['reasoning']}")
    print(f"Generated Joke: {response['generated_joke']}")
    print(f"Joke Quality Score: {response['joke_quality_score']}/1000")
    print(f"Score Reason: {response['score_reason']}")
    print(f"Final Response: {response['final_response']}")
    print(f"Response Tone: {response['response_tone']}")
    print()

def example_command_line():
    """Example 4: Command-line interface"""
    print("=== Example 4: Command Line Interface ===")
    print("Type 'quit' to exit")
    
    chatbot = ChatBot()
    
    while True:
        user_input = input("\nYou: ")
        if user_input.lower() in ['quit', 'exit', 'bye']:
            break
        
        response = chatbot.get_simple_response(user_input)
        print(f"Bot: {response}")

def example_web_integration():
    """Example 5: How to integrate with a web framework"""
    print("=== Example 5: Web Integration ===")
    
    # This is how you would use it in a web framework like Flask
    from flask import Flask, request, jsonify
    
    app = Flask(__name__)
    chatbot = ChatBot()
    
    @app.route('/api/chat', methods=['POST'])
    def api_chat():
        data = request.get_json()
        user_message = data.get('message', '')
        
        response = chatbot.chat(user_message)
        return jsonify(response)
    
    print("Web integration example created. You can use this in your Flask app.")
    print("The chatbot can be accessed via POST requests to /api/chat")
    print()

if __name__ == "__main__":
    print("ChatBot Component Examples")
    print("=" * 50)
    
    try:
        # Run examples
        example_basic_usage()
        example_custom_config()
        example_detailed_response()
        
        # Uncomment the line below to run the interactive command line interface
        # example_command_line()
        
        example_web_integration()
        
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure Ollama is running and the model is available.") 