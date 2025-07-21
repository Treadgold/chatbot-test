#!/usr/bin/env python3
"""
Simple test to check RunPod endpoint availability
"""

import os
import requests
import time
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_endpoint(endpoint_url, api_key):
    """Test if a RunPod endpoint is responsive"""
    print(f"Testing endpoint: {endpoint_url}")
    
    # Test payload - simple health check
    payload = {
        "input": {
            "type": "health"
        }
    }
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        # Submit job
        print("🔥 Submitting job...")
        response = requests.post(f"{endpoint_url}/run", json=payload, headers=headers, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
            return False
            
        job_data = response.json()
        job_id = job_data.get("id")
        
        if not job_id:
            print(f"❌ No job ID returned: {job_data}")
            return False
            
        print(f"✅ Job submitted: {job_id}")
        
        # Poll for results
        print("⏳ Waiting for job completion...")
        max_wait = 60  # Wait up to 60 seconds
        wait_time = 0
        
        while wait_time < max_wait:
            status_response = requests.get(f"{endpoint_url}/status/{job_id}", headers=headers, timeout=10)
            
            if status_response.status_code != 200:
                print(f"❌ Failed to get status: {status_response.status_code}")
                return False
                
            status_data = status_response.json()
            status = status_data.get("status")
            
            if status == "COMPLETED":
                print("✅ Job completed successfully!")
                return True
            elif status in ["FAILED", "CANCELLED", "ERROR"]:
                print(f"❌ Job failed with status: {status}")
                print(f"Error details: {status_data}")
                return False
            else:
                print(f"⏳ Status: {status} (waiting {wait_time}s)")
                
            time.sleep(2)
            wait_time += 2
            
        print("❌ Job timed out")
        return False
        
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False

def main():
    api_key = os.getenv("RUNPOD_API_KEY")
    if not api_key:
        print("❌ RUNPOD_API_KEY not found in environment")
        return
        
    # Test endpoints from various sources
    endpoints_to_test = [
        os.getenv("RUNPOD_ENDPOINT"),  # From env if set
        "https://api.runpod.ai/v2/su4vbjbyk3h613",  # From web_chat.py
        "https://api.runpod.ai/v2/d4rdbc4d0vxrif",   # From test script
    ]
    
    for endpoint in endpoints_to_test:
        if endpoint:
            print(f"\n{'='*50}")
            if test_endpoint(endpoint, api_key):
                print(f"✅ Working endpoint found: {endpoint}")
                return
            else:
                print(f"❌ Endpoint not working: {endpoint}")
        else:
            print(f"\n{'='*50}")
            print("⚠️  Endpoint is None/empty")
    
    print("\n❌ No working endpoints found!")

if __name__ == "__main__":
    main() 