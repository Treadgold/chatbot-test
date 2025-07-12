#!/usr/bin/env python3
"""
Test script to verify session isolation in the web chat application.
This script simulates multiple browser sessions to ensure each maintains its own conversation context.
"""

import requests
import json
import time

def test_session_isolation():
    """Test that different sessions maintain separate conversation histories"""
    
    base_url = "http://127.0.0.1:8000"
    
    print("🧪 Testing Session Isolation")
    print("=" * 50)
    
    # Create two different sessions (simulating different browsers)
    session1 = requests.Session()
    session2 = requests.Session()
    
    # Test 1: Initialize sessions
    print("\n1. Initializing sessions...")
    
    # Visit the main page to initialize sessions
    response1 = session1.get(f"{base_url}/")
    response2 = session2.get(f"{base_url}/")
    
    print(f"Session 1 status: {response1.status_code}")
    print(f"Session 2 status: {response2.status_code}")
    
    # Test 2: Get initial conversation history
    print("\n2. Getting initial conversation history...")
    
    history1 = session1.get(f"{base_url}/get-conversation-history").json()
    history2 = session2.get(f"{base_url}/get-conversation-history").json()
    
    print(f"Session 1 ID: {history1['session_id']}")
    print(f"Session 2 ID: {history2['session_id']}")
    print(f"Session 1 history length: {history1['history_length']}")
    print(f"Session 2 history length: {history2['history_length']}")
    
    # Verify sessions are different
    assert history1['session_id'] != history2['session_id'], "Sessions should have different IDs"
    print("✅ Session IDs are different")
    
    # Test 3: Send messages to session 1
    print("\n3. Sending messages to Session 1...")
    
    messages_session1 = [
        "Hello, I'm from session 1",
        "What's the weather like?",
        "Tell me a joke"
    ]
    
    for i, message in enumerate(messages_session1, 1):
        print(f"   Sending message {i}: {message}")
        response = session1.post(f"{base_url}/chat", 
                               json={"message": message})
        data = response.json()
        print(f"   Response: {data['response'][:50]}...")
        time.sleep(0.5)  # Small delay between messages
    
    # Test 4: Send messages to session 2
    print("\n4. Sending messages to Session 2...")
    
    messages_session2 = [
        "Hello, I'm from session 2",
        "What's your favorite color?",
        "How are you today?"
    ]
    
    for i, message in enumerate(messages_session2, 1):
        print(f"   Sending message {i}: {message}")
        response = session2.post(f"{base_url}/chat", 
                               json={"message": message})
        data = response.json()
        print(f"   Response: {data['response'][:50]}...")
        time.sleep(0.5)  # Small delay between messages
    
    # Test 5: Check conversation histories are isolated
    print("\n5. Verifying conversation isolation...")
    
    history1_after = session1.get(f"{base_url}/get-conversation-history").json()
    history2_after = session2.get(f"{base_url}/get-conversation-history").json()
    
    print(f"Session 1 history length: {history1_after['history_length']}")
    print(f"Session 2 history length: {history2_after['history_length']}")
    
    # Verify each session has its own conversation history
    assert history1_after['history_length'] == 3, f"Session 1 should have 3 messages, got {history1_after['history_length']}"
    assert history2_after['history_length'] == 3, f"Session 2 should have 3 messages, got {history2_after['history_length']}"
    print("✅ Both sessions have correct message counts")
    
    # Test 6: Verify conversation content isolation
    print("\n6. Verifying conversation content isolation...")
    
    # Get the actual conversation histories
    conv1 = history1_after['conversation_history']
    conv2 = history2_after['conversation_history']
    
    print("Session 1 conversation:")
    for i, exchange in enumerate(conv1, 1):
        print(f"   {i}. User: {exchange['user']}")
        print(f"      AI: {exchange['ai'][:50]}...")
    
    print("\nSession 2 conversation:")
    for i, exchange in enumerate(conv2, 1):
        print(f"   {i}. User: {exchange['user']}")
        print(f"      AI: {exchange['ai'][:50]}...")
    
    # Verify the conversations are different
    assert conv1[0]['user'] != conv2[0]['user'], "First messages should be different"
    print("✅ Conversation contents are isolated")
    
    # Test 7: Test clear conversation functionality
    print("\n7. Testing clear conversation...")
    
    # Clear session 1
    clear_response = session1.post(f"{base_url}/clear-conversation")
    clear_data = clear_response.json()
    print(f"Clear response: {clear_data}")
    
    # Verify session 1 is cleared but session 2 is not
    history1_cleared = session1.get(f"{base_url}/get-conversation-history").json()
    history2_unchanged = session2.get(f"{base_url}/get-conversation-history").json()
    
    print(f"Session 1 after clear: {history1_cleared['history_length']} messages")
    print(f"Session 2 after clear: {history2_unchanged['history_length']} messages")
    
    assert history1_cleared['history_length'] == 0, "Session 1 should be cleared"
    assert history2_unchanged['history_length'] == 3, "Session 2 should remain unchanged"
    print("✅ Clear conversation works correctly")
    
    print("\n🎉 All session isolation tests passed!")
    print("=" * 50)

if __name__ == "__main__":
    try:
        test_session_isolation()
    except requests.exceptions.ConnectionError:
        print("❌ Error: Could not connect to the Flask app.")
        print("Make sure the app is running on http://127.0.0.1:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc() 