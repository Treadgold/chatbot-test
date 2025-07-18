#!/bin/bash
echo "Starting Ollama..."
ollama serve &
sleep 10

echo "Loading dolphin-mistral-nemo model..."
# Explicitly load the model to ensure it's recognized
ollama run dolphin-mistral-nemo:latest < /dev/null || echo "Model loading failed, but continuing..."

echo "Starting Python handler..."
# For local testing, keep the container running
# python3 -u ollama_handler.py
echo "Ollama is ready for testing on port 11434"
echo "Container will stay running for local testing"
tail -f /dev/null 