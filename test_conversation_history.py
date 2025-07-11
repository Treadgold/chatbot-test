#!/usr/bin/env python3
"""
Test script to verify conversation history functionality
"""

from chatbot_component import ChatBot, ChatBotConfig

def test_conversation_history():
    print("Testing conversation history functionality...")
    
    # Create chatbot
    chatbot = ChatBot()
    
    # Simulate a conversation
    conversation_history = []
    
    # First exchange
    print("\n=== Exchange 1 ===")
    response1 = chatbot.chat("Hello, my name is Alice", conversation_history)
    print(f"User: Hello, my name is Alice")
    print(f"Bot: {response1['final_response']}")
    conversation_history = response1['conversation_history']
    
    # Second exchange - should remember the name
    print("\n=== Exchange 2 ===")
    response2 = chatbot.chat("What's my name?", conversation_history)
    print(f"User: What's my name?")
    print(f"Bot: {response2['final_response']}")
    conversation_history = response2['conversation_history']
    
    # Third exchange - should build on previous context
    print("\n=== Exchange 3 ===") 
    response3 = chatbot.chat("Tell me a joke about my name", conversation_history)
    print(f"User: Tell me a joke about my name")
    print(f"Bot: {response3['final_response']}")
    conversation_history = response3['conversation_history']
    
    # Print conversation history
    print("\n=== Conversation History ===")
    for i, exchange in enumerate(conversation_history, 1):
        print(f"{i}. User: {exchange['user']}")
        print(f"   AI: {exchange['ai']}")
    
    print(f"\nTotal exchanges: {len(conversation_history)}")

if __name__ == "__main__":
    test_conversation_history() 