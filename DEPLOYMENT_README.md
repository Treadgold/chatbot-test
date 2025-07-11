# GitHub Actions + RunPod Serverless Deployment

This repository is set up with GitHub Actions to automatically build Docker images and deploy them to RunPod serverless endpoints.

## 🚀 Features

- **Automated Docker builds** on every push to main
- **Multi-platform support** (AMD64 and ARM64)
- **Docker layer caching** for faster builds
- **Automatic RunPod deployment** after successful builds
- **Security attestations** for supply chain security
- **Manual deployment triggers** via GitHub Actions UI

## 🛠️ Setup Instructions

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and Variables → Actions, and add these secrets:

#### Required Secrets:
- `DOCKER_USERNAME`: Your Docker Hub username
- `DOCKER_PASSWORD`: Your Docker Hub password or access token
- `RUNPOD_API_KEY`: Your RunPod API key

#### Getting Your RunPod API Key:
1. Go to [RunPod Settings](https://www.runpod.io/console/user/settings)
2. Navigate to the "API Keys" section
3. Create a new API key
4. Copy the key and add it to GitHub Secrets

### 2. Configure Docker Hub

Make sure you have:
1. A Docker Hub account
2. A repository named `runpod-ollama` (or update the image name in the workflow)
3. Your Docker Hub credentials added to GitHub Secrets

### 3. Configure RunPod Settings

Edit `scripts/runpod_config.json` to customize your deployment:

```json
{
  "template_name": "ollama-serverless-template",
  "endpoint_name": "ollama-serverless-endpoint",
  "container_disk_gb": 20,
  "volume_gb": 0,
  "gpu_ids": "AMPERE_16",
  "locations": "US",
  "idle_timeout": 5,
  "workers_min": 0,
  "workers_max": 3,
  "jobs_per_worker": 1
}
```

#### GPU Options:
- `AMPERE_16`: RTX 4090 (24GB) - Recommended for most models
- `AMPERE_24`: RTX 3090 (24GB) 
- `AMPERE_48`: RTX 6000 Ada (48GB) - For larger models
- `AMPERE_80`: A100 (80GB) - For very large models

#### Location Options:
- `US`: United States
- `EU`: Europe
- `AS`: Asia

## 📦 How It Works

### Automatic Deployment
1. **Push to main branch** → Triggers build and deployment
2. **Docker image is built** using `Dockerfile.ollama`
3. **Image is pushed** to Docker Hub
4. **RunPod template** is created/updated
5. **Serverless endpoint** is created/updated
6. **Endpoint is tested** with a simple request

### Manual Deployment
1. Go to **Actions** tab in your GitHub repository
2. Select **"Build and Push Ollama Image"** workflow
3. Click **"Run workflow"**
4. Check **"Deploy to RunPod after build"** if you want to deploy
5. Click **"Run workflow"** button

## 🔍 Monitoring Deployments

### GitHub Actions Logs
- Go to **Actions** tab to see build and deployment logs
- Each step is logged with emojis for easy identification:
  - 🔄 Building Docker image
  - 📋 Creating/updating template
  - 🔗 Creating/updating endpoint
  - 🧪 Testing endpoint
  - ✅ Success indicators

### RunPod Console
- Visit [RunPod Console](https://www.runpod.io/console/serverless)
- Check your endpoints and templates
- Monitor usage and costs

## 🧪 Testing Your Deployment

### Test Endpoint Directly
```bash
# Replace YOUR_ENDPOINT_ID with your actual endpoint ID
curl -X POST \
  https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/run \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_RUNPOD_API_KEY" \
  -d '{
    "input": {
      "prompt": "Hello! How are you?",
      "model": "dolphin-mistral-nemo:latest",
      "options": {
        "temperature": 0.7,
        "num_predict": 100
      }
    }
  }'
```

### Test with Python
```python
import requests
import time

endpoint_id = "YOUR_ENDPOINT_ID"
api_key = "YOUR_RUNPOD_API_KEY"

# Submit job
response = requests.post(
    f"https://api.runpod.ai/v2/{endpoint_id}/run",
    json={
        "input": {
            "prompt": "Tell me a joke",
            "model": "dolphin-mistral-nemo:latest",
            "options": {"temperature": 0.7, "num_predict": 100}
        }
    },
    headers={"Authorization": f"Bearer {api_key}"}
)

job_id = response.json()["id"]
print(f"Job submitted: {job_id}")

# Poll for results
while True:
    status_response = requests.get(
        f"https://api.runpod.ai/v2/{endpoint_id}/status/{job_id}",
        headers={"Authorization": f"Bearer {api_key}"}
    )
    
    status_data = status_response.json()
    if status_data["status"] == "COMPLETED":
        print("Response:", status_data["output"])
        break
    elif status_data["status"] == "FAILED":
        print("Job failed:", status_data)
        break
    
    time.sleep(2)
```

## 💰 Cost Optimization

### Recommended Settings:
- **Idle Timeout**: 5 seconds (minimize idle costs)
- **Workers Min**: 0 (no minimum running workers)
- **Workers Max**: 1-3 (based on expected load)
- **Container Disk**: 20GB (sufficient for most models)

### Cost Factors:
- **Cold Start**: First request takes 3-10 minutes (downloads model)
- **Warm Requests**: Subsequent requests are fast (< 30 seconds)
- **Idle Time**: You're only charged when processing requests
- **GPU Type**: Higher-end GPUs cost more but process faster

## 🔧 Troubleshooting

### Common Issues:

#### Build Failures:
- Check Docker Hub credentials in GitHub Secrets
- Verify Dockerfile.ollama syntax
- Check for sufficient disk space in runner

#### Deployment Failures:
- Verify RunPod API key is correct
- Check RunPod account has sufficient credits
- Ensure GPU type is available in selected region

#### Endpoint Not Responding:
- Wait 3-10 minutes for cold start
- Check RunPod console for error logs
- Verify model name matches what's in your handler

### Debug Commands:
```bash
# Test local Docker build
docker build -f Dockerfile.ollama -t test-image .

# Test RunPod deployment script locally
export RUNPOD_API_KEY="your-key-here"
export DOCKER_IMAGE="your-image:latest"
python scripts/deploy_runpod.py
```

## 📚 Additional Resources

- [RunPod Documentation](https://docs.runpod.io/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Hub Documentation](https://docs.docker.com/docker-hub/)
- [Ollama Documentation](https://ollama.ai/docs)

## 🔄 Updating Your Deployment

1. **Update Code**: Make changes to your code
2. **Commit & Push**: Push to main branch
3. **Automatic Build**: GitHub Actions will build and deploy
4. **Monitor**: Check Actions tab for progress
5. **Test**: Verify your endpoint works with new changes

## 🎯 Next Steps

1. **Set up secrets** in GitHub repository
2. **Push code** to trigger first build
3. **Monitor deployment** in Actions tab
4. **Test endpoint** with sample requests
5. **Customize configuration** as needed

Your RunPod serverless endpoint will be automatically created and updated with each push to main! 