# Ollama GPU Deployment Guide

This guide ensures your Ollama deployment properly utilizes GPU acceleration for optimal performance.

## 🚀 Key Improvements Made

### 1. **Official Ollama Base Image**
- Changed from `nvidia/cuda:12.9.1-devel-ubuntu22.04` to `ollama/ollama:latest`
- The official image is optimized for GPU support and includes all necessary CUDA libraries
- Reduces image size and build complexity

### 2. **GPU Environment Variables**
```bash
# Force GPU-only mode
OLLAMA_NUM_CPU=0
OLLAMA_N_GPU_LAYERS=9999
OLLAMA_CTX_SIZE=8192
OLLAMA_GPU_OVERHEAD=0
OLLAMA_FLASH_ATTENTION=true
```

### 3. **NVIDIA Runtime Configuration**
- Proper `NVIDIA_VISIBLE_DEVICES=all`
- `NVIDIA_DRIVER_CAPABILITIES=compute,utility`
- Docker runtime configuration for GPU access

## 🛠️ Deployment Options

### Option 1: RunPod Serverless (Recommended)
Your current setup is optimized for RunPod. The Dockerfile includes:
- GPU environment variables
- Proper port exposure (11434)
- Optimized startup script

### Option 2: Local Docker with GPU
```bash
# Build the image
docker build -f Dockerfile.ollama -t ollama-gpu .

# Run with GPU support
docker run --gpus all \
  -p 11434:11434 \
  -e OLLAMA_NUM_CPU=0 \
  -e OLLAMA_N_GPU_LAYERS=9999 \
  -e OLLAMA_CTX_SIZE=8192 \
  -e OLLAMA_GPU_OVERHEAD=0 \
  -e OLLAMA_FLASH_ATTENTION=true \
  ollama-gpu
```

### Option 3: Docker Compose (Local)
```bash
# Start with GPU support
docker-compose -f docker-compose.gpu.yml up -d

# Check logs
docker-compose -f docker-compose.gpu.yml logs -f
```

## 🧪 Testing GPU Support

### 1. Run the GPU Test Script
```bash
python3 test_gpu_support.py
```

This script checks:
- ✅ NVIDIA GPU detection
- ✅ Environment variables
- ✅ Ollama API connectivity
- ✅ GPU inference test

### 2. Manual GPU Verification
```bash
# Check GPU availability
nvidia-smi

# Check Ollama GPU usage
curl http://localhost:11434/api/generate \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "model": "CognitiveComputations/dolphin-mistral-nemo:latest",
    "prompt": "Hello, are you using GPU?",
    "stream": false
  }'
```

### 3. Monitor GPU Usage
```bash
# Watch GPU usage during inference
watch -n 1 nvidia-smi
```

## 🔧 RunPod Configuration

### Recommended RunPod Settings:
```json
{
  "template_name": "ollama-gpu-template",
  "endpoint_name": "ollama-gpu-endpoint",
  "container_disk_gb": 20,
  "gpu_ids": "AMPERE_16",  // RTX 4090 (24GB)
  "locations": "US",
  "idle_timeout": 5,
  "workers_min": 0,
  "workers_max": 3,
  "jobs_per_worker": 1
}
```

### GPU Options for RunPod:
- `AMPERE_16`: RTX 4090 (24GB) - **Recommended**
- `AMPERE_24`: RTX 3090 (24GB)
- `AMPERE_48`: RTX 6000 Ada (48GB) - For larger models
- `AMPERE_80`: A100 (80GB) - For very large models

## 📊 Performance Optimization

### Model-Specific GPU Layers
For optimal performance, adjust `OLLAMA_N_GPU_LAYERS` based on your model:

| Model Size | GPU Layers | Memory Usage | 24GB VRAM Status |
|------------|------------|--------------|------------------|
| 7B         | 35         | ~8GB         | ✅ Excellent     |
| 12B (Nemo) | 9999       | ~12-15GB     | ✅ Optimal       |
| 13B        | 43         | ~16GB        | ✅ Good          |
| 30B        | 60         | ~32GB        | ❌ Too Large     |
| 70B        | 80         | ~64GB        | ❌ Too Large     |

**Current Model: CognitiveComputations/dolphin-mistral-nemo (12B)**
- Quantized Size: 7.1GB 
- With Context (8192): ~12-15GB total VRAM
- Recommended for 24GB: ✅ Perfect fit

### Context Size Optimization
```bash
# For 24GB VRAM with 12B model (Recommended)
OLLAMA_CTX_SIZE=8192

# For longer conversations (may use more VRAM)
OLLAMA_CTX_SIZE=16384

# For memory-constrained environments
OLLAMA_CTX_SIZE=4096

# Conservative setting (always fits)
OLLAMA_CTX_SIZE=2048
```

**VRAM Impact for dolphin-mistral-nemo (12B):**
- Context 2048: ~11GB total VRAM
- Context 4096: ~12GB total VRAM  
- Context 8192: ~14GB total VRAM ✅ (Recommended)
- Context 16384: ~18GB total VRAM (may be tight)

## 🚨 Troubleshooting

### Common Issues:

#### 1. GPU Not Detected
```bash
# Check if nvidia-smi works
nvidia-smi

# Verify Docker GPU runtime
docker run --rm --gpus all nvidia/cuda:12.9.1-base-ubuntu22.04 nvidia-smi
```

#### 2. Out of Memory Errors
```bash
# Reduce GPU layers
export OLLAMA_N_GPU_LAYERS=35

# Reduce context size
export OLLAMA_CTX_SIZE=4096

# Enable CPU fallback
export OLLAMA_NUM_CPU=4
```

#### 3. Slow Performance
```bash
# Enable flash attention
export OLLAMA_FLASH_ATTENTION=true

# Reduce GPU overhead
export OLLAMA_GPU_OVERHEAD=0

# Increase context size for better throughput
export OLLAMA_CTX_SIZE=8192
```

#### 4. Model Download Issues
```bash
# Check available disk space
df -h

# Verify network connectivity
curl -I https://ollama.ai

# Try downloading with verbose output
ollama pull CognitiveComputations/dolphin-mistral-nemo:latest --verbose
```

### Debug Commands:
```bash
# Check Ollama logs
docker logs <container_name>

# Monitor GPU usage
nvidia-smi -l 1

# Test API endpoint
curl http://localhost:11434/api/tags

# Check environment variables
docker exec <container_name> env | grep OLLAMA
```

## 📈 Performance Benchmarks

### Expected Performance (RTX 4090):
- **Cold Start**: 3-10 minutes (model download)
- **Warm Inference**: 20-50 tokens/second
- **Memory Usage**: 8-16GB depending on model
- **Context Processing**: 8192 tokens

### Optimization Tips:
1. **Use Flash Attention**: `OLLAMA_FLASH_ATTENTION=true`
2. **Optimize GPU Layers**: Match to your model size
3. **Monitor Memory**: Use `nvidia-smi` to track usage
4. **Batch Requests**: Process multiple requests together when possible

## 🔒 Security Considerations

### Environment Variables:
- GPU environment variables are safe to expose
- No sensitive information in GPU config
- Consider using secrets for API keys

### Network Security:
- Ollama API runs on port 11434
- Use reverse proxy for production deployments
- Implement rate limiting for public endpoints

## 📚 Additional Resources

- [Ollama GPU Documentation](https://github.com/ollama/ollama/blob/main/docs/gpu.md)
- [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/)
- [RunPod GPU Documentation](https://docs.runpod.io/docs/gpu-support)

---

**Note**: This configuration is optimized for the `CognitiveComputations/dolphin-mistral-nemo:latest` model. For other models, adjust the GPU layers and context size accordingly. 