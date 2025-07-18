#!/bin/bash

# Script to download Ollama model locally for Docker build optimization
set -e

MODEL_NAME="CognitiveComputations/dolphin-mistral-nemo:latest"
MODELS_DIR="./models"
OLLAMA_DATA_DIR="$HOME/.ollama"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
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

# Function to check if Ollama is installed
check_ollama() {
    if ! command -v ollama &> /dev/null; then
        print_error "Ollama is not installed or not in PATH"
        echo ""
        echo "To install Ollama, run:"
        echo "  curl -fsSL https://ollama.ai/install.sh | sh"
        echo ""
        exit 1
    fi
    print_success "Ollama is installed"
}

echo "🚀 === Local Model Download for Docker Build ==="
echo ""
print_status "Model: $MODEL_NAME"
print_status "Target directory: $MODELS_DIR"
echo ""

# Check if Ollama is available
check_ollama

# Create models directory
print_status "Creating models directory..."
mkdir -p "$MODELS_DIR"
print_success "Models directory ready"

# Check if model already exists locally
if [ -d "$OLLAMA_DATA_DIR/models" ] && [ "$(ls -A $OLLAMA_DATA_DIR/models)" ]; then
    print_success "Found existing Ollama models in $OLLAMA_DATA_DIR"
    
    # Copy existing models to our models directory
    print_status "Copying existing models to $MODELS_DIR..."
    cp -r "$OLLAMA_DATA_DIR"/* "$MODELS_DIR/"
    print_success "Models copied successfully"
    
    # List copied models
    echo ""
    print_status "Available models:"
    if [ -d "$MODELS_DIR/models" ]; then
        ls -la "$MODELS_DIR/models/" | head -10
        if [ $(ls -1 "$MODELS_DIR/models/" | wc -l) -gt 10 ]; then
            echo "... and $(($(ls -1 "$MODELS_DIR/models/" | wc -l) - 10)) more"
        fi
    else
        print_warning "No models found in copied directory"
    fi
    
else
    print_warning "No existing models found. Starting Ollama to download model..."
    echo ""
    
    # Start Ollama service
    print_status "Starting Ollama service..."
    ollama serve > /dev/null 2>&1 &
    OLLAMA_PID=$!
    
    # Wait for Ollama to be ready
    print_status "Waiting for Ollama service to start..."
    attempts=0
    max_attempts=30
    
    while [ $attempts -lt $max_attempts ]; do
        if ollama list >/dev/null 2>&1; then
            print_success "Ollama service is ready"
            break
        fi
        
        attempts=$((attempts + 1))
        echo -n "."
        sleep 2
        
        if [ $attempts -eq $max_attempts ]; then
            print_error "Ollama service failed to start after $max_attempts attempts"
            kill $OLLAMA_PID 2>/dev/null || true
            exit 1
        fi
    done
    echo ""
    
    # Download the model
    echo ""
    print_status "Downloading model: $MODEL_NAME"
    print_warning "This may take several minutes depending on your internet connection..."
    
    if ollama pull "$MODEL_NAME"; then
        print_success "Model downloaded successfully"
    else
        print_error "Failed to download model"
        kill $OLLAMA_PID 2>/dev/null || true
        exit 1
    fi
    
    # Stop Ollama service
    print_status "Stopping Ollama service..."
    kill $OLLAMA_PID
    wait $OLLAMA_PID 2>/dev/null || true
    print_success "Ollama service stopped"
    
    # Copy models to our directory
    print_status "Copying models to $MODELS_DIR..."
    cp -r "$OLLAMA_DATA_DIR"/* "$MODELS_DIR/"
    print_success "Model copied successfully"
fi

# Calculate and display size
echo ""
print_status "Calculating directory size..."
SIZE=$(du -sh $MODELS_DIR 2>/dev/null | cut -f1 || echo 'Unknown')

echo ""
echo "🎉 === Summary ==="
echo "📁 Models directory: $MODELS_DIR"
echo "📊 Size: $SIZE"
echo ""
print_success "Ready for Docker build! The build will use these local models."
echo ""
echo "💡 Tips:"
echo "   • To force re-download, delete the $MODELS_DIR directory and run this script again"
echo "   • The Docker build will be much faster now"
echo "   • You can build with: docker build -f Dockerfile.ollama -t your-image-name ." 