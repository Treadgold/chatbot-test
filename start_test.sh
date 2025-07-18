#!/bin/bash
echo "Starting Ollama..."
ollama serve &
sleep 10
echo "Starting Python handler for testing..."
python3 -u ollama_handler.py 