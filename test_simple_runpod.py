#!/usr/bin/env python3
"""
Simple test script for the RunPod LLM class only.
"""

import os
from dotenv import load_dotenv
from runpod_llm import RunPodLLM

# Load environment variables
load_dotenv()

def test_runpod_llm_direct():
    """Test the RunPodLLM class directly"""
    print("=== Testing RunPodLLM directly ===")
    
    endpoint = os.getenv('RUNPOD_ENDPOINT', "https://api.runpod.ai/v2/d4rdbc4d0vxrif")
    api_key = os.getenv('RUNPOD_API_KEY')
    
    if not api_key:
        print("❌ RUNPOD_API_KEY not found in environment variables")
        return False
    
    print(f"Using endpoint: {endpoint}")
    print(f"API key configured: ✅")
    
    llm = RunPodLLM(
        endpoint=endpoint,
        api_key=api_key,
        model="CognitiveComputations/dolphin-mistral-nemo:latest"
    )
    
    test_prompt = "Hello! You're a Scottish madman trapped in a computer. Tell me a short joke."
    print(f"Prompt: {test_prompt}")
    
    try:
        response = llm.invoke(test_prompt)
        print(f"Response: {response}")
        print("✅ Direct RunPodLLM test successful!")
        return True
    except Exception as e:
        print(f"❌ Direct RunPodLLM test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run the test"""
    print("Testing RunPod LLM integration...\n")
    
    success = test_runpod_llm_direct()
    
    print(f"\n=== Test Results ===")
    if success:
        print("🎉 RunPod LLM test passed! Your endpoint is working correctly.")
    else:
        print("⚠️  Test failed. Check the error messages above.")

if __name__ == "__main__":
    main() 