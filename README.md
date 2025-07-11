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

## RunPod Serverless Deployment

### 1. Build and Push Docker Image

```bash
# Build the Ollama serverless image
docker build -f Dockerfile.ollama -t yourusername/runpod-ollama:latest .

# Push to Docker Hub
docker push yourusername/runpod-ollama:latest
```

### 2. Create RunPod Endpoint

1. Go to [RunPod Console](https://www.runpod.io/) → **Serverless**
2. Click **New Endpoint**
3. Use your Docker image: `yourusername/runpod-ollama:latest`
4. Configure GPU settings based on your model size
5. Set timeout to 600 seconds (10 minutes)

### 3. Update Configuration

```python
from chatbot_component import ChatBot, ChatBotConfig

cfg = ChatBotConfig(
    provider="runpod_ollama",
    runpod_endpoint="https://api.runpod.ai/v2/YOUR_ENDPOINT_ID",
    runpod_api_key="your_runpod_api_key",
    model_name="dolphin-mistral-nemo:latest"
)

bot = ChatBot(cfg)
response = bot.get_simple_response("Hello!")
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