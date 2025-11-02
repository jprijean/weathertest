"""Email notification service for weather alerts."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional
from models import Intervention, Database

"""

Personal notes

"""


class EmailService:
    """Handles sending email notifications."""
    
    def __init__(self, smtp_host: str = None, smtp_port: int = 587,
                 sender_email: str = None, sender_password: Optional[str] = None,
                 use_tls: bool = True, use_resend: bool = False, 
                 resend_api_key: Optional[str] = None):
        """Initialize the email service.
        
        Args:
            smtp_host: SMTP server hostname (if using SMTP)
            smtp_port: SMTP server port (if using SMTP)
            sender_email: Email address to send from
            sender_password: Password for sender email (None for no auth, if using SMTP)
            use_tls: Whether to use TLS encryption (if using SMTP)
            use_resend: Whether to use Resend API instead of SMTP
            resend_api_key: Resend API key (if using Resend)
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.use_tls = use_tls
        self.use_resend = use_resend
        
        if use_resend:
            try:
                import resend
                if resend_api_key:
                    resend.api_key = resend_api_key
                else:
                    # Try to get from environment
                    import os
                    resend.api_key = os.getenv("RESEND_API_KEY")
                self.resend_client = resend
            except ImportError:
                print("Warning: Resend package not installed. Install with: pip install resend")
                self.use_resend = False
    
    def send_alert_email(self, recipient_email: str, intervention: Intervention) -> bool:
        """Send an alert email to a recipient.
        
        Args:
            recipient_email: Email address to send to
            intervention: Intervention object with alert details
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            subject = f"Weather Alert: {intervention.title}"
            body = f"""{intervention.title}

{intervention.description}

This is an automated weather alert from the Weather Alert System.
"""
            
            # Use Resend if configured

            
            if self.use_resend:
                params = {
                    "from": self.sender_email,
                    "to": [recipient_email],
                    "subject": subject,
                    "html": f"<p>{body.replace(chr(10), '<br>')}</p>",
                }
                email = self.resend_client.Emails.send(params)
                print(f"Alert email sent to {recipient_email} via Resend")
                return True
            else:
                # Use SMTP
                msg = MIMEMultipart()
                msg['From'] = self.sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                msg.attach(MIMEText(body, 'plain'))
                
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                
                if self.use_tls:
                    server.starttls()
                
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
                server.send_message(msg)
                server.quit()
                
                print(f"Alert email sent to {recipient_email} via SMTP")
                return True
        
        except Exception as e:
            print(f"Error sending email to {recipient_email}: {e}")
            return False
    
    def send_alerts_for_location(self, db: Database, building_code: str, 
                                 intervention_id: str) -> int:
        """Send alert emails to all owners for a location.
        
        Args:
            db: Database instance
            building_code: Building code for the location
            intervention_id: Intervention ID to send
            
        Returns:
            Number of emails sent successfully
        """
        if intervention_id == "no-alert":
            return 0
        
        intervention = db.get_intervention(intervention_id)
        if not intervention:
            print(f"Intervention {intervention_id} not found")
            return 0
        
        emails = db.get_location_emails(building_code)
        if not emails:
            print(f"No emails found for building {building_code}")
            return 0
        
        sent_count = 0
        for email in emails:
            email = email.strip()
            if email and self.send_alert_email(email, intervention):
                sent_count += 1
        
        return sent_count

