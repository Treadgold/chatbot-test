# How to Use Your RunPod Ollama Endpoint

This guide explains how to configure and use your deployed RunPod Ollama endpoint with your Flask web chat application.

## 🚀 Getting Your Endpoint URL

### From RunPod Dashboard:
1. Go to your RunPod **Serverless** dashboard
2. Find your deployed endpoint
3. Copy the **Endpoint URL** (it will look like: `https://api.runpod.ai/v2/{endpoint-id}`)

### From Worker Logs:
1. Go to your endpoint's **Workers** tab
2. Look for the **Connect** section
3. Copy the HTTP endpoint URL (format: `https://{worker-id}-11434.proxy.runpod.net/`)

## 📝 Configuration Options

You have **3 ways** to configure your `web_chat.py` to use the RunPod endpoint:

### Option 1: Direct Ollama API (Recommended)
```python
config = ChatBotConfig(
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    base_url="https://YOUR-WORKER-ID-11434.proxy.runpod.net/",
    max_iterations=3,
    min_joke_score=800,
    principles="""Your chatbot personality here"""
)
```

### Option 2: RunPod Serverless API
```python
cfg = ChatBotConfig(
    provider="runpod",
    runpod_endpoint="https://api.runpod.ai/v2/d4rdbc4d0vxrif",
    runpod_api_key="YOUR-RUNPOD-API-KEY",
    principles="""Your chatbot personality here"""
)
```

### Option 3: Local Development (Fallback)
```python
config = ChatBotConfig(
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    base_url="http://localhost:11434",
    max_iterations=3,
    min_joke_score=800,
    principles="""Your chatbot personality here"""
)
```

## 🔧 Step-by-Step Setup

### 1. Get Your Endpoint Details

From your RunPod dashboard, you'll need:
- **Worker Proxy URL**: `https://{worker-id}-11434.proxy.runpod.net/`
- **OR Serverless Endpoint**: `https://api.runpod.ai/v2/{endpoint-id}`
- **RunPod API Key**: (if using serverless API)

### 2. Update web_chat.py

Edit lines 25-31 in `web_chat.py`:

```python
# Replace the existing config with your RunPod endpoint
config = ChatBotConfig(
    model_name="CognitiveComputations/dolphin-mistral-nemo:latest",
    base_url="https://YOUR-ACTUAL-WORKER-ID-11434.proxy.runpod.net/",  # 👈 PUT YOUR URL HERE
    max_iterations=3,
    min_joke_score=800,
    principles="""You are a scottish madman who is trapped in a computer, you are short tempered and have a tendency to swear"""
)
```

### 3. Set Environment Variables (for Serverless API)

If using Option 2, create/update your `.env` file:
```bash
RUNPOD_ENDPOINT=https://api.runpod.ai/v2/YOUR-ENDPOINT-ID
RUNPOD_API_KEY=your-runpod-api-key-here
```

## 🧪 Testing Your Setup

### 1. Test the Endpoint Directly

```python
import requests

# Test if Ollama is responding
response = requests.get("https://YOUR-WORKER-ID-11434.proxy.runpod.net/api/tags")
print("Available models:", response.json())

# Test text generation
payload = {
    "model": "CognitiveComputations/dolphin-mistral-nemo:latest",
    "prompt": "Hello! Tell me a joke.",
    "stream": False
}
response = requests.post(
    "https://YOUR-WORKER-ID-11434.proxy.runpod.net/api/generate",
    json=payload
)
print("Response:", response.json()["response"])
```

### 2. Test Your Flask App

```bash
# Start your Flask app
python web_chat.py

# Open browser to: http://localhost:8000
# Send a test message in the chat interface
```

### 3. Test Health Endpoint

```bash
curl http://localhost:8000/health
```

## 🔍 API Endpoints Reference

### Your RunPod Ollama API:
- **Health**: `GET https://your-endpoint/api/tags`
- **Generate**: `POST https://your-endpoint/api/generate`
- **Models**: `GET https://your-endpoint/api/tags`

### Your Flask Web App:
- **Chat Interface**: `http://localhost:8000/`
- **API Chat**: `POST http://localhost:8000/chat`
- **Simple Chat**: `POST http://localhost:8000/simple-chat`
- **Health Check**: `GET http://localhost:8000/health`

## 📊 Example API Calls

### Direct to RunPod Ollama:
```bash
curl -X POST https://YOUR-WORKER-ID-11434.proxy.runpod.net/api/generate \
  -H "Content-Type: application/json" \
  -d '{
    "model": "CognitiveComputations/dolphin-mistral-nemo:latest",
    "prompt": "Tell me a Scottish joke",
    "stream": false,
    "options": {
      "temperature": 0.7,
      "num_predict": 100
    }
  }'
```

### To Your Flask App:
```bash
curl -X POST http://localhost:8000/simple-chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello there!"}'
```

## ⚠️ Troubleshooting

### Common Issues:

1. **"Connection failed" errors**
   - ✅ Check your RunPod endpoint is running
   - ✅ Verify the URL format is correct
   - ✅ Ensure port 11434 is in the URL

2. **"Model not found" errors**
   - ✅ Check available models: `GET /api/tags`
   - ✅ Verify model name matches exactly: `CognitiveComputations/dolphin-mistral-nemo:latest`

3. **Slow responses**
   - ✅ Your model is now on 24GB GPU - should be much faster!
   - ✅ Check RunPod worker isn't scaling down due to inactivity

4. **Flask app errors**
   - ✅ Check console logs for detailed error messages
   - ✅ Test the endpoint directly first before blaming the Flask app

### Debug Commands:

```bash
# Check if your endpoint is running
curl https://YOUR-WORKER-ID-11434.proxy.runpod.net/api/tags

# Check Flask app health
curl http://localhost:8000/health

# View Flask app logs
python web_chat.py  # Watch console output
```

## 🎯 Best Practices

1. **URL Format**: Always include the trailing slash for base_url
2. **Model Name**: Use the full model name with namespace
3. **Error Handling**: The ChatBot component handles retries automatically
4. **Session Management**: Conversation history is stored in Flask sessions
5. **Cost Management**: RunPod charges per second of GPU usage

## 🚀 Ready to Chat!

Once configured, your Flask app will:
- ✅ Send chat messages to your RunPod Ollama endpoint
- ✅ Stream responses back to the web interface
- ✅ Maintain conversation history per session
- ✅ Handle errors gracefully with fallbacks

Your Scottish chatbot is now running on a powerful 24GB GPU in the cloud! 🏴󠁧󠁢󠁳󠁣󠁴󠁿🤖

---

## 📞 Need Help?

If you encounter issues:
1. Check the RunPod worker logs
2. Test the endpoint directly with curl
3. Check Flask console output for errors
4. Verify all URLs and API keys are correct