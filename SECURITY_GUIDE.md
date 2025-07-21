# Security Guide for Chatbot Application

## Overview
This guide outlines security measures implemented and recommended for your Flask chatbot application to protect against common web attacks and automated scanning.

## Current Security Measures Implemented

### 1. Rate Limiting
- **Implemented**: Flask-Limiter with default limits
- **Protection**: 200 requests/day, 50/hour, 10/minute per IP
- **Blocks**: Automated scanners and DoS attempts

### 2. Malicious Request Blocking
- **WordPress Attack Prevention**: Automatically blocks requests for WordPress-related paths
- **File Extension Filtering**: Blocks dangerous file extensions (.asp, .jsp, .cgi, .exe, .bat)
- **Common Attack Patterns**: Filters known vulnerability scanning attempts

### 3. Security Headers
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Browser XSS protection
- `Strict-Transport-Security` - Forces HTTPS (when using SSL)
- `Content-Security-Policy` - Controls resource loading

### 4. Input Validation
- **Message Length Limits**: Max 1000 characters per message
- **XSS Prevention**: Blocks script injection attempts
- **Content Filtering**: Basic validation of user input

### 5. Production Configuration
- **Debug Mode**: Disabled in production
- **Host Binding**: Restricted to localhost in production
- **Environment-based Configuration**: FLASK_ENV controls security settings

## Additional Security Recommendations

### 1. Reverse Proxy Setup (Recommended)
Use Nginx or Apache as a reverse proxy:

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    
    location / {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
    
    # Block common attack patterns
    location ~* /(wp-|wordpress|xmlrpc\.php) {
        return 404;
    }
}
```

### 2. Firewall Configuration
```bash
# UFW firewall rules
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. Fail2Ban Setup
Install and configure fail2ban to automatically block suspicious IPs:

```bash
sudo apt-get install fail2ban
```

See `fail2ban/` directory for configuration files.

### 4. SSL/TLS Certificate
- Use Let's Encrypt for free SSL certificates
- Redirect all HTTP traffic to HTTPS
- Use strong cipher suites

### 5. Environment Variables Security
Ensure sensitive data is properly secured:

```bash
# Set proper permissions on .env file
chmod 600 .env

# Example .env content:
FLASK_SECRET_KEY=your-very-long-random-secret-key-here
RUNPOD_API_KEY=your-runpod-api-key
STRIPE_SECRET_KEY=your-stripe-secret-key
FLASK_ENV=production
```

### 6. Regular Updates
- Keep system packages updated
- Update Python dependencies regularly
- Monitor security advisories

### 7. Logging and Monitoring
- Enable access logs
- Monitor for suspicious patterns
- Set up alerts for unusual activity

## Security Checklist for Production

- [ ] Environment variables properly secured
- [ ] Debug mode disabled (`FLASK_ENV=production`)
- [ ] Rate limiting configured
- [ ] Security headers enabled
- [ ] Input validation implemented
- [ ] Reverse proxy configured
- [ ] Firewall enabled
- [ ] Fail2ban installed and configured
- [ ] SSL certificate installed
- [ ] Regular backups configured
- [ ] Monitoring and alerting set up
- [ ] Dependencies updated
- [ ] Access logs reviewed regularly

## Monitoring Suspicious Activity

Watch for these patterns in logs:
- Multiple 404 errors from same IP
- Requests for non-existent WordPress files
- Rapid successive requests (rate limiting violations)
- Attempts to access admin interfaces
- Unusual user agents or referrers

## Response to Security Incidents

1. **Immediate Response**:
   - Block the attacking IP
   - Review logs for scope of attack
   - Check for successful breaches

2. **Investigation**:
   - Analyze attack patterns
   - Update security rules if needed
   - Document incident

3. **Prevention**:
   - Update fail2ban rules
   - Enhance rate limiting if needed
   - Review and update security measures

## Contact and Reporting

For security issues or questions:
- Review logs regularly
- Test security measures periodically
- Stay informed about new threats

---

**Note**: The automated scanning you're seeing (WordPress-related requests) is completely normal for any public web server. The security measures implemented will effectively block these attacks while allowing legitimate users to access your application. 