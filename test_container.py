#!/usr/bin/env python3
"""
Test script to verify Ollama container functionality
"""
import requests
import json
import time
import sys

def test_ollama_health():
    """Test if Ollama is running and responsive"""
    print("🔍 Testing Ollama health...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama is running")
            return True
        else:
            print(f"❌ Ollama returned status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Ollama connection failed: {e}")
        return False

def test_available_models():
    """List available models"""
    print("\n📋 Checking available models...")
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            if models:
                print(f"✅ Found {len(models)} model(s):")
                for model in models:
                    name = model.get('name', 'Unknown')
                    size = model.get('size', 0)
                    size_gb = size / (1024**3) if size else 0
                    print(f"   • {name} ({size_gb:.1f} GB)")
                return [model.get('name', '') for model in models]
            else:
                print("❌ No models found")
                return []
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return []
    except Exception as e:
        print(f"❌ Error getting models: {e}")
        return []

def test_model_generation(model_name):
    """Test text generation with a specific model"""
    print(f"\n🤖 Testing text generation with {model_name}...")
    
    payload = {
        "model": model_name,
        "prompt": "Hello! Please introduce yourself in one sentence.",
        "stream": False,
        "options": {
            "temperature": 0.7,
            "num_predict": 50
        }
    }
    
    try:
        print("   Sending request...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            if generated_text:
                print("✅ Generation successful!")
                print(f"   Response: {generated_text.strip()}")
                return True
            else:
                print("❌ Empty response received")
                return False
        else:
            print(f"❌ Generation failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Generation error: {e}")
        return False

def test_runpod_handler():
    """Test the RunPod handler (if running)"""
    print("\n🏃 Testing RunPod handler...")
    
    # This would only work if the handler is running
    # For container testing, we'll skip this or make it optional
    print("   (Skipped - handler not running in test mode)")
    return True

def main():
    """Run all tests"""
    print("🚀 Ollama Container Test Suite")
    print("=" * 40)
    
    # Test 1: Health check
    if not test_ollama_health():
        print("\n❌ Ollama is not running. Make sure the container is started.")
        sys.exit(1)
    
    # Test 2: Check models
    models = test_available_models()
    if not models:
        print("\n❌ No models available. Check model installation.")
        sys.exit(1)
    
    # Test 3: Test generation with first available model
    target_model = None
    for model in models:
        if "dolphin-mistral-nemo" in model:
            target_model = model
            break
    
    if not target_model:
        target_model = models[0]
        print(f"\n⚠️  dolphin-mistral-nemo not found, using {target_model}")
    
    if not test_model_generation(target_model):
        print(f"\n❌ Model generation failed with {target_model}")
        sys.exit(1)
    
    # Test 4: RunPod handler
    test_runpod_handler()
    
    print("\n🎉 All tests passed!")
    print("✅ Container is ready for deployment")

if __name__ == "__main__":
    main() 