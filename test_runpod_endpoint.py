#!/usr/bin/env python3
"""
Test script for the updated RunPod serverless endpoint integration.
"""

import os
from dotenv import load_dotenv
from runpod_llm import RunPodLLM
from chatbot_component import ChatBot, ChatBotConfig

# Load environment variables
load_dotenv()

def test_runpod_llm_direct():
    """Test the RunPodLLM class directly"""
    print("=== Testing RunPodLLM directly ===")
    
    llm = RunPodLLM(
        endpoint=os.getenv('RUNPOD_ENDPOINT', "https://api.runpod.ai/v2/d4rdbc4d0vxrif"),
        api_key=os.getenv('RUNPOD_API_KEY'),
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
        return False

def test_chatbot_component():
    """Test the ChatBot component with RunPod"""
    print("\n=== Testing ChatBot component ===")
    
    config = ChatBotConfig(
        provider="runpod",
        model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
        runpod_endpoint=os.getenv('RUNPOD_ENDPOINT', "https://api.runpod.ai/v2/d4rdbc4d0vxrif"),
        runpod_api_key=os.getenv('RUNPOD_API_KEY'),
        principles="""You are a Scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
    )
    
    chatbot = ChatBot(config)
    
    test_message = "Hello there! How are you today?"
    print(f"Message: {test_message}")
    
    try:
        # Test simple response
        simple_response = chatbot.get_simple_response(test_message)
        print(f"Simple Response: {simple_response}")
        
        # Test full chat response
        full_response = chatbot.chat(test_message)
        print(f"Full Response: {full_response}")
        
        print("✅ ChatBot component test successful!")
        return True
    except Exception as e:
        print(f"❌ ChatBot component test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Testing updated RunPod serverless endpoint integration...\n")
    
    # Check environment variables
    endpoint = os.getenv('RUNPOD_ENDPOINT')
    api_key = os.getenv('RUNPOD_API_KEY')
    
    if not endpoint or not api_key:
        print("❌ Missing environment variables:")
        print(f"  RUNPOD_ENDPOINT: {'✅' if endpoint else '❌'}")
        print(f"  RUNPOD_API_KEY: {'✅' if api_key else '❌'}")
        return
    
    print(f"Using endpoint: {endpoint}")
    print(f"API key configured: {'✅' if api_key else '❌'}\n")
    
    # Run tests
    direct_test_passed = test_runpod_llm_direct()
    component_test_passed = test_chatbot_component()
    
    print(f"\n=== Test Results ===")
    print(f"Direct RunPodLLM test: {'✅ PASSED' if direct_test_passed else '❌ FAILED'}")
    print(f"ChatBot component test: {'✅ PASSED' if component_test_passed else '❌ FAILED'}")
    
    if direct_test_passed and component_test_passed:
        print("\n🎉 All tests passed! Your RunPod endpoint is working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the error messages above.")

if __name__ == "__main__":
    main() 