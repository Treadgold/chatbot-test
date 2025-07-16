#!/usr/bin/env python3
"""
RunPod Serverless Ollama Handler
Follows the official RunPod pattern for serverless workers
"""
import runpod
import requests
import json
import os
import sys
import time
import subprocess
from typing import Dict, Any, Optional

def ensure_model_available(model_name: str) -> bool:
    """Ensure the specified model is available, download if needed"""
    try:
        # Check if model exists
        response = requests.get("http://localhost:11434/api/tags", timeout=10)
        if response.status_code == 200:
            models = response.json().get("models", [])
            for model in models:
                if model.get("name", "").startswith(model_name):
                    print(f"✅ Model {model_name} is already available")
                    return True
        
        # Download model if not found
        print(f"📥 Downloading model {model_name}...")
        pull_response = requests.post(
            "http://localhost:11434/api/pull",
            json={"name": model_name},
            timeout=600  # 10 minutes timeout for model download
        )
        
        if pull_response.status_code == 200:
            print(f"✅ Model {model_name} downloaded successfully")
            return True
        else:
            print(f"❌ Failed to download model {model_name}: {pull_response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error ensuring model availability: {e}")
        return False

def handler(job):
    """
    RunPod serverless handler function
    This is called for each request to the endpoint
    """
    try:
        print("🚀 Handler started")
        
        # Get input from job
        job_input = job.get("input", {})
        prompt = job_input.get("prompt", "Hello!")
        model = job_input.get("model", "dolphin-mistral-nemo:latest")
        options = job_input.get("options", {})
        
        print(f"📝 Processing prompt: {prompt[:100]}...")
        print(f"🤖 Using model: {model}")
        
        # Ensure model is available
        if not ensure_model_available(model):
            return {"error": f"Failed to ensure model {model} is available"}
        
        # Prepare request payload
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": options.get("temperature", 0.7),
                "num_predict": options.get("num_predict", 500),
                **options
            }
        }
        
        print("🔄 Sending request to Ollama...")
        
        # Make request to Ollama
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=300  # 5 minutes timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            
            print(f"✅ Generated {len(generated_text)} characters")
            
            return {
                "output": generated_text,
                "model": model,
                "prompt": prompt,
                "done": result.get("done", True),
                "total_duration": result.get("total_duration"),
                "load_duration": result.get("load_duration"),
                "prompt_eval_count": result.get("prompt_eval_count"),
                "eval_count": result.get("eval_count")
            }
        else:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            print(f"❌ {error_msg}")
            return {"error": error_msg}
            
    except Exception as e:
        error_msg = f"Handler error: {str(e)}"
        print(f"❌ {error_msg}")
        return {"error": error_msg}

def check_ollama_health():
    """Check if Ollama is running and healthy"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def wait_for_ollama(max_wait=60):
    """Wait for Ollama to be ready"""
    print("⏳ Waiting for Ollama to be ready...")
    
    for i in range(max_wait):
        if check_ollama_health():
            print(f"✅ Ollama is ready after {i + 1} seconds!")
            return True
        
        if i % 10 == 0 and i > 0:
            print(f"Still waiting for Ollama... ({i}/{max_wait} seconds)")
        
        time.sleep(1)
    
    print(f"❌ Ollama not ready after {max_wait} seconds")
    return False

def start_ollama():
    """Start Ollama server if not already running"""
    if check_ollama_health():
        print("✅ Ollama is already running")
        return True
    
    print("🔄 Starting Ollama server...")
    try:
        # Start Ollama in background
        process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for it to be ready
        if wait_for_ollama():
            print("✅ Ollama server started successfully")
            return True
        else:
            print("❌ Failed to start Ollama server")
            return False
            
    except Exception as e:
        print(f"❌ Error starting Ollama: {e}")
        return False

if __name__ == "__main__":
    print("🚀 RunPod Ollama Worker Starting...")
    
    # Start Ollama server
    if not start_ollama():
        print("❌ Failed to start Ollama, exiting...")
        sys.exit(1)
    
    # Pre-download the default model
    default_model = os.getenv("DEFAULT_MODEL", "dolphin-mistral-nemo:latest")
    print(f"📥 Pre-downloading default model: {default_model}")
    ensure_model_available(default_model)
    
    print("✅ Worker initialization complete, starting RunPod handler...")
    
    # Start the RunPod serverless worker
    runpod.serverless.start({"handler": handler}) 