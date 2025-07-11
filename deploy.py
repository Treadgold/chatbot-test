#!/usr/bin/env python3
"""
Deployment script for RunPod Ollama Serverless Worker
"""
import subprocess
import sys
import os
import getpass

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}")
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False

def get_docker_info():
    """Get Docker Hub information from user"""
    print("\n📝 Docker Hub Configuration")
    print("You need a Docker Hub account to push your image.")
    print("Go to https://hub.docker.com if you don't have one.")
    
    username = input("Enter your Docker Hub username: ").strip()
    if not username:
        print("❌ Username is required")
        sys.exit(1)
    
    # Check if user is logged in to Docker Hub
    print("\n🔐 Checking Docker Hub authentication...")
    result = subprocess.run("docker info", shell=True, capture_output=True, text=True)
    
    if "Username:" not in result.stdout:
        print("You're not logged in to Docker Hub. Please log in:")
        if not run_command("docker login", "Logging in to Docker Hub"):
            sys.exit(1)
    
    return username

def build_and_push_image(username):
    """Build and push the Docker image"""
    image_name = f"{username}/runpod-ollama:latest"
    
    print(f"\n🏗️ Building Docker image: {image_name}")
    
    # Build the image
    build_cmd = f"docker build -f Dockerfile.ollama -t {image_name} ."
    if not run_command(build_cmd, "Building Docker image"):
        return None
    
    # Push the image
    push_cmd = f"docker push {image_name}"
    if not run_command(push_cmd, "Pushing Docker image to Docker Hub"):
        return None
    
    print(f"✅ Image successfully pushed: {image_name}")
    return image_name

def create_deployment_config(image_name):
    """Create deployment configuration"""
    config = f"""
# RunPod Serverless Endpoint Configuration

## Docker Image
{image_name}

## Recommended Settings:
- **Container Disk**: 20GB minimum (for model storage)
- **GPU Type**: RTX 4090 (24GB) or better for dolphin-mistral-nemo
- **Max Workers**: 1-3 (depending on expected load)
- **Idle Timeout**: 5 seconds (to minimize costs)
- **Max Execution Time**: 600 seconds (10 minutes)

## Environment Variables:
None required for basic setup.

## Test Payload:
```json
{json_payload}
```

## Next Steps:
1. Go to https://www.runpod.io/console/serverless
2. Click "New Endpoint"
3. Use the image name above
4. Configure the settings as recommended
5. Note down your ENDPOINT_ID and API_KEY
6. Test with: python test_deployed.py
"""
    
    with open('test_input.json', 'r') as f:
        json_payload = f.read()
    
    config = config.format(json_payload=json_payload)
    
    with open('deployment_config.txt', 'w') as f:
        f.write(config)
    
    print(f"✅ Deployment configuration saved to: deployment_config.txt")

def main():
    print("🚀 RunPod Ollama Serverless Deployment")
    print("=" * 50)
    
    # Check if Docker is installed
    if not run_command("docker --version", "Checking Docker installation"):
        print("❌ Docker is not installed. Please install Docker first.")
        sys.exit(1)
    
    # Check if required files exist
    required_files = ["ollama_handler.py", "Dockerfile.ollama", "test_input.json"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file not found: {file}")
            sys.exit(1)
    
    print("✅ All required files found")
    
    # Get Docker Hub info
    username = get_docker_info()
    
    # Build and push image
    image_name = build_and_push_image(username)
    if not image_name:
        print("❌ Failed to build and push image")
        sys.exit(1)
    
    # Create deployment configuration
    create_deployment_config(image_name)
    
    print("\n🎉 Build and Push Complete!")
    print("\nNext steps:")
    print("1. Read the deployment_config.txt file")
    print("2. Go to https://www.runpod.io/console/serverless")
    print("3. Create a new endpoint with the settings provided")
    print("4. Test with: python test_deployed.py")
    print("\nNote: The first request will take 3-10 minutes as it downloads the model.")

if __name__ == "__main__":
    main() 