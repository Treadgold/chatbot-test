#!/usr/bin/env python3
"""
Simple RunPod Serverless Ollama Handler
"""
import runpod
import requests
import time
import sys

def check_ollama():
    """Check if Ollama is responding"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def handler(job):
    """Process incoming requests"""
    try:
        print("Job received")
        job_input = job.get('input', {})
        
        # Handle health check
        if job_input.get('type') == 'health':
            ollama_ready = check_ollama()
            return {
                "status": "healthy" if ollama_ready else "starting",
                "ollama_ready": ollama_ready
            }
        
        # Wait for Ollama to be ready
        print("Waiting for Ollama...")
        for i in range(30):  # Wait up to 30 seconds
            if check_ollama():
                break
            time.sleep(1)
        
        if not check_ollama():
            return {"error": "Ollama not ready"}
        
        # Process the request
        prompt = job_input.get('prompt', 'Hello!')
        model = job_input.get('model', 'dolphin-mistral-nemo:latest')
        
        print(f"Processing: {prompt}")
        
        # Check if model is available, if not pull it
        try:
            model_check = requests.get(f"http://localhost:11434/api/tags", timeout=5)
            if model_check.status_code == 200:
                models = model_check.json().get('models', [])
                model_names = [m.get('name') for m in models]
                if model not in model_names:
                    print(f"Model {model} not found, pulling...")
                    pull_response = requests.post(
                        "http://localhost:11434/api/pull",
                        json={"name": model},
                        timeout=300
                    )
                    if pull_response.status_code != 200:
                        return f"Error pulling model: {pull_response.status_code}"
        except Exception as e:
            print(f"Error checking/pulling model: {e}")
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result.get("response", "")
        else:
            return f"Error: {response.status_code}"
            
    except Exception as e:
        print(f"Error: {e}")
        return f"Handler error: {str(e)}"

if __name__ == '__main__':
    print("Starting RunPod handler...")
    runpod.serverless.start({'handler': handler}) 