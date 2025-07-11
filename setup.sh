#!/bin/bash

# Download and install Ollama
echo "Installing Ollama..."
curl -fsSL https://ollama.ai/install.sh | sh

# Wait for Ollama to be available
echo "Waiting for Ollama to be ready..."
sleep 5

# Start Ollama service if not running
echo "Starting Ollama service..."
ollama serve &
sleep 3

# Pull the model
echo "Pulling CognitiveComputations/dolphin-mistral-nemo:latest..."
ollama pull CognitiveComputations/dolphin-mistral-nemo:latest

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment and install requirements
echo "Activating virtual environment and installing requirements..."
source .venv/bin/activate
pip3 install -r requirements.txt

echo "Setup complete!" 