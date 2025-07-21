#!/bin/bash

# Secure Deployment Script for Chatbot Application
# This script sets up the application with all security measures enabled

set -e

echo "🚀 Starting secure deployment of Chatbot Application..."

# Check if running as root (needed for some operations)
if [ "$EUID" -eq 0 ]; then
    echo "⚠️  Running as root. This is needed for system-level security setup."
else
    echo "ℹ️  Running as regular user. Some security features may require sudo."
fi

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p logs
mkdir -p scripts
chmod 755 logs scripts

# Set up environment variables for production
echo "⚙️  Setting up production environment..."
if [ ! -f .env ]; then
    echo "Creating .env file..."
    cat > .env << EOF
FLASK_ENV=production
FLASK_SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
RUNPOD_ENDPOINT=your-runpod-endpoint-here
RUNPOD_API_KEY=your-runpod-api-key-here
STRIPE_SECRET_KEY=your-stripe-secret-key-here
EOF
    echo "✅ Created .env file with secure random secret key"
    echo "⚠️  Please update the API keys in .env file!"
else
    echo "✅ .env file already exists"
fi

# Set proper permissions on sensitive files
echo "🔒 Setting file permissions..."
chmod 600 .env
chmod +x fail2ban/setup_fail2ban.sh
chmod +x scripts/monitor_security.py

# Install Python dependencies
echo "📦 Installing Python dependencies..."
if [ -f requirements.txt ]; then
    pip3 install -r requirements.txt
    echo "✅ Dependencies installed"
else
    echo "❌ requirements.txt not found!"
    exit 1
fi

# Set up firewall (if not already configured)
echo "🛡️  Checking firewall configuration..."
if command -v ufw >/dev/null 2>&1; then
    if ! ufw status | grep -q "Status: active"; then
        echo "Setting up UFW firewall..."
        if [ "$EUID" -eq 0 ]; then
            ufw default deny incoming
            ufw default allow outgoing
            ufw allow ssh
            ufw allow 80/tcp
            ufw allow 443/tcp
            ufw --force enable
            echo "✅ Firewall configured and enabled"
        else
            echo "⚠️  Firewall setup requires root. Run: sudo ufw enable"
        fi
    else
        echo "✅ Firewall already active"
    fi
else
    echo "⚠️  UFW not installed. Install with: sudo apt-get install ufw"
fi

# Setup fail2ban (optional)
echo "🚫 Setting up fail2ban..."
if [ -d fail2ban ]; then
    if [ "$EUID" -eq 0 ]; then
        cd fail2ban
        ./setup_fail2ban.sh
        cd ..
        echo "✅ Fail2ban configured"
    else
        echo "⚠️  Fail2ban setup requires root. Run: sudo ./fail2ban/setup_fail2ban.sh"
    fi
else
    echo "⚠️  Fail2ban configuration not found"
fi

# Test the application
echo "🧪 Testing application startup..."
if python3 -c "from web_chat import app; print('✅ Application imports successfully')" 2>/dev/null; then
    echo "✅ Application test passed"
else
    echo "❌ Application test failed - check your configuration"
    exit 1
fi

# Security checklist
echo ""
echo "🔍 SECURITY CHECKLIST:"
echo "======================="

# Check environment variables
if grep -q "FLASK_ENV=production" .env; then
    echo "✅ Production mode enabled"
else
    echo "❌ Production mode not set - check .env file"
fi

# Check secret key
if grep -q "FLASK_SECRET_KEY=" .env && ! grep -q "your-secret-key-here" .env; then
    echo "✅ Secure secret key configured"
else
    echo "❌ Default secret key detected - update .env file"
fi

# Check API keys
if grep -q "your-runpod-api-key-here" .env; then
    echo "❌ Default RunPod API key - update .env file"
else
    echo "✅ RunPod API key configured"
fi

# Check log directory
if [ -d logs ]; then
    echo "✅ Logs directory created"
else
    echo "❌ Logs directory missing"
fi

# Check permissions
if [ "$(stat -c %a .env)" = "600" ]; then
    echo "✅ .env file permissions secured"
else
    echo "❌ .env file permissions not secure"
fi

echo ""
echo "🚀 DEPLOYMENT COMPLETE!"
echo "======================"
echo ""
echo "📋 Next steps:"
echo "1. Update API keys in .env file"
echo "2. Start the application: python3 web_chat.py"
echo "3. Monitor security logs: python3 scripts/monitor_security.py"
echo "4. Set up reverse proxy (nginx/apache) for production"
echo "5. Configure SSL/TLS certificate"
echo ""
echo "📊 Monitoring commands:"
echo "- View security logs: tail -f logs/chatbot_security.log"
echo "- Monitor live: python3 scripts/monitor_security.py"
echo "- Check fail2ban status: sudo fail2ban-client status"
echo ""
echo "🆘 In case of security incidents:"
echo "- Block IP manually: sudo fail2ban-client set chatbot-app banip <IP>"
echo "- View attack statistics: python3 scripts/monitor_security.py --stats-only"
echo ""
echo "⚠️  Remember to:"
echo "- Keep dependencies updated: pip3 install -r requirements.txt --upgrade"
echo "- Review logs regularly"
echo "- Test security measures periodically" 