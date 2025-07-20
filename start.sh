#!/bin/bash
echo "Starting Ollama for initial setup..."
ollama serve &
OLLAMA_PID=$!

# Give Ollama time to create its directory structure
echo "Waiting for initial Ollama setup..."
sleep 10

# Stop the initial Ollama process
echo "Stopping Ollama to restart with models..."
kill $OLLAMA_PID
wait $OLLAMA_PID 2>/dev/null || true

# Now restart Ollama - this should trigger a proper model scan
echo "Restarting Ollama to scan models..."
ollama serve &
OLLAMA_PID=$!

# Give it more time to scan the models
echo "Waiting for Ollama to scan models..."
sleep 30

# Wait for Ollama API to be ready
echo "Checking Ollama API..."
for i in {1..30}; do
    if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo "Ollama API is ready"
        break
    fi
    echo "Waiting for Ollama API... ($i/30)"
    sleep 15
done

# Check models using Ollama's native list command
echo "Checking models with 'ollama list':"
ollama list 2>/dev/null || echo "  ⚠️ Could not run ollama list"

# List available models via API for verification
echo "Available models via API:"
curl -s http://localhost:11434/api/tags | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    models = data.get('models', [])
    if models:
        for model in models:
            print(f'  ✅ {model.get(\"name\", \"Unknown\")}')
        print(f'Total models found: {len(models)}')
    else:
        print('  ❌ No models found')
except Exception as e:
    print(f'  ⚠️ Could not parse model list: {e}')
" 2>/dev/null || echo "  ⚠️ Could not check models"

echo "Starting Python handler..."
echo "Ollama is ready for testing on port 11434"

# Start the RunPod handler
python3 -u ollama_handler.py
