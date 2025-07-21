# Chatbot Systemd Service

This directory contains files to run your chatbot application as a reliable systemd service for production use.

## Files Created

- `chatbot.service` - Systemd service configuration
- `deploy_service.sh` - Deployment and management script
- `SERVICE_README.md` - This documentation

## Quick Start

### 1. Install and Start the Service

```bash
./deploy_service.sh install
```

This will:
- Install the service to `/etc/systemd/system/chatbot.service`
- Enable it to start automatically on boot
- Start the service immediately
- Show the service status

### 2. Check Service Status

```bash
./deploy_service.sh status
```

### 3. View Logs

```bash
# View recent logs
./deploy_service.sh logs

# Follow logs in real-time
./deploy_service.sh follow
```

## Service Management Commands

```bash
# Start the service
./deploy_service.sh start

# Stop the service
./deploy_service.sh stop

# Restart the service
./deploy_service.sh restart

# View help
./deploy_service.sh help
```

## Service Features

### Reliability
- **Automatic restart**: Service restarts automatically if it crashes
- **Boot start**: Service starts automatically when the server boots
- **Graceful shutdown**: Proper signal handling for clean shutdowns
- **Timeout protection**: Prevents hanging during stop operations

### Performance
- **Multiple workers**: Configured with 2 uvicorn workers for better performance
- **Resource limits**: File descriptor limits set appropriately
- **Proper environment**: Virtual environment and Python path configured

### Security
- **User isolation**: Runs as ubuntu user, not root
- **File system protection**: Limited file system access
- **No privilege escalation**: Cannot gain additional privileges
- **Private temp**: Isolated temporary directory

### Monitoring
- **Systemd integration**: Full integration with systemd logging and monitoring
- **Journal logging**: Logs are sent to systemd journal
- **Service identification**: Logs are tagged with "chatbot" identifier

## Configuration Details

The service is configured to:
- Run on `0.0.0.0:8000` (accessible from all interfaces)
- Use 2 worker processes for better performance
- Restart automatically with a 5-second delay
- Log all output to systemd journal
- Use your virtual environment at `.venv/`

## Troubleshooting

### Service won't start
```bash
# Check service status for error details
sudo systemctl status chatbot

# View detailed logs
sudo journalctl -u chatbot -n 50
```

### Port already in use
If port 8000 is already in use, stop your manual uvicorn process first:
```bash
# Find the process using port 8000
sudo netstat -tlnp | grep :8000

# Kill the process (replace PID with actual process ID)
kill <PID>
```

### Permission issues
Make sure the service file has correct permissions:
```bash
sudo chmod 644 /etc/systemd/system/chatbot.service
sudo systemctl daemon-reload
```

## Uninstalling

To completely remove the service:
```bash
./deploy_service.sh uninstall
```

## Manual Commands (if needed)

If you prefer to use systemctl directly:

```bash
# Install service manually
sudo cp chatbot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable chatbot
sudo systemctl start chatbot

# Service management
sudo systemctl start chatbot    # Start
sudo systemctl stop chatbot     # Stop
sudo systemctl restart chatbot  # Restart
sudo systemctl status chatbot   # Status

# Logs
sudo journalctl -u chatbot       # All logs
sudo journalctl -u chatbot -f    # Follow logs
``` 