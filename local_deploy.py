#!/usr/bin/env python3
"""
Local deployment script for RunPod Ollama Serverless Worker
Builds Docker image locally and deploys to RunPod
"""
import subprocess
import sys
import os
import json
import time
import requests
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class LocalDeployer:
    def __init__(self, docker_username: str, runpod_api_key: str):
        self.docker_username = docker_username
        self.runpod_api_key = runpod_api_key
        self.image_name = f"{docker_username}/runpod-ollama"
        self.base_url = "https://api.runpod.io/graphql"
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {runpod_api_key}"
        }

    def run_command(self, cmd: str, description: str) -> bool:
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

    def build_and_push_image(self, tag: str = "latest") -> Optional[str]:
        """Build and push the Docker image"""
        full_image_name = f"{self.image_name}:{tag}"
        
        print(f"\n🏗️ Building Docker image: {full_image_name}")
        
        # Build the image
        build_cmd = f"docker build -f Dockerfile.ollama -t {full_image_name} ."
        if not self.run_command(build_cmd, "Building Docker image"):
            return None
        
        # Push the image
        push_cmd = f"docker push {full_image_name}"
        if not self.run_command(push_cmd, "Pushing Docker image to Docker Hub"):
            return None
        
        print(f"✅ Image successfully pushed: {full_image_name}")
        return full_image_name

    def create_template(self, name: str, docker_image: str, config: Dict[str, Any]) -> Optional[str]:
        """Create a new template or update existing one"""
        query = """
        mutation CreateTemplate($input: PodTemplateInput!) {
            saveTemplate(input: $input) {
                id
                name
                dockerImage
                containerDiskSizeGb
                volumeInGb
                volumeMountPath
                env {
                    key
                    value
                }
                ports
                startJupyter
                startSsh
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "dockerImage": docker_image,
                "containerDiskSizeGb": config.get("container_disk_gb", 20),
                "volumeInGb": config.get("volume_gb", 0),
                "volumeMountPath": config.get("volume_mount_path", "/workspace"),
                "env": config.get("env", []),
                "ports": config.get("ports", "8000/http"),
                "startJupyter": config.get("start_jupyter", False),
                "startSsh": config.get("start_ssh", False)
            }
        }
        
        response = requests.post(
            self.base_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Error creating template: {data['errors']}")
                return None
            template_id = data["data"]["saveTemplate"]["id"]
            print(f"✅ Template created/updated: {template_id}")
            return template_id
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None

    def create_serverless_endpoint(self, name: str, template_id: str, config: Dict[str, Any]) -> Optional[str]:
        """Create a serverless endpoint"""
        query = """
        mutation CreateEndpoint($input: EndpointInput!) {
            createEndpoint(input: $input) {
                id
                name
                userId
                templateId
                gpuIds
                networkVolumeId
                locations
                idleTimeout
                scaleSettings {
                    workersMin
                    workersMax
                    jobsPerWorker
                }
            }
        }
        """
        
        variables = {
            "input": {
                "name": name,
                "templateId": template_id,
                "gpuIds": config.get("gpu_ids", "AMPERE_16"),
                "networkVolumeId": config.get("network_volume_id"),
                "locations": config.get("locations", "US"),
                "idleTimeout": config.get("idle_timeout", 5),
                "scaleSettings": {
                    "workersMin": config.get("workers_min", 0),
                    "workersMax": config.get("workers_max", 3),
                    "jobsPerWorker": config.get("jobs_per_worker", 1)
                }
            }
        }
        
        response = requests.post(
            self.base_url,
            json={"query": query, "variables": variables},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Error creating endpoint: {data['errors']}")
                return None
            endpoint_id = data["data"]["createEndpoint"]["id"]
            print(f"✅ Serverless endpoint created: {endpoint_id}")
            return endpoint_id
        else:
            print(f"❌ HTTP error: {response.status_code} - {response.text}")
            return None

    def get_existing_template(self, name: str) -> Optional[str]:
        """Get existing template ID by name"""
        query = """
        query GetTemplates {
            myself {
                templates {
                    id
                    name
                    dockerImage
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            json={"query": query},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Error getting templates: {data['errors']}")
                return None
            
            templates = data["data"]["myself"]["templates"]
            for template in templates:
                if template["name"] == name:
                    return template["id"]
        
        return None

    def get_existing_endpoint(self, name: str) -> Optional[str]:
        """Get existing endpoint ID by name"""
        query = """
        query GetEndpoints {
            myself {
                endpoints {
                    id
                    name
                    templateId
                }
            }
        }
        """
        
        response = requests.post(
            self.base_url,
            json={"query": query},
            headers=self.headers
        )
        
        if response.status_code == 200:
            data = response.json()
            if "errors" in data:
                print(f"❌ Error getting endpoints: {data['errors']}")
                return None
            
            endpoints = data["data"]["myself"]["endpoints"]
            for endpoint in endpoints:
                if endpoint["name"] == name:
                    return endpoint["id"]
        
        return None

    def test_endpoint(self, endpoint_id: str) -> bool:
        """Test the endpoint with a simple request"""
        test_url = f"https://api.runpod.ai/v2/{endpoint_id}/run"
        
        test_payload = {
            "input": {
                "prompt": "Hello, this is a test. Please respond briefly.",
                "model": "dolphin-mistral-nemo:latest",
                "options": {
                    "temperature": 0.7,
                    "num_predict": 50
                }
            }
        }
        
        print("🧪 Testing endpoint...")
        
        try:
            response = requests.post(
                test_url,
                json=test_payload,
                headers=self.headers,
                timeout=30
            )
            
            if response.status_code == 200:
                job_data = response.json()
                job_id = job_data.get("id")
                
                if job_id:
                    print(f"✅ Test job submitted: {job_id}")
                    return True
                else:
                    print(f"❌ Test failed: {job_data}")
                    return False
            else:
                print(f"❌ Test failed: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ Test error: {e}")
            return False


def load_config() -> Dict[str, Any]:
    """Load deployment configuration"""
    config_file = "scripts/runpod_config.json"
    
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            return json.load(f)
    
    # Default configuration
    return {
        "template_name": "ollama-serverless-template",
        "endpoint_name": "ollama-serverless-endpoint",
        "container_disk_gb": 20,
        "volume_gb": 0,
        "volume_mount_path": "/workspace",
        "env": [],
        "ports": "8000/http",
        "start_jupyter": False,
        "start_ssh": False,
        "gpu_ids": "AMPERE_16",
        "locations": "US",
        "idle_timeout": 5,
        "workers_min": 0,
        "workers_max": 3,
        "jobs_per_worker": 1
    }


def main():
    print("🚀 Local RunPod Deployment")
    print("=" * 40)
    
    # Check if Docker is installed
    if not subprocess.run("docker --version", shell=True, capture_output=True).returncode == 0:
        print("❌ Docker is not installed. Please install Docker first.")
        sys.exit(1)
    
    # Get credentials
    docker_username = os.getenv("DOCKER_USERNAME")
    runpod_api_key = os.getenv("RUNPOD_API_KEY")
    
    if not docker_username:
        docker_username = input("Enter your Docker Hub username: ").strip()
    
    if not runpod_api_key:
        runpod_api_key = input("Enter your RunPod API key: ").strip()
    
    if not docker_username or not runpod_api_key:
        print("❌ Both Docker username and RunPod API key are required")
        sys.exit(1)
    
    # Check if user is logged in to Docker Hub
    print("\n🔐 Checking Docker Hub authentication...")
    result = subprocess.run("docker info", shell=True, capture_output=True, text=True)
    
    if "Username:" not in result.stdout:
        print("You're not logged in to Docker Hub. Please log in:")
        if not subprocess.run("docker login", shell=True).returncode == 0:
            print("❌ Failed to log in to Docker Hub")
            sys.exit(1)
    
    # Initialize deployer
    deployer = LocalDeployer(docker_username, runpod_api_key)
    
    # Load configuration
    config = load_config()
    
    print(f"🐳 Docker Username: {docker_username}")
    print(f"📋 Template: {config['template_name']}")
    print(f"🔗 Endpoint: {config['endpoint_name']}")
    
    # Build and push image
    image_name = deployer.build_and_push_image()
    if not image_name:
        print("❌ Failed to build and push image")
        sys.exit(1)
    
    # Create or update template
    template_id = deployer.get_existing_template(config["template_name"])
    if template_id:
        print(f"📋 Using existing template: {template_id}")
    else:
        print("📋 Creating new template...")
        template_id = deployer.create_template(
            config["template_name"],
            image_name,
            config
        )
    
    if not template_id:
        print("❌ Failed to create template")
        sys.exit(1)
    
    # Create or update endpoint
    endpoint_id = deployer.get_existing_endpoint(config["endpoint_name"])
    if endpoint_id:
        print(f"🔗 Using existing endpoint: {endpoint_id}")
    else:
        print("🔗 Creating new endpoint...")
        endpoint_id = deployer.create_serverless_endpoint(
            config["endpoint_name"],
            template_id,
            config
        )
    
    if not endpoint_id:
        print("❌ Failed to create endpoint")
        sys.exit(1)
    
    # Test endpoint
    print("\n⏳ Waiting for endpoint to be ready...")
    time.sleep(10)  # Give it a moment to initialize
    
    if deployer.test_endpoint(endpoint_id):
        print("✅ Endpoint is working!")
    else:
        print("⚠️  Endpoint test failed, but endpoint was created")
    
    # Output summary
    print("\n📊 Deployment Summary:")
    print(f"   Template ID: {template_id}")
    print(f"   Endpoint ID: {endpoint_id}")
    print(f"   Endpoint URL: https://api.runpod.ai/v2/{endpoint_id}")
    print(f"   Docker Image: {image_name}")
    
    # Save endpoint info to file
    deployment_info = {
        "endpoint_id": endpoint_id,
        "template_id": template_id,
        "endpoint_url": f"https://api.runpod.ai/v2/{endpoint_id}",
        "docker_image": image_name,
        "deployed_at": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    with open("deployment_info.json", "w") as f:
        json.dump(deployment_info, f, indent=2)
    
    print(f"\n💾 Deployment info saved to: deployment_info.json")
    print("\n🎉 Deployment complete!")


if __name__ == "__main__":
    main() 