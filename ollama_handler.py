import runpod
import subprocess
import time
import requests
import json
import threading
import os
from typing import Dict, Any

# Global variable to track if Ollama is running
ollama_process = None
ollama_ready = False

def start_ollama():
    """Start the Ollama server in the background"""
    global ollama_process, ollama_ready
    
    try:
        # Start Ollama server
        ollama_process = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for Ollama to be ready
        max_attempts = 30
        for attempt in range(max_attempts):
            try:
                response = requests.get("http://localhost:11434/api/tags", timeout=2)
                if response.status_code == 200:
                    ollama_ready = True
                    print("Ollama server is ready!")
                    return True
            except:
                time.sleep(2)
        
        print("Failed to start Ollama server")
        return False
        
    except Exception as e:
        print(f"Error starting Ollama: {e}")
        return False

def ensure_model_downloaded(model_name: str):
    """Ensure the specified model is downloaded"""
    try:
        # Check if model exists
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model["name"] for model in models]
            
            if model_name not in model_names:
                print(f"Downloading model: {model_name}")
                subprocess.run(["ollama", "pull", model_name], check=True)
                print(f"Model {model_name} downloaded successfully")
            else:
                print(f"Model {model_name} already available")
                
    except Exception as e:
        print(f"Error ensuring model download: {e}")

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod serverless handler that mimics the Ollama API
    
    Expected input format:
    {
        "model": "dolphin-mistral-nemo:latest",
        "prompt": "Your prompt here",
        "stream": false,
        "options": {
            "temperature": 0.7,
            "num_predict": 100
        }
    }
    """
    global ollama_ready
    
    try:
        # Start Ollama if not already running
        if not ollama_ready:
            print("Starting Ollama server...")
            if not start_ollama():
                return {"error": "Failed to start Ollama server"}
        
        # Get input parameters
        input_data = event.get("input", {})
        model = input_data.get("model", "dolphin-mistral-nemo:latest")
        prompt = input_data.get("prompt", "")
        stream = input_data.get("stream", False)
        options = input_data.get("options", {})
        
        if not prompt:
            return {"error": "No prompt provided"}
        
        # Ensure model is downloaded
        ensure_model_downloaded(model)
        
        # Prepare the request to local Ollama
        ollama_request = {
            "model": model,
            "prompt": prompt,
            "stream": stream,
            "options": options
        }
        
        # Make request to local Ollama server
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=ollama_request,
            timeout=120  # 2 minute timeout for generation
        )
        
        if response.status_code == 200:
            if stream:
                # Handle streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        chunk = json.loads(line)
                        if "response" in chunk:
                            full_response += chunk["response"]
                        if chunk.get("done", False):
                            break
                
                return {
                    "response": full_response,
                    "model": model,
                    "done": True
                }
            else:
                # Handle non-streaming response
                result = response.json()
                return {
                    "response": result.get("response", ""),
                    "model": model,
                    "done": result.get("done", True),
                    "context": result.get("context", []),
                    "total_duration": result.get("total_duration", 0),
                    "load_duration": result.get("load_duration", 0),
                    "prompt_eval_duration": result.get("prompt_eval_duration", 0),
                    "eval_duration": result.get("eval_duration", 0),
                    "eval_count": result.get("eval_count", 0)
                }
        else:
            return {"error": f"Ollama server error: {response.status_code} - {response.text}"}
            
    except Exception as e:
        return {"error": f"Handler error: {str(e)}"}

# Initialize Ollama when the container starts
print("Initializing Ollama serverless worker...")
start_ollama()

# Start the RunPod serverless worker
runpod.serverless.start({"handler": handler}) 