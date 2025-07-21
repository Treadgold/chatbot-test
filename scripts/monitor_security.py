#!/usr/bin/env python3
"""
Security Log Monitor for Chatbot Application

This script monitors the security logs and provides alerts for suspicious activity.
Run with: python3 scripts/monitor_security.py
"""

import os
import time
import re
from collections import defaultdict, deque
from datetime import datetime, timedelta
import argparse

class SecurityMonitor:
    def __init__(self, log_file='logs/chatbot_security.log'):
        self.log_file = log_file
        self.ip_counts = defaultdict(int)
        self.recent_events = deque(maxlen=1000)  # Keep last 1000 events
        self.alert_thresholds = {
            'wordpress_attacks': 5,  # Alert after 5 WordPress attacks from same IP
            'xss_attempts': 3,       # Alert after 3 XSS attempts from same IP
            'rate_limit_hits': 10,   # Alert after 10 rate limit violations
        }
        
    def parse_log_line(self, line):
        """Parse a log line and extract relevant information"""
        # Example log format: 2024-01-01 12:00:00,000 WARNING: Blocked WordPress attack attempt from 1.2.3.4: /wp-admin/ - User-Agent: BadBot
        
        patterns = {
            'wordpress': r'Blocked WordPress attack attempt from (\d+\.\d+\.\d+\.\d+): (.+?) - User-Agent: (.+)',
            'xss': r'XSS attempt blocked from (\d+\.\d+\.\d+\.\d+): (.+)',
            'long_message': r'Message too long from (\d+\.\d+\.\d+\.\d+): (\d+) characters',
            'malicious_file': r'Blocked malicious file extension request from (\d+\.\d+\.\d+\.\d+): (.+?) - User-Agent: (.+)'
        }
        
        for event_type, pattern in patterns.items():
            match = re.search(pattern, line)
            if match:
                timestamp = datetime.now()  # Could parse from log line if needed
                ip = match.group(1)
                return {
                    'timestamp': timestamp,
                    'type': event_type,
                    'ip': ip,
                    'details': match.groups(),
                    'line': line.strip()
                }
        return None
    
    def process_event(self, event):
        """Process a security event and check for alerts"""
        if not event:
            return
            
        self.recent_events.append(event)
        ip = event['ip']
        event_type = event['type']
        
        # Count events by IP and type
        key = f"{ip}_{event_type}"
        self.ip_counts[key] += 1
        
        # Check for alerts
        self.check_alerts(event)
    
    def check_alerts(self, event):
        """Check if an event should trigger an alert"""
        ip = event['ip']
        event_type = event['type']
        
        # WordPress attack threshold
        if event_type == 'wordpress':
            wp_count = self.ip_counts.get(f"{ip}_wordpress", 0)
            if wp_count >= self.alert_thresholds['wordpress_attacks']:
                self.send_alert(f"🚨 HIGH PRIORITY: IP {ip} has made {wp_count} WordPress attack attempts!")
        
        # XSS attempt threshold
        elif event_type == 'xss':
            xss_count = self.ip_counts.get(f"{ip}_xss", 0)
            if xss_count >= self.alert_thresholds['xss_attempts']:
                self.send_alert(f"🚨 XSS ATTACK: IP {ip} has made {xss_count} XSS attempts!")
        
        # Check for multiple different attack types from same IP
        ip_attack_types = [key for key in self.ip_counts.keys() if key.startswith(ip)]
        if len(ip_attack_types) >= 3:
            self.send_alert(f"🚨 SOPHISTICATED ATTACK: IP {ip} is using multiple attack vectors!")
    
    def send_alert(self, message):
        """Send an alert (print to console, could extend to email/SMS)"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        alert_msg = f"[{timestamp}] SECURITY ALERT: {message}"
        print(alert_msg)
        
        # Write to alerts log
        with open('logs/security_alerts.log', 'a') as f:
            f.write(alert_msg + '\n')
    
    def show_stats(self):
        """Display current security statistics"""
        print("\n" + "="*50)
        print("SECURITY STATISTICS")
        print("="*50)
        
        # Recent events summary
        event_types = defaultdict(int)
        unique_ips = set()
        
        for event in self.recent_events:
            event_types[event['type']] += 1
            unique_ips.add(event['ip'])
        
        print(f"Recent Events (last {len(self.recent_events)}):")
        for event_type, count in event_types.items():
            print(f"  {event_type}: {count}")
        
        print(f"\nUnique attacking IPs: {len(unique_ips)}")
        
        # Top attacking IPs
        ip_totals = defaultdict(int)
        for key, count in self.ip_counts.items():
            ip = key.split('_')[0]
            ip_totals[ip] += count
        
        if ip_totals:
            print("\nTop Attacking IPs:")
            sorted_ips = sorted(ip_totals.items(), key=lambda x: x[1], reverse=True)
            for ip, count in sorted_ips[:10]:
                print(f"  {ip}: {count} attacks")
    
    def monitor_file(self, follow=True):
        """Monitor the log file for new entries"""
        if not os.path.exists(self.log_file):
            print(f"Log file {self.log_file} not found. Creating directory...")
            os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
            return
        
        print(f"Monitoring {self.log_file} for security events...")
        print("Press Ctrl+C to stop\n")
        
        with open(self.log_file, 'r') as f:
            # Read existing lines first
            lines = f.readlines()
            for line in lines:
                event = self.parse_log_line(line)
                self.process_event(event)
            
            if follow:
                # Follow mode - watch for new lines
                f.seek(0, 2)  # Go to end of file
                try:
                    while True:
                        line = f.readline()
                        if line:
                            event = self.parse_log_line(line)
                            self.process_event(event)
                            if event:
                                print(f"[{datetime.now().strftime('%H:%M:%S')}] {event['type']}: {event['ip']}")
                        else:
                            time.sleep(1)
                except KeyboardInterrupt:
                    print("\nMonitoring stopped.")
                    self.show_stats()

def main():
    parser = argparse.ArgumentParser(description='Monitor chatbot security logs')
    parser.add_argument('--log-file', default='logs/chatbot_security.log', 
                       help='Path to the security log file')
    parser.add_argument('--no-follow', action='store_true', 
                       help='Analyze existing logs only, don\'t follow')
    parser.add_argument('--stats-only', action='store_true',
                       help='Show statistics and exit')
    
    args = parser.parse_args()
    
    monitor = SecurityMonitor(args.log_file)
    
    if args.stats_only:
        monitor.monitor_file(follow=False)
        monitor.show_stats()
    else:
        monitor.monitor_file(follow=not args.no_follow)

if __name__ == '__main__':
    main() 