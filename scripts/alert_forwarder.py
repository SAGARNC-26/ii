"""
Smart Vault CCTV - Suricata Alert Forwarder
Monitors Suricata logs and forwards alerts to Flask dashboard via WebSocket
"""

import os
import sys
import time
import re
import requests
import logging
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import SURICATA_ALERT_LOG, ALERT_ENDPOINT

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class SuricataAlertForwarder:
    """
    Monitor Suricata alert logs and forward to Flask dashboard.
    """
    
    def __init__(self, log_file: str = None, endpoint: str = None):
        """
        Initialize forwarder.
        
        Args:
            log_file: Path to Suricata fast.log
            endpoint: Flask endpoint URL
        """
        self.log_file = log_file or SURICATA_ALERT_LOG
        self.endpoint = endpoint or ALERT_ENDPOINT
        self.position = 0
        
        logger.info("Suricata Alert Forwarder initialized")
        logger.info(f"Monitoring: {self.log_file}")
        logger.info(f"Forwarding to: {self.endpoint}")
    
    def check_log_file(self) -> bool:
        """Check if log file exists and is readable"""
        if not os.path.exists(self.log_file):
            logger.error(f"Log file not found: {self.log_file}")
            return False
        
        if not os.access(self.log_file, os.R_OK):
            logger.error(f"Log file not readable: {self.log_file}")
            logger.info("Try: sudo chmod 644 /var/log/suricata/fast.log")
            return False
        
        return True
    
    def parse_alert(self, line: str) -> dict:
        """
        Parse Suricata fast.log alert line.
        
        Format: timestamp [**] [gid:sid:rev] message [**] [Classification] [Priority] {protocol} src_ip:port -> dst_ip:port
        
        Args:
            line: Alert line from fast.log
        
        Returns:
            Parsed alert dictionary
        """
        try:
            # Parse timestamp
            timestamp_match = re.match(r'(\d{2}/\d{2}/\d{4}-\d{2}:\d{2}:\d{2}\.\d+)', line)
            timestamp = timestamp_match.group(1) if timestamp_match else None
            
            # Parse signature info [gid:sid:rev]
            sig_match = re.search(r'\[\*\*\]\s*\[(\d+):(\d+):(\d+)\]', line)
            gid, sid, rev = sig_match.groups() if sig_match else (None, None, None)
            
            # Parse message
            msg_match = re.search(r'\]\s*([^\[]+?)\s*\[\*\*\]', line)
            message = msg_match.group(1).strip() if msg_match else "Unknown alert"
            
            # Parse classification
            class_match = re.search(r'\[Classification:\s*([^\]]+)\]', line)
            classification = class_match.group(1) if class_match else None
            
            # Parse priority
            priority_match = re.search(r'\[Priority:\s*(\d+)\]', line)
            priority = int(priority_match.group(1)) if priority_match else None
            
            # Parse protocol and addresses
            proto_match = re.search(r'\{(\w+)\}\s+([^:]+):(\d+)\s+->\s+([^:]+):(\d+)', line)
            if proto_match:
                protocol, src_ip, src_port, dst_ip, dst_port = proto_match.groups()
            else:
                protocol = src_ip = src_port = dst_ip = dst_port = None
            
            return {
                'timestamp': timestamp,
                'alert_type': 'suricata',
                'gid': gid,
                'sid': sid,
                'rev': rev,
                'message': message,
                'classification': classification,
                'priority': priority,
                'protocol': protocol,
                'src_ip': src_ip,
                'src_port': src_port,
                'dst_ip': dst_ip,
                'dst_port': dst_port,
                'raw': line.strip()
            }
            
        except Exception as e:
            logger.error(f"Failed to parse alert: {e}")
            return {
                'alert_type': 'suricata',
                'message': line.strip(),
                'raw': line.strip()
            }
    
    def forward_alert(self, alert: dict) -> bool:
        """
        Forward alert to Flask dashboard.
        
        Args:
            alert: Alert dictionary
        
        Returns:
            True if successful
        """
        try:
            response = requests.post(
                self.endpoint,
                json=alert,
                timeout=5
            )
            
            if response.status_code == 200:
                logger.info(f"Alert forwarded: {alert['message']}")
                return True
            else:
                logger.warning(f"Forward failed: HTTP {response.status_code}")
                return False
                
        except requests.exceptions.ConnectionError:
            logger.error("Connection failed. Is Flask server running?")
            return False
        except requests.exceptions.Timeout:
            logger.error("Request timeout")
            return False
        except Exception as e:
            logger.error(f"Forward error: {e}")
            return False
    
    def tail_log(self):
        """
        Tail log file and forward new alerts.
        Similar to 'tail -f' behavior.
        """
        logger.info("Starting log monitor...")
        
        with open(self.log_file, 'r') as f:
            # Go to end of file
            f.seek(0, 2)
            self.position = f.tell()
            
            while True:
                line = f.readline()
                
                if line:
                    # New alert found
                    alert = self.parse_alert(line)
                    self.forward_alert(alert)
                    self.position = f.tell()
                else:
                    # No new data, wait
                    time.sleep(0.5)
                    
                    # Check if file was rotated
                    current_size = os.path.getsize(self.log_file)
                    if current_size < self.position:
                        logger.info("Log file rotated, resetting position")
                        f.seek(0)
                        self.position = 0
    
    def run(self):
        """Main run loop with error recovery"""
        logger.info("=" * 60)
        logger.info("  Suricata Alert Forwarder Started")
        logger.info("=" * 60)
        
        # Check log file
        if not self.check_log_file():
            logger.error("Cannot start forwarder")
            logger.info("\nTroubleshooting:")
            logger.info("  1. Ensure Suricata is running: sudo systemctl status suricata")
            logger.info("  2. Check log file exists: ls -la /var/log/suricata/")
            logger.info("  3. Fix permissions: sudo chmod 644 /var/log/suricata/fast.log")
            return
        
        # Main loop with reconnection
        retry_count = 0
        max_retries = 5
        
        while True:
            try:
                self.tail_log()
            except KeyboardInterrupt:
                logger.info("\nShutting down...")
                break
            except FileNotFoundError:
                logger.error(f"Log file disappeared: {self.log_file}")
                time.sleep(5)
            except Exception as e:
                logger.error(f"Error: {e}")
                retry_count += 1
                
                if retry_count >= max_retries:
                    logger.error(f"Max retries ({max_retries}) reached. Exiting.")
                    break
                
                wait_time = min(60, 2 ** retry_count)
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Forward Suricata alerts to Smart Vault dashboard'
    )
    parser.add_argument(
        '--log-file',
        default=SURICATA_ALERT_LOG,
        help='Path to Suricata fast.log'
    )
    parser.add_argument(
        '--endpoint',
        default=ALERT_ENDPOINT,
        help='Flask alert endpoint URL'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Send a test alert and exit'
    )
    
    args = parser.parse_args()
    
    forwarder = SuricataAlertForwarder(
        log_file=args.log_file,
        endpoint=args.endpoint
    )
    
    if args.test:
        # Send test alert
        logger.info("Sending test alert...")
        test_alert = {
            'alert_type': 'suricata',
            'message': 'Test Alert from Forwarder',
            'priority': 1,
            'timestamp': datetime.now().isoformat()
        }
        success = forwarder.forward_alert(test_alert)
        if success:
            logger.info("✓ Test alert sent successfully")
        else:
            logger.error("✗ Test alert failed")
        return
    
    # Run forwarder
    try:
        forwarder.run()
    except KeyboardInterrupt:
        logger.info("\nStopped by user")


if __name__ == '__main__':
    main()
