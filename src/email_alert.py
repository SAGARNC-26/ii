"""
Email Alert System for Unauthorized Person Detection
Sends email notifications with snapshots when unknown faces are detected
"""

import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from datetime import datetime, timedelta
import cv2
from typing import Optional
import base64
from io import BytesIO

from src.config import (
    ENABLE_EMAIL_ALERTS,
    EMAIL_SENDER,
    EMAIL_PASSWORD,
    EMAIL_RECIPIENT,
    SMTP_SERVER,
    SMTP_PORT,
    EMAIL_COOLDOWN,
    EMAIL_INCLUDE_SNAPSHOT
)

logger = logging.getLogger(__name__)


class EmailAlertSystem:
    """Handles email alerts for unauthorized detections"""
    
    def __init__(self):
        self.enabled = ENABLE_EMAIL_ALERTS
        self.sender = EMAIL_SENDER
        self.password = EMAIL_PASSWORD
        self.recipient = EMAIL_RECIPIENT
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.cooldown = EMAIL_COOLDOWN
        self.include_snapshot = EMAIL_INCLUDE_SNAPSHOT
        
        # Track last email time to avoid spam
        self.last_email_time = None
        
        # Validate configuration
        if self.enabled:
            if not self.password:
                logger.warning("⚠️ Email alerts enabled but EMAIL_PASSWORD not set. Please set it in .env file.")
                logger.warning("   For Gmail, use App Password: https://support.google.com/accounts/answer/185833")
                self.enabled = False
            else:
                logger.info(f"✓ Email alerts enabled: {self.sender} → {self.recipient}")
                logger.info(f"  Cooldown: {self.cooldown}s, Snapshots: {self.include_snapshot}")
    
    def can_send_email(self) -> bool:
        """Check if enough time has passed since last email (cooldown)"""
        if not self.last_email_time:
            return True
        
        elapsed = (datetime.now() - self.last_email_time).total_seconds()
        return elapsed >= self.cooldown
    
    def send_alert(self, 
                   camera_id: str = "cam_01", 
                   confidence: float = 0.0,
                   frame: Optional = None,
                   location: str = "Main Entrance") -> bool:
        """
        Send unauthorized person detection alert email
        
        Args:
            camera_id: Camera identifier
            confidence: Detection confidence score
            frame: OpenCV frame (BGR format) for snapshot
            location: Human-readable location name
            
        Returns:
            bool: True if email sent successfully
        """
        if not self.enabled:
            return False
        
        # Check cooldown
        if not self.can_send_email():
            remaining = self.cooldown - (datetime.now() - self.last_email_time).total_seconds()
            logger.debug(f"Email cooldown active. {remaining:.0f}s remaining")
            return False
        
        try:
            # Create email message
            msg = MIMEMultipart('related')
            msg['From'] = self.sender
            msg['To'] = self.recipient
            msg['Subject'] = f'🚨 SECURITY ALERT - Unauthorized Person Detected'
            
            # Email body
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            confidence_pct = confidence * 100
            
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .alert-box {{ 
                        background-color: #f8d7da; 
                        border: 2px solid #dc3545; 
                        border-radius: 5px; 
                        padding: 20px; 
                        margin: 20px 0;
                    }}
                    .alert-header {{ 
                        color: #721c24; 
                        font-size: 24px; 
                        font-weight: bold; 
                        margin-bottom: 15px;
                    }}
                    .detail-row {{ 
                        margin: 10px 0; 
                        padding: 8px; 
                        background-color: white;
                        border-radius: 3px;
                    }}
                    .label {{ font-weight: bold; color: #495057; }}
                    .value {{ color: #212529; }}
                    .warning {{ color: #dc3545; font-weight: bold; }}
                    .footer {{ 
                        margin-top: 30px; 
                        padding-top: 20px; 
                        border-top: 1px solid #ccc; 
                        color: #6c757d; 
                        font-size: 12px;
                    }}
                </style>
            </head>
            <body>
                <div class="alert-box">
                    <div class="alert-header">
                        🚨 UNAUTHORIZED PERSON DETECTED
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">Timestamp:</span>
                        <span class="value">{timestamp}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">Location:</span>
                        <span class="value">{location}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">Camera ID:</span>
                        <span class="value">{camera_id}</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="label">Detection Confidence:</span>
                        <span class="value">{confidence_pct:.1f}%</span>
                    </div>
                    
                    <div class="detail-row">
                        <span class="warning">⚠️ This person is NOT in the authorized database.</span>
                    </div>
                    
                    {"<div class='detail-row'><span class='label'>📸 Snapshot attached below</span></div>" if self.include_snapshot and frame is not None else ""}
                </div>
                
                {"<div style='margin: 20px 0;'><img src='cid:snapshot' style='max-width: 600px; border: 2px solid #dc3545;' /></div>" if self.include_snapshot and frame is not None else ""}
                
                <div class="footer">
                    <p>
                        <strong>Smart Vault CCTV Security System</strong><br>
                        Automated Facial Recognition & Access Control<br>
                        This is an automated alert. Please review the dashboard for more details.
                    </p>
                    <p>
                        Dashboard: <a href="http://localhost:5000">http://localhost:5000</a><br>
                        If this is a false alarm, you can enroll this person in the system.
                    </p>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Attach snapshot if available
            if self.include_snapshot and frame is not None:
                try:
                    # Convert frame to JPEG
                    _, buffer = cv2.imencode('.jpg', frame)
                    img_data = buffer.tobytes()
                    
                    # Attach image
                    image = MIMEImage(img_data, name=f'unauthorized_{timestamp.replace(":", "-")}.jpg')
                    image.add_header('Content-ID', '<snapshot>')
                    msg.attach(image)
                    
                except Exception as e:
                    logger.warning(f"Failed to attach snapshot: {e}")
            
            # Send email via SMTP
            logger.info(f"📧 Sending alert email to {self.recipient}...")
            
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()  # Enable TLS encryption
                server.login(self.sender, self.password)
                server.send_message(msg)
            
            # Update last email time
            self.last_email_time = datetime.now()
            
            logger.info(f"✅ Alert email sent successfully!")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error("❌ Email authentication failed. Check EMAIL_PASSWORD in .env")
            logger.error("   For Gmail, you need an App Password: https://support.google.com/accounts/answer/185833")
            self.enabled = False  # Disable to avoid repeated errors
            return False
            
        except Exception as e:
            logger.error(f"❌ Failed to send alert email: {e}")
            return False
    
    def get_cooldown_remaining(self) -> float:
        """Get remaining cooldown time in seconds"""
        if not self.last_email_time:
            return 0
        
        elapsed = (datetime.now() - self.last_email_time).total_seconds()
        remaining = max(0, self.cooldown - elapsed)
        return remaining


# Global instance
_email_system = None

def get_email_system() -> EmailAlertSystem:
    """Get or create global email alert system instance"""
    global _email_system
    if _email_system is None:
        _email_system = EmailAlertSystem()
    return _email_system


# Convenience function
def send_unauthorized_alert(camera_id: str = "cam_01", 
                           confidence: float = 0.0,
                           frame: Optional = None,
                           location: str = "Main Entrance") -> bool:
    """Quick function to send unauthorized person alert"""
    system = get_email_system()
    return system.send_alert(camera_id, confidence, frame, location)


if __name__ == '__main__':
    # Test email system
    print("Testing Email Alert System")
    print("=" * 50)
    
    system = EmailAlertSystem()
    print(f"Enabled: {system.enabled}")
    print(f"Sender: {system.sender}")
    print(f"Recipient: {system.recipient}")
    print(f"Cooldown: {system.cooldown}s")
    
    if system.enabled:
        print("\nSending test email...")
        success = system.send_alert(
            camera_id="cam_test",
            confidence=0.75,
            frame=None,
            location="Test Location"
        )
        print(f"Result: {'✅ Sent' if success else '❌ Failed'}")
