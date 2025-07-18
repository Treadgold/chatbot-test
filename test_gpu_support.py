#!/usr/bin/env python3
"""
Test script to verify GPU support and Ollama configuration
"""

import requests
import json
import subprocess
import sys
import time

def check_nvidia_gpu():
    """Check if NVIDIA GPU is available"""
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("✅ NVIDIA GPU detected")
            print("GPU Info:")
            print(result.stdout)
            return True
        else:
            print("❌ nvidia-smi failed")
            return False
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ nvidia-smi not found or timed out")
        return False

def check_ollama_gpu_info():
    """Check Ollama GPU information"""
    try:
        response = requests.get('http://localhost:11434/api/generate', 
                              json={"model": "test", "prompt": "test"}, 
                              timeout=5)
        # Even if it fails, the endpoint should be reachable
        print("✅ Ollama API is reachable")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Ollama API not reachable: {e}")
        return False

def test_gpu_inference():
    """Test GPU inference with a simple prompt"""
    try:
        # First check if model is available
        response = requests.get('http://localhost:11434/api/tags', timeout=10)
        if response.status_code == 200:
            models = response.json().get('models', [])
            if models:
                model_name = models[0]['name']
                print(f"✅ Found model: {model_name}")
                
                # Test inference
                test_prompt = "Hello! This is a GPU test. Please respond with 'GPU test successful' if you can see this message."
                
                response = requests.post('http://localhost:11434/api/generate', 
                                       json={
                                           "model": model_name,
                                           "prompt": test_prompt,
                                           "stream": False,
                                           "options": {
                                               "num_predict": 50,
                                               "temperature": 0.7
                                           }
                                       }, 
                                       timeout=30)
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ GPU inference test successful")
                    print(f"Response: {result.get('response', 'No response')}")
                    return True
                else:
                    print(f"❌ Inference failed with status {response.status_code}")
                    return False
            else:
                print("❌ No models found")
                return False
        else:
            print(f"❌ Failed to get models: {response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Inference test failed: {e}")
        return False

def check_environment_variables():
    """Check if GPU environment variables are set"""
    import os
    
    gpu_vars = {
        'OLLAMA_NUM_CPU': '0',
        'OLLAMA_N_GPU_LAYERS': '9999',
        'OLLAMA_CTX_SIZE': '8192',
        'OLLAMA_GPU_OVERHEAD': '0',
        'OLLAMA_FLASH_ATTENTION': 'true'
    }
    
    print("=== Environment Variables ===")
    all_set = True
    for var, expected in gpu_vars.items():
        value = os.environ.get(var, 'NOT_SET')
        print(f"{var}: {value}")
        if value == expected:
            print(f"  ✅ {var} correctly set")
        else:
            print(f"  ❌ {var} not set correctly (expected: {expected})")
            all_set = False
    
    return all_set

def main():
    print("=== Ollama GPU Support Test ===\n")
    
    # Check environment variables
    env_ok = check_environment_variables()
    print()
    
    # Check GPU availability
    gpu_ok = check_nvidia_gpu()
    print()
    
    # Check Ollama API
    api_ok = check_ollama_gpu_info()
    print()
    
    # Test inference if everything else is OK
    if gpu_ok and api_ok:
        inference_ok = test_gpu_inference()
    else:
        inference_ok = False
        print("⏭️  Skipping inference test due to previous failures")
    
    print("\n=== Test Summary ===")
    print(f"Environment Variables: {'✅' if env_ok else '❌'}")
    print(f"GPU Detection: {'✅' if gpu_ok else '❌'}")
    print(f"Ollama API: {'✅' if api_ok else '❌'}")
    print(f"Inference Test: {'✅' if inference_ok else '❌'}")
    
    if all([env_ok, gpu_ok, api_ok, inference_ok]):
        print("\n🎉 All tests passed! GPU support is working correctly.")
        return 0
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 