#!/usr/bin/env python3
"""
Test script for RunPod serverless endpoint
"""
import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional


def test_endpoint(endpoint_id: str, api_key: str, test_prompts: list = None) -> bool:
    """Test the RunPod endpoint with various prompts"""
    
    if test_prompts is None:
        test_prompts = [
            "Hello! How are you?",
            "Tell me a short joke.",
            "What is 2+2?",
            "Write a haiku about computers."
        ]
    
    base_url = f"https://api.runpod.ai/v2/{endpoint_id}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    
    print(f"🧪 Testing RunPod endpoint: {endpoint_id}")
    print("=" * 50)
    
    success_count = 0
    total_tests = len(test_prompts)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\nTest {i}/{total_tests}: {prompt}")
        print("-" * 30)
        
        # Submit job
        payload = {
            "input": {
                "prompt": prompt,
                "model": "dolphin-mistral-nemo:latest",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 100
                }
            }
        }
        
        try:
            # Submit the job
            response = requests.post(
                f"{base_url}/run",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
                continue
            
            job_data = response.json()
            job_id = job_data.get("id")
            
            if not job_id:
                print(f"❌ No job ID returned: {job_data}")
                continue
            
            print(f"⏳ Job submitted: {job_id}")
            
            # Poll for results
            start_time = time.time()
            timeout = 300  # 5 minutes
            
            while time.time() - start_time < timeout:
                status_response = requests.get(
                    f"{base_url}/status/{job_id}",
                    headers=headers,
                    timeout=30
                )
                
                if status_response.status_code != 200:
                    print(f"❌ Failed to get status: {status_response.status_code}")
                    break
                
                status_data = status_response.json()
                status = status_data.get("status")
                
                if status == "COMPLETED":
                    output = status_data.get("output", {})
                    
                    if isinstance(output, dict):
                        response_text = output.get("response", str(output))
                    else:
                        response_text = str(output)
                    
                    print(f"✅ Response: {response_text}")
                    success_count += 1
                    break
                    
                elif status in ["FAILED", "CANCELLED", "ERROR"]:
                    print(f"❌ Job failed: {status_data}")
                    break
                    
                elif status in ["IN_QUEUE", "IN_PROGRESS", "STARTED"]:
                    print(f"⏳ Status: {status}")
                    time.sleep(5)
                    
                else:
                    print(f"⚠️  Unknown status: {status}")
                    time.sleep(5)
            
            else:
                print(f"❌ Test timed out after {timeout} seconds")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
    
    print(f"\n📊 Test Results: {success_count}/{total_tests} tests passed")
    
    if success_count == total_tests:
        print("🎉 All tests passed! Your endpoint is working correctly.")
        return True
    elif success_count > 0:
        print("⚠️  Some tests failed. Check the logs above.")
        return False
    else:
        print("❌ All tests failed. Check your endpoint configuration.")
        return False


def main():
    print("🚀 RunPod Endpoint Tester")
    print("=" * 40)
    
    # Get parameters
    endpoint_id = os.getenv("RUNPOD_ENDPOINT_ID")
    api_key = os.getenv("RUNPOD_API_KEY")
    
    if not endpoint_id:
        endpoint_id = input("Enter your RunPod endpoint ID: ").strip()
    
    if not api_key:
        api_key = input("Enter your RunPod API key: ").strip()
    
    if not endpoint_id or not api_key:
        print("❌ Both endpoint ID and API key are required")
        sys.exit(1)
    
    # Run tests
    success = test_endpoint(endpoint_id, api_key)
    
    if success:
        print("\n🎯 Next Steps:")
        print("1. Your endpoint is ready for production use")
        print("2. Update your application to use this endpoint")
        print("3. Monitor costs and usage in RunPod console")
        sys.exit(0)
    else:
        print("\n🔧 Troubleshooting:")
        print("1. Check RunPod console for error logs")
        print("2. Verify your endpoint is running")
        print("3. Ensure you have sufficient credits")
        print("4. Wait a few minutes for cold start if first run")
        sys.exit(1)


if __name__ == "__main__":
    main() 