#!/usr/bin/env python3
"""
Simple RunPod Serverless Ollama Handler
"""
import runpod
import requests
import time
import sys
import json

def check_ollama():
    """Check if Ollama is responding"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        return response.status_code == 200
    except:
        return False

def get_available_models():
    """Get list of available models"""
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            data = response.json()
            models = data.get('models', [])
            return [model.get('name', '') for model in models]
        return []
    except Exception as e:
        print(f"Error getting models: {e}")
        return []

def handler(job):
    """Process incoming requests"""
    try:
        print("Job received")
        job_input = job.get('input', {})
        
        # Handle health check
        if job_input.get('type') == 'health':
            ollama_ready = check_ollama()
            available_models = get_available_models() if ollama_ready else []
            return {
                "status": "healthy" if ollama_ready else "starting",
                "ollama_ready": ollama_ready,
                "available_models": available_models
            }
        
        # Wait for Ollama to be ready
        print("Waiting for Ollama...")
        for i in range(60):  # Wait up to 60 seconds
            if check_ollama():
                break
            time.sleep(1)
        
        if not check_ollama():
            return {"error": "Ollama not ready after 60 seconds"}
        
        # Get available models for debugging
        available_models = get_available_models()
        print(f"Available models: {available_models}")
        
        # Process the request
        prompt = job_input.get('prompt', 'Hello!')
        model = job_input.get('model', 'dolphin-mistral-nemo:latest')
        
        print(f"Processing: {prompt}")
        print(f"Requested model: {model}")
        
        # Check if the requested model is available
        if model not in available_models:
            print(f"Model {model} not found in available models: {available_models}")
            
            # Try to find a similar model name
            model_base = model.split(':')[0] if ':' in model else model
            similar_models = [m for m in available_models if model_base in m]
            
            if similar_models:
                alternative_model = similar_models[0]
                print(f"Using alternative model: {alternative_model}")
                model = alternative_model
            else:
                print(f"No similar models found. Attempting to pull {model}...")
                try:
                    pull_response = requests.post(
                        "http://localhost:11434/api/pull",
                        json={"name": model},
                        timeout=300
                    )
                    if pull_response.status_code != 200:
                        return {
                            "error": f"Model {model} not available and pull failed: {pull_response.status_code}",
                            "available_models": available_models
                        }
                    print(f"Successfully pulled model: {model}")
                except Exception as e:
                    return {
                        "error": f"Model {model} not available and pull failed: {str(e)}",
                        "available_models": available_models
                    }
        
        payload = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "num_predict": 100
            }
        }
        
        print(f"Sending request to Ollama with model: {model}")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return {
                "response": result.get("response", ""),
                "model_used": model,
                "available_models": available_models
            }
        else:
            return {
                "error": f"Generation failed: {response.status_code}",
                "response_text": response.text,
                "model_used": model,
                "available_models": available_models
            }
            
    except Exception as e:
        print(f"Error: {e}")
        return {
            "error": f"Handler error: {str(e)}",
            "available_models": get_available_models()
        }

if __name__ == '__main__':
    print("Starting RunPod handler...")
    runpod.serverless.start({'handler': handler}) 