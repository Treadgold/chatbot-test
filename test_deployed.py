#!/usr/bin/env python3
"""
Test script for the deployed RunPod Ollama endpoint
"""
import requests
import json
import time
import os

def test_deployed_endpoint():
    # Configuration - Update these with your actual values
    ENDPOINT_ID = os.getenv("RUNPOD_ENDPOINT_ID", "YOUR_ENDPOINT_ID")
    API_KEY = os.getenv("RUNPOD_API_KEY", "YOUR_API_KEY")
    
    if ENDPOINT_ID == "YOUR_ENDPOINT_ID" or API_KEY == "YOUR_API_KEY":
        print("❌ Please set RUNPOD_ENDPOINT_ID and RUNPOD_API_KEY environment variables")
        print("   Or update the values in this script")
        return
    
    url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/run"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }
    
    # Load test input
    with open('test_input.json', 'r') as f:
        test_data = json.load(f)
    
    print("Testing deployed RunPod endpoint...")
    print(f"Endpoint: {url}")
    print(f"Input: {json.dumps(test_data, indent=2)}")
    print("\n" + "="*50 + "\n")
    
    try:
        # Make the request
        response = requests.post(url, json=test_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            
            # Check if it's a sync or async response
            if "id" in result:
                # Async - need to poll for results
                job_id = result["id"]
                print(f"Job submitted with ID: {job_id}")
                print("Polling for results...")
                
                # Poll for results
                status_url = f"https://api.runpod.ai/v2/{ENDPOINT_ID}/status/{job_id}"
                
                while True:
                    status_response = requests.get(status_url, headers=headers)
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        status = status_data.get("status", "UNKNOWN")
                        
                        print(f"Status: {status}")
                        
                        if status == "COMPLETED":
                            output = status_data.get("output", {})
                            print("\n✅ Success!")
                            print(f"Response: {output.get('response', '')[:200]}...")
                            break
                        elif status == "FAILED":
                            print(f"❌ Job failed: {status_data.get('error', 'Unknown error')}")
                            break
                        else:
                            time.sleep(2)
                    else:
                        print(f"❌ Error checking status: {status_response.text}")
                        break
            else:
                # Sync response
                print("✅ Success!")
                print(f"Response: {result.get('response', '')[:200]}...")
                
        else:
            print(f"❌ HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception: {e}")

if __name__ == "__main__":
    test_deployed_endpoint() 