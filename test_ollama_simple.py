from langchain_ollama import OllamaLLM

# Test basic Ollama connection
llm = OllamaLLM(model="dolphin-mistral-nemo:latest", base_url="http://localhost:11434")

try:
    # Simple test without structured output
    response = llm.invoke("Hello, what's your name?")
    print("SUCCESS!")
    print(f"Response: {response}")
except Exception as e:
    print(f"ERROR: {e}") 