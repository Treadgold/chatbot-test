#!/bin/bash

# Fail2Ban Setup Script for Chatbot Application
# This script installs and configures fail2ban to protect against automated attacks

set -e

echo "🔒 Setting up Fail2Ban for Chatbot Application..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "❌ Please run this script as root (use sudo)"
    exit 1
fi

# Install fail2ban
echo "📦 Installing fail2ban..."
apt-get update
apt-get install -y fail2ban

# Create fail2ban directory if it doesn't exist
mkdir -p /etc/fail2ban/filter.d
mkdir -p /etc/fail2ban/jail.d

# Copy configuration files
echo "⚙️  Configuring fail2ban..."

# Copy jail configuration
cp jail.local /etc/fail2ban/jail.d/chatbot.conf

# Copy filter configurations
cp filter.d/chatbot-wordpress.conf /etc/fail2ban/filter.d/
cp filter.d/chatbot-rate-limit.conf /etc/fail2ban/filter.d/

# Create log directory for chatbot if needed
mkdir -p /var/log/chatbot
chown www-data:www-data /var/log/chatbot

# Enable and start fail2ban
echo "🚀 Starting fail2ban service..."
systemctl enable fail2ban
systemctl restart fail2ban

# Show status
echo "✅ Fail2ban setup complete!"
echo ""
echo "📊 Current status:"
fail2ban-client status

echo ""
echo "🔍 To monitor fail2ban:"
echo "  - View status: sudo fail2ban-client status"
echo "  - View specific jail: sudo fail2ban-client status chatbot-app"
echo "  - View logs: sudo tail -f /var/log/fail2ban.log"
echo ""
echo "⚠️  Important notes:"
echo "  - Adjust log paths in /etc/fail2ban/jail.d/chatbot.conf if needed"
echo "  - Test your configuration before deploying to production"
echo "  - Monitor logs to ensure legitimate users aren't being blocked"
echo ""
echo "🔧 Manual fail2ban commands:"
echo "  - Unban IP: sudo fail2ban-client set chatbot-app unbanip <IP>"
echo "  - Ban IP manually: sudo fail2ban-client set chatbot-app banip <IP>" 