#!/usr/bin/env python3
"""
Example script showing how to use the new runpod_ollama_proxy provider
with your RunPod Ollama endpoint.
"""

from chatbot_component import ChatBot, ChatBotConfig

def main():
    # Configure the chatbot to use your RunPod Ollama proxy endpoint
    config = ChatBotConfig(
        provider="runpod_ollama_proxy",
        model_name="CognitiveComputations/dolphin-mistral-nemo:latest",  # Use the exact model name from your endpoint
        runpod_ollama_proxy_url="https://vc9fx2v79484c9-11434.proxy.runpod.net",
        principles="You are a helpful and friendly AI assistant who likes to make jokes.",
        max_iterations=3,
        min_joke_score=800
    )
    
    # Create the chatbot instance
    chatbot = ChatBot(config)
    
    # Test the chatbot
    print("🤖 Chatbot initialized with RunPod Ollama proxy!")
    print("Type 'quit' to exit\n")
    
    conversation_history = []
    
    while True:
        user_input = input("You: ").strip()
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("🤖 Goodbye!")
            break
        
        if not user_input:
            continue
        
        try:
            # Get response from chatbot
            result = chatbot.chat(user_input, conversation_history)
            
            if result.get("status") == "error":
                print(f"❌ Error: {result.get('error', 'Unknown error')}")
            else:
                print(f"🤖 {result.get('final_response', 'No response')}")
                conversation_history = result.get('conversation_history', [])
                
                # Optional: Print debug info
                print(f"💭 Thoughts: {result.get('thoughts', '')}")
                print(f"🎭 Tone: {result.get('response_tone', '')}")
                print()
                
        except Exception as e:
            print(f"❌ Exception: {e}")

if __name__ == "__main__":
    main() 