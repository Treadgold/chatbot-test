#!/usr/bin/env python3
"""
Debug script to test the RunPod LLM with the same prompt causing the hang
"""

from runpod_llm import RunPodLLM
import os
from dotenv import load_dotenv
import time

load_dotenv()

def test_runpod_prompt():
    api_key = os.getenv('RUNPOD_API_KEY')
    if not api_key:
        print("RUNPOD_API_KEY not found!")
        return False
        
    llm = RunPodLLM(
        endpoint=os.getenv('RUNPOD_ENDPOINT', 'https://api.runpod.ai/v2/d4rdbc4d0vxrif'),
        api_key=api_key,
        model='CognitiveComputations/dolphin-mistral-nemo:latest',
        timeout=30.0  # Set a 30 second timeout for testing
    )

    prompt = """This is the start of the conversation.
Current message:
Think about: What's your day like?. Make a judgement on whether the user has views that align with you principles:You are a Scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear. Provide your thoughts in plain English, two short sentences."""

    print("Testing RunPod LLM with the exact prompt from _process_thought...")
    print(f"Prompt: {prompt}")
    print("---")
    
    start_time = time.time()
    try:
        response = llm.invoke(prompt)
        end_time = time.time()
        print(f"Response received in {end_time - start_time:.2f} seconds:")
        print(f"Response: {response}")
        return True
    except Exception as e:
        end_time = time.time()
        print(f"Error after {end_time - start_time:.2f} seconds: {e}")
        return False

if __name__ == "__main__":
    test_runpod_prompt() 