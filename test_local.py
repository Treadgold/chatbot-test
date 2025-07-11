#!/usr/bin/env python3
"""
Local test script for the Ollama handler before RunPod deployment
"""
import json
from ollama_handler import handler

def test_local():
    # Load test input
    with open('test_input.json', 'r') as f:
        test_event = json.load(f)
    
    print("Testing Ollama handler locally...")
    print(f"Input: {json.dumps(test_event, indent=2)}")
    print("\n" + "="*50 + "\n")
    
    # Test the handler
    try:
        result = handler(test_event)
        print("Handler Response:")
        print(json.dumps(result, indent=2))
        
        if "error" in result:
            print(f"\n❌ Error: {result['error']}")
        else:
            print(f"\n✅ Success! Generated response: {result.get('response', '')[:100]}...")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_local() 