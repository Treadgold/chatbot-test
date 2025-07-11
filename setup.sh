#!/bin/bash

# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull the model
ollama pull CognitiveComputations/dolphin-mistral-nemo:latest

# Create virtual environment
python3 -m venv .venv

# Activate virtual environment and install requirements
source .venv/bin/activate
pip3 install -r requirements.txt 