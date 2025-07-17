#!/usr/bin/env python3
"""
RunPod Serverless Ollama Handler
Follows the official RunPod pattern for serverless workers
"""
import runpod
import requests
import os

def handler(job):
    """
    Processes incoming requests to your Serverless endpoint.
    Args:
        job (dict): Contains the input data and request metadata
    Returns:
        The generated text from Ollama
    """
    print(f"Worker Start")
    job_input = job.get('input', {})
    prompt = job_input.get('prompt', 'Hello!')
    model = job_input.get('model', 'CognitiveComputations/dolphin-mistral-nemo:latest')
    options = job_input.get('options', {})
    print(f"Received prompt: {prompt}")
    print(f"Using model: {model}")
    try:
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
        print("Sending request to Ollama...")
        response = requests.post(
            "http://localhost:11434/api/generate",
            json=payload,
            timeout=300
        )
        if response.status_code == 200:
            result = response.json()
            generated_text = result.get("response", "")
            print(f"Generated {len(generated_text)} characters")
            return generated_text
        else:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            print(error_msg)
            return error_msg
    except Exception as e:
        error_msg = f"Handler error: {str(e)}"
        print(error_msg)
        return error_msg

if __name__ == '__main__':
    print("🚀 RunPod Ollama Worker Starting...")
    runpod.serverless.start({'handler': handler}) 