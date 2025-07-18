#!/bin/bash

# Exit on any error
set -e

echo "=== Starting Ollama Pod Container ==="
echo "Timestamp: $(date)"
echo "Container ID: $(hostname)"

# Set GPU-specific environment variables for optimal performance
export OLLAMA_NUM_CPU=0
export OLLAMA_N_GPU_LAYERS=9999
export OLLAMA_CTX_SIZE=8192
export OLLAMA_GPU_OVERHEAD=0
export OLLAMA_FLASH_ATTENTION=true

# Activate Python virtual environment
echo "=== Activating Python Virtual Environment ==="
source /opt/venv/bin/activate

# Log basic environment info
echo "=== Environment Info ==="
echo "Python version: $(python3 --version)"
echo "Working directory: $(pwd)"
echo "Files in /app:"
ls -la /app/ || echo "No /app directory"

# Check if handler file exists
if [ ! -f "/app/ollama_handler.py" ]; then
    echo "❌ Handler file not found at /app/ollama_handler.py"
    echo "Available files:"
    find /app -type f 2>/dev/null || echo "No files found in /app"
    exit 1
fi

# Start Ollama server in the background
echo "=== Starting Ollama Server ==="
ollama serve &
OLLAMA_PID=$!
echo "Ollama PID: $OLLAMA_PID"

# Wait for Ollama to be ready (simplified)
echo "=== Waiting for Ollama to be Ready ==="
for i in {1..30}; do
    if ollama list >/dev/null 2>&1; then
        echo "✅ Ollama service is ready"
        break
    fi
    echo "⏳ Waiting for Ollama... (attempt $i/30)"
    sleep 2
done

# Check if Ollama started successfully
if ! ollama list >/dev/null 2>&1; then
    echo "❌ Ollama failed to start"
    exit 1
fi

# Simple API test
echo "=== Testing Ollama API ==="
for i in {1..10}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "✅ Ollama API is ready"
        break
    fi
    echo "⏳ Waiting for API... (attempt $i/10)"
    sleep 2
done

echo "✅ Starting Python handler..."

# Start the Python handler
exec python3 -u /app/ollama_handler.py 