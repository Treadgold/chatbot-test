# RunPod Ollama Serverless Deployment Guide

## Step 1: Build and Push Docker Image

1. **Build the Docker image:**
   ```bash
   docker build -f Dockerfile.ollama -t your-username/runpod-ollama:latest .
   ```

2. **Push to Docker Hub:**
   ```bash
   docker push your-username/runpod-ollama:latest
   ```

## Step 2: Create RunPod Serverless Endpoint

1. Go to [RunPod Console](https://www.runpod.io/) → **Serverless**
2. Click **New Endpoint**
3. Fill in the configuration:

   **Basic Settings:**
   - **Endpoint Name**: `ollama-serverless`
   - **Docker Image**: `your-username/runpod-ollama:latest`
   - **Container Disk**: 20GB (minimum for most models)
   - **Environment Variables**: None needed

   **Advanced Settings:**
   - **GPU Types**: Select based on your model:
     - RTX 4090 (24GB): Good for 7B-13B models
     - A40 (48GB): Good for 30B+ models
     - A100 (80GB): Good for 70B+ models
   - **Max Workers**: 1-3 (depending on usage)
   - **Idle Timeout**: 5 seconds
   - **Max Execution Time**: 600 seconds (10 minutes)

4. Click **Create Endpoint**

## Step 3: Update Your Code

Once deployed, update your chatbot configuration:

```python
from chatbot_component import ChatBot, ChatBotConfig

# Use RunPod Ollama Serverless
cfg = ChatBotConfig(
    provider="runpod_ollama",
    runpod_endpoint="https://api.runpod.ai/v2/YOUR_ENDPOINT_ID",  # Replace with actual endpoint ID
    runpod_api_key="your_runpod_api_key",  # Replace with your API key
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest"  # Or any Ollama model
)

bot = ChatBot(cfg)
response = bot.get_simple_response("Hello!")
print(response)
```

## Step 4: Configure Environment Variables

Create or update your `.env` file with your RunPod details:

```bash
# RunPod Configuration
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR_ENDPOINT_ID
RUNPOD_API_KEY=your_runpod_api_key

# Flask Configuration
FLASK_SECRET_KEY=your-secret-key-here
FLASK_ENV=production
```

## Step 5: Start the Web Application

### Option 1: Using uvicorn (Recommended for Production)

```bash
# Install dependencies
pip install -r requirements.txt

# Start with uvicorn ASGI server
uvicorn asgi:application --host 0.0.0.0 --port 8000

# For development with auto-reload
uvicorn asgi:application --host 0.0.0.0 --port 8000 --reload
```

### Option 2: Using Flask Development Server

```bash
# Start with Flask built-in server (development only)
python web_chat.py
```

### Access Your Application

- **Local**: http://localhost:8000
- **Production**: http://your-server-ip:8000

## Step 6: Test the Complete Setup

### Test the Web Interface
1. Open your browser and go to http://localhost:8000
2. Type a message in the chat interface
3. Verify you get a response from your RunPod backend

### Test the RunPod Endpoint Directly

```python
import requests

url = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run"
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_runpod_api_key"
}
payload = {
    "input": {
        "model": "CognitiveComputations/dolphin-mistral-nemo:latest",
        "prompt": "What is a banana?",
        "stream": False
    }
}

response = requests.post(url, json=payload, headers=headers)
print(response.json())
```

## Benefits of This Approach

✅ **Same Interface**: Your existing code works unchanged  
✅ **Serverless**: Pay only when you use it  
✅ **Auto-scaling**: Handles multiple requests automatically  
✅ **Model Choice**: Use any Ollama model  
✅ **Reliable**: Ollama's proven inference engine  

## Model Download Notes

- The first request to a new model will take longer (3-10 minutes) as it downloads
- Subsequent requests with the same model are fast
- Consider pre-downloading models by uncommenting the line in `Dockerfile.ollama`

## Cost Optimization

- Use smaller GPU types for smaller models
- Set appropriate idle timeouts
- Consider pre-downloading models to reduce cold start time 