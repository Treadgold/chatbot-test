#!/usr/bin/env python3
"""
Health check script for RunPod Ollama endpoint
"""
import requests
import json
import sys
import time
from typing import Dict, Any

def check_endpoint_health(endpoint_id: str, api_key: str) -> Dict[str, Any]:
    """Check the health of a RunPod endpoint"""
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    # Test health check
    health_payload = {
        "input": {
            "type": "health"
        }
    }
    
    test_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
    
    try:
        print(f"🔍 Checking health of endpoint {endpoint_id}...")
        
        response = requests.post(
            test_url,
            json=health_payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            job_data = response.json()
            job_id = job_data.get("id")
            
            if job_id:
                print(f"✅ Health check job submitted: {job_id}")
                
                # Wait for job to complete
                print("⏳ Waiting for health check to complete...")
                time.sleep(10)
                
                # Check job status
                status_url = f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}"
                status_response = requests.get(status_url, headers=headers)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    status = status_data.get("status")
                    
                    if status == "COMPLETED":
                        result = status_data.get("output")
                        if result and result.get("ollama_ready"):
                            print("✅ Endpoint is healthy and Ollama is ready!")
                            return {"status": "healthy", "ollama_ready": True}
                        else:
                            print("⚠️  Endpoint is running but Ollama is not ready")
                            return {"status": "starting", "ollama_ready": False}
                    elif status == "IN_PROGRESS":
                        print("⏳ Health check is still in progress")
                        return {"status": "starting", "ollama_ready": False}
                    else:
                        print(f"❌ Health check failed with status: {status}")
                        return {"status": "failed", "ollama_ready": False}
                else:
                    print(f"❌ Failed to get job status: {status_response.status_code}")
                    return {"status": "error", "ollama_ready": False}
            else:
                print(f"❌ Health check failed: {job_data}")
                return {"status": "error", "ollama_ready": False}
        else:
            print(f"❌ Health check request failed: {response.status_code} - {response.text}")
            return {"status": "error", "ollama_ready": False}
            
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return {"status": "error", "ollama_ready": False}

def main():
    if len(sys.argv) != 3:
        print("Usage: python health_check.py <endpoint_id> <api_key>")
        print("Or set RUNPOD_API_KEY environment variable")
        sys.exit(1)
    
    endpoint_id = sys.argv[1]
    api_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not api_key:
        import os
        api_key = os.getenv("RUNPOD_API_KEY")
        if not api_key:
            print("❌ No API key provided")
            sys.exit(1)
    
    result = check_endpoint_health(endpoint_id, api_key)
    
    if result["status"] == "healthy":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main() 