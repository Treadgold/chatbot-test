#!/bin/bash

# Start Ollama server in the background
echo "Starting Ollama server..."
ollama serve &
OLLAMA_PID=$!

# Wait for Ollama to be ready
echo "Waiting for Ollama to be ready..."
until ollama list >/dev/null 2>&1; do
    echo "Waiting for Ollama service to start..."
    sleep 2
done

# Additional wait to ensure API is fully ready
echo "Ollama service detected, waiting for API to be fully ready..."
sleep 5

# Test the generate endpoint specifically
echo "Testing Ollama API endpoint..."
until curl -s http://localhost:11434/api/generate -X POST -H "Content-Type: application/json" -d '{"model":"CognitiveComputations/dolphin-mistral-nemo:latest","prompt":"test"}' >/dev/null 2>&1; do
    echo "Waiting for Ollama API to be ready..."
    sleep 2
done

echo "Ollama is ready, starting Python handler..."

# Start the Python handler
exec python3 -u ollama_handler.py 