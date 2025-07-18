
#!/bin/bash

# Build script for Ollama Docker image with local model optimization
set -e

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

# Default values
IMAGE_NAME="ollama-pod"
TAG="latest"
SKIP_MODEL_DOWNLOAD=false

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -t|--tag)
            TAG="$2"
            shift 2
            ;;
        -n|--name)
            IMAGE_NAME="$2"
            shift 2
            ;;
        --skip-model-download)
            SKIP_MODEL_DOWNLOAD=true
            shift
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -t, --tag TAG              Docker image tag (default: latest)"
            echo "  -n, --name NAME            Docker image name (default: ollama-pod)"
            echo "  --skip-model-download      Skip model download step"
            echo "  -h, --help                 Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0                                    # Build with default settings"
            echo "  $0 -t v1.0 -n my-ollama              # Build with custom name and tag"
            echo "  $0 --skip-model-download             # Build without downloading models"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "🚀 === Ollama Docker Build with Local Models ==="
echo ""
print_status "Image name: $FULL_IMAGE_NAME"
print_status "Skip model download: $SKIP_MODEL_DOWNLOAD"
echo ""

# Check if Docker is available
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed or not in PATH"
    exit 1
fi
print_success "Docker is available"

# Download models if not skipped
if [ "$SKIP_MODEL_DOWNLOAD" = false ]; then
    print_status "Step 1: Downloading models locally..."
    if [ -f "scripts/download_model_local.sh" ]; then
        chmod +x scripts/download_model_local.sh
        ./scripts/download_model_local.sh
        print_success "Model download completed"
    else
        print_error "download_model_local.sh script not found"
        exit 1
    fi
else
    print_warning "Skipping model download (--skip-model-download flag used)"
fi

echo ""
print_status "Step 2: Building Docker image..."

# Build the Docker image
if docker build -f Dockerfile.ollama -t "$FULL_IMAGE_NAME" .; then
    print_success "Docker image built successfully: $FULL_IMAGE_NAME"
else
    print_error "Docker build failed"
    exit 1
fi

echo ""
echo "🎉 === Build Complete ==="
print_success "Image: $FULL_IMAGE_NAME"
print_success "Size: $(docker images $FULL_IMAGE_NAME --format 'table {{.Size}}' | tail -1)"
echo ""
echo "💡 Next steps:"
echo "   • Test locally: docker run --gpus all -p 11434:11434 $FULL_IMAGE_NAME"
echo "   • Push to registry: docker push $FULL_IMAGE_NAME"
echo "   • Deploy to RunPod using your existing workflow" 