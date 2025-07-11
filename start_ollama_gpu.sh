#!/bin/bash

# Force Ollama to use GPU only
export OLLAMA_NUM_CPU=0
export OLLAMA_N_GPU_LAYERS=9999
export OLLAMA_CTX_SIZE=8192

# Optional: Set additional GPU-related variables
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_FLASH_ATTENTION=true

echo "Starting Ollama server with GPU-only configuration..."
echo "OLLAMA_NUM_CPU: $OLLAMA_NUM_CPU"
echo "OLLAMA_N_GPU_LAYERS: $OLLAMA_N_GPU_LAYERS"
echo "OLLAMA_CTX_SIZE: $OLLAMA_CTX_SIZE"

# Start Ollama server
ollama serve 