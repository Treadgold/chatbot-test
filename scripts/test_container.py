#!/usr/bin/env python3
"""
Test script to verify the Ollama handler works locally
"""
import requests
import json
import time
import sys

def test_health_check():
    """Test the health check endpoint"""
    print("🧪 Testing health check...")
    
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama API is responding")
            return True
        else:
            print(f"❌ Ollama API error: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama API connection failed: {e}")
        return False

def test_generate():
    """Test the generate endpoint"""
    print("🧪 Testing generate endpoint...")
    
    payload = {
        "model": "CognitiveComputations/dolphin-mistral-nemo:latest",
        "prompt": "Hello, this is a test. Please respond briefly.",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 50
        }
    }
    
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            print(f"✅ Generate test successful: {len(generated_text)} characters")
            print(f"Response: {generated_text[:100]}...")
            return True
        else:
            print(f"❌ Generate test failed: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ Generate test error: {e}")
        return False

def main():
    print("🚀 Testing Ollama Container")
    print("=" * 40)
    
    # Test 1: Health check
    if not test_health_check():
        print("❌ Health check failed")
        sys.exit(1)
    
    # Test 2: Generate
    if not test_generate():
        print("❌ Generate test failed")
        sys.exit(1)
    
    print("✅ All tests passed!")

if __name__ == "__main__":
    main() 