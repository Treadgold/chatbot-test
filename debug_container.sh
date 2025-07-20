#!/bin/bash

# Container debugging and testing script
set -e

IMAGE_NAME="ollama-pod:latest"
CONTAINER_NAME="ollama-test"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to clean up existing container
cleanup() {
    print_status "Cleaning up existing containers..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Function to build the image
build_image() {
    print_status "Building Docker image..."
    if docker build -f Dockerfile.ollama -t $IMAGE_NAME .; then
        print_success "Image built successfully"
    else
        print_error "Failed to build image"
        exit 1
    fi
}

# Function to run the container
run_container() {
    print_status "Starting container..."
    docker run -d \
        --name $CONTAINER_NAME \
        --gpus all \
        -p 11434:11434 \
        $IMAGE_NAME
    
    if [ $? -eq 0 ]; then
        print_success "Container started: $CONTAINER_NAME"
    else
        print_error "Failed to start container"
        exit 1
    fi
}

# Function to wait for container to be ready
wait_for_container() {
    print_status "Waiting for container to be ready..."
    
    for i in {1..30}; do
        if docker exec $CONTAINER_NAME curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            print_success "Container is ready!"
            return 0
        fi
        echo -n "."
        sleep 2
    done
    
    print_error "Container failed to become ready"
    return 1
}

# Function to show container logs
show_logs() {
    print_status "Container logs:"
    docker logs $CONTAINER_NAME
}

# Function to test the container
test_container() {
    print_status "Testing container functionality..."
    
    # Copy test script into container
    docker cp test_container.py $CONTAINER_NAME:/app/
    
    # Run tests
    if docker exec $CONTAINER_NAME python3 /app/test_container.py; then
        print_success "All tests passed!"
    else
        print_error "Tests failed"
        return 1
    fi
}

# Function to get interactive shell
get_shell() {
    print_status "Opening interactive shell in container..."
    docker exec -it $CONTAINER_NAME /bin/bash
}

# Function to check models in container
check_models() {
    print_status "Checking models in container..."
    echo ""
    echo "Models directory structure:"
    docker exec $CONTAINER_NAME find /root/.ollama/models -type f | head -10
    echo ""
    echo "Available models via API:"
    docker exec $CONTAINER_NAME curl -s http://localhost:11434/api/tags | jq '.models[]? | .name'
}

# Main menu
main() {
    echo "🚀 Ollama Container Debug Tool"
    echo "=============================="
    echo ""
    echo "Choose an action:"
    echo "1) Build image"
    echo "2) Run container"
    echo "3) Test container"
    echo "4) Show logs"
    echo "5) Check models"
    echo "6) Get shell"
    echo "7) Cleanup"
    echo "8) Full rebuild and test"
    echo "9) Exit"
    echo ""
    read -p "Enter choice [1-9]: " choice
    
    case $choice in
        1)
            build_image
            ;;
        2)
            cleanup
            run_container
            wait_for_container
            ;;
        3)
            test_container
            ;;
        4)
            show_logs
            ;;
        5)
            check_models
            ;;
        6)
            get_shell
            ;;
        7)
            cleanup
            ;;
        8)
            cleanup
            build_image
            run_container
            wait_for_container
            test_container
            ;;
        9)
            echo "Goodbye!"
            exit 0
            ;;
        *)
            print_error "Invalid choice"
            main
            ;;
    esac
}

# Check if docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Run main menu
main 