# Chatbot with RunPod Ollama Serverless

A LangGraph-based chatbot that can run locally with Ollama or on RunPod serverless infrastructure.

## Features

- **Local Ollama Support**: Run with local Ollama installation
- **RunPod Serverless**: Deploy Ollama in Docker containers on RunPod for serverless inference
- **LangGraph Integration**: Complex conversation flows with thoughts, principles, and personality
- **Web Interface**: Flask-based chat interface
- **Stripe Integration**: Payment processing capabilities

## Quick Start (Local)

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start Ollama locally:
   ```bash
   ollama serve
   ollama pull dolphin-mistral-nemo:latest
   ```

3. Run the web interface:
   ```bash
   python web_chat.py
   ```

4. Open http://localhost:5000

## Complete Deployment Guide

### Step 1: Build and Push Docker Image for RunPod Backend

```bash
# Build the Ollama serverless image
docker build -f Dockerfile.ollama -t yourusername/runpod-ollama:latest .

# Push to Docker Hub
docker push yourusername/runpod-ollama:latest
```

### Step 2: Create RunPod Serverless Endpoint

1. Go to [RunPod Console](https://www.runpod.io/) → **Serverless**
2. Click **New Endpoint**
3. Configure the endpoint:
   - **Docker Image**: `yourusername/runpod-ollama:latest`
   - **Container Disk**: 20GB (minimum for most models)
   - **GPU Type**: Select based on your model (RTX 4090 recommended for 7B-13B models)
   - **Max Execution Time**: 600 seconds (10 minutes)
   - **Idle Timeout**: 5 seconds
   - **Workers Min**: 0, **Workers Max**: 1-3
4. Click **Create Endpoint**
5. **Copy the Endpoint ID** from the URL (e.g., `vsgzvmdz6x1bei`)

### Step 3: Configure Environment Variables

Create or update your `.env` file:

```bash
# RunPod Configuration
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_runpod_api_key

# Flask Configuration  
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

### Step 4: Install Dependencies and Start Web Application

```bash
# Install Python dependencies
pip install -r requirements.txt

# Start the web application with uvicorn (recommended for production)
uvicorn asgi:application --host 0.0.0.0 --port 8000

# Alternative: Start with Flask development server
python web_chat.py
```

### Step 5: Access Your Chat Application

Open your browser and navigate to:
- **Local**: http://localhost:8000
- **Production**: http://your-server-ip:8000

## Configuration Options

### RunPod Backend Configuration

Update `web_chat.py` if needed:

```python
cfg = ChatBotConfig(
    provider="runpod",  # Using RunPod serverless endpoint
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    runpod_endpoint=os.getenv('RUNPOD_ENDPOINT', 
                            "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID"),
    runpod_api_key=os.getenv('RUNPOD_API_KEY'),
    max_iterations=3,
    timeout=0  # No timeout - wait indefinitely
)
```

## Files

- `chatbot_component.py` - Main chatbot logic with LangGraph
- `web_chat.py` - Flask web interface
- `Dockerfile.ollama` - Docker image for RunPod serverless
- `ollama_handler.py` - RunPod serverless handler
- `runpod_ollama_llm.py` - Client wrapper for RunPod Ollama
- `build_and_deploy.md` - Detailed deployment instructions

## Configuration

The chatbot supports three providers:

1. **"ollama"** - Local Ollama installation
2. **"runpod"** - RunPod vLLM endpoints (basic)
3. **"runpod_ollama"** - RunPod Ollama serverless (recommended)

## Benefits of RunPod Ollama

- ✅ **Identical behavior** to local Ollama
- ✅ **Serverless scaling** - pay only when used
- ✅ **Any Ollama model** - supports full model library
- ✅ **Reliable inference** - proven Ollama engine
- ✅ **Auto-scaling** - handles multiple requests

## License

MIT License 