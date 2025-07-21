#!/bin/bash

# Chatbot Service Deployment Script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="chatbot"
SERVICE_FILE="${SCRIPT_DIR}/${SERVICE_NAME}.service"
SYSTEM_SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "🚀 Deploying Chatbot Service..."

# Function to check if running as root
check_sudo() {
    if [[ $EUID -eq 0 ]]; then
        echo "❌ Please run this script as a regular user, not as root"
        echo "   The script will use sudo when needed"
        exit 1
    fi
}

# Function to install the service
install_service() {
    echo "📋 Installing systemd service..."
    
    # Copy service file to system directory
    sudo cp "${SERVICE_FILE}" "${SYSTEM_SERVICE_FILE}"
    
    # Set proper permissions
    sudo chmod 644 "${SYSTEM_SERVICE_FILE}"
    
    # Reload systemd
    sudo systemctl daemon-reload
    
    # Enable service to start on boot
    sudo systemctl enable "${SERVICE_NAME}"
    
    echo "✅ Service installed successfully!"
}

# Function to start the service
start_service() {
    echo "🟢 Starting ${SERVICE_NAME} service..."
    sudo systemctl start "${SERVICE_NAME}"
    echo "✅ Service started!"
}

# Function to stop the service
stop_service() {
    echo "🔴 Stopping ${SERVICE_NAME} service..."
    sudo systemctl stop "${SERVICE_NAME}"
    echo "✅ Service stopped!"
}

# Function to check service status
status_service() {
    echo "📊 Service Status:"
    sudo systemctl status "${SERVICE_NAME}" --no-pager -l
}

# Function to show logs
show_logs() {
    echo "📜 Recent logs:"
    sudo journalctl -u "${SERVICE_NAME}" --no-pager -l -n 50
}

# Function to follow logs in real-time
follow_logs() {
    echo "📜 Following logs (Ctrl+C to exit):"
    sudo journalctl -u "${SERVICE_NAME}" -f
}

# Function to restart the service
restart_service() {
    echo "🔄 Restarting ${SERVICE_NAME} service..."
    sudo systemctl restart "${SERVICE_NAME}"
    echo "✅ Service restarted!"
}

# Function to uninstall the service
uninstall_service() {
    echo "🗑️  Uninstalling ${SERVICE_NAME} service..."
    sudo systemctl stop "${SERVICE_NAME}" 2>/dev/null || true
    sudo systemctl disable "${SERVICE_NAME}" 2>/dev/null || true
    sudo rm -f "${SYSTEM_SERVICE_FILE}"
    sudo systemctl daemon-reload
    echo "✅ Service uninstalled!"
}

# Function to check prerequisites
check_prerequisites() {
    echo "🔍 Checking prerequisites..."
    
    # Check if service file exists
    if [[ ! -f "${SERVICE_FILE}" ]]; then
        echo "❌ Service file not found: ${SERVICE_FILE}"
        exit 1
    fi
    
    # Check if virtual environment exists
    if [[ ! -d "${SCRIPT_DIR}/.venv310" ]]; then
        echo "❌ Virtual environment not found: ${SCRIPT_DIR}/.venv310"
        echo "   Please create a virtual environment first"
        exit 1
    fi
    
    # Check if uvicorn is installed
    if [[ ! -f "${SCRIPT_DIR}/.venv310/bin/python" ]]; then
        echo "❌ Python not found in virtual environment"
        echo "   Please check your virtual environment"
        exit 1
    fi
    
    # Check if asgi.py exists
    if [[ ! -f "${SCRIPT_DIR}/asgi.py" ]]; then
        echo "❌ asgi.py not found in ${SCRIPT_DIR}"
        exit 1
    fi
    
    echo "✅ Prerequisites check passed!"
}

# Main script logic
case "${1:-install}" in
    "install")
        check_sudo
        check_prerequisites
        install_service
        start_service
        status_service
        ;;
    "start")
        start_service
        ;;
    "stop")
        stop_service
        ;;
    "restart")
        restart_service
        ;;
    "status")
        status_service
        ;;
    "logs")
        show_logs
        ;;
    "follow")
        follow_logs
        ;;
    "uninstall")
        uninstall_service
        ;;
    "help"|"-h"|"--help")
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  install    Install and start the service (default)"
        echo "  start      Start the service"
        echo "  stop       Stop the service"
        echo "  restart    Restart the service"
        echo "  status     Show service status"
        echo "  logs       Show recent logs"
        echo "  follow     Follow logs in real-time"
        echo "  uninstall  Remove the service"
        echo "  help       Show this help message"
        ;;
    *)
        echo "❌ Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac 