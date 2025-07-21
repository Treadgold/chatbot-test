#!/bin/bash

# Optimized configuration for 24GB VRAM
export OLLAMA_NUM_CPU=0
export OLLAMA_N_GPU_LAYERS=9999
export OLLAMA_CTX_SIZE=8192  # Optimal for 24GB VRAM with 12B model

# Memory optimization settings
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_FLASH_ATTENTION=true
export OLLAMA_LOW_VRAM=true
export OLLAMA_DISABLE_SPINNER=true

# Additional optimizations
export OLLAMA_KV_CACHE_TYPE=q8_0  # Quantize KV cache
export OLLAMA_MAX_BATCH_SIZE=128  # Smaller batch size

echo "Starting Ollama server with optimized 24GB VRAM configuration..."
echo "OLLAMA_NUM_CPU: $OLLAMA_NUM_CPU"
echo "OLLAMA_N_GPU_LAYERS: $OLLAMA_N_GPU_LAYERS" 
echo "OLLAMA_CTX_SIZE: $OLLAMA_CTX_SIZE"
echo "OLLAMA_LOW_VRAM: $OLLAMA_LOW_VRAM"
echo "OLLAMA_KV_CACHE_TYPE: $OLLAMA_KV_CACHE_TYPE"

# Start Ollama server
ollama serve 