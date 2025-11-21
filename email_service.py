"""Email notification service for weather alerts."""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Dict
from models import Intervention, Database
from status_calculator import calculate_site_status, get_status_label, get_status_description

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
        
        DEPRECATED: Use send_daily_status_emails instead.
        
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
    
    def send_daily_status_email(self, recipient_email: str, sites: List[Dict]) -> bool:
        """
        Send a daily status email to a recipient with all their sites' statuses.
        
        Args:
            recipient_email: Email address to send to
            sites: List of site dictionaries with keys:
                - building_code: Building identifier
                - status: Site status ('green', 'red', 'yellow', 'purple')
                - windspeed: Current wind speed
                - precipitation: Current precipitation
                - timestamp: Last update timestamp
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from datetime import datetime
            
            subject = f"Daily Weather Status Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Build HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #137fec; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .site-card {{ 
                        border: 2px solid #ddd; 
                        border-radius: 8px; 
                        margin: 15px 0; 
                        padding: 15px; 
                        background-color: #f9f9f9;
                    }}
                    .status-green {{ border-color: #22c55e; background-color: #f0fdf4; }}
                    .status-red {{ border-color: #ef4444; background-color: #fef2f2; }}
                    .status-yellow {{ border-color: #f59e0b; background-color: #fffbeb; }}
                    .status-purple {{ border-color: #a855f7; background-color: #faf5ff; }}
                    .status-badge {{
                        display: inline-block;
                        padding: 5px 15px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 14px;
                        margin-bottom: 10px;
                    }}
                    .badge-green {{ background-color: #22c55e; color: white; }}
                    .badge-red {{ background-color: #ef4444; color: white; }}
                    .badge-yellow {{ background-color: #f59e0b; color: white; }}
                    .badge-purple {{ background-color: #a855f7; color: white; }}
                    .site-header {{ font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                    .site-details {{ margin: 10px 0; }}
                    .detail-row {{ margin: 5px 0; }}
                    .footer {{ 
                        margin-top: 30px; 
                        padding-top: 20px; 
                        border-top: 1px solid #ddd; 
                        color: #666; 
                        font-size: 12px; 
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>Daily Weather Status Report</h1>
                    <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p>Here is the daily weather status for all your registered sites:</p>
            """
            
            for site in sites:
                status = site.get('status', 'green')
                status_label = get_status_label(status)
                status_desc = get_status_description(status)
                building_code = site.get('building_code', 'Unknown')
                windspeed = site.get('windspeed', 0)
                precipitation = site.get('precipitation', 0)
                timestamp = site.get('timestamp', '')
                
                # Format timestamp
                try:
                    if timestamp:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00').split('+')[0])
                        formatted_time = ts.strftime('%Y-%m-%d %H:%M')
                    else:
                        formatted_time = 'N/A'
                except:
                    formatted_time = timestamp
                
                html_body += f"""
                    <div class="site-card status-{status}">
                        <div class="site-header">{building_code}</div>
                        <div class="status-badge badge-{status}">{status_label}</div>
                        <p style="margin: 10px 0; color: #666;">{status_desc}</p>
                        <div class="site-details">
                            <div class="detail-row"><strong>Wind Speed:</strong> {windspeed:.2f} m/s</div>
                            <div class="detail-row"><strong>Precipitation:</strong> {precipitation:.2f} mm</div>
                            <div class="detail-row"><strong>Last Update:</strong> {formatted_time}</div>
                        </div>
                    </div>
                """
            
            html_body += """
                    <p style="margin-top: 20px;">This is an automated daily weather status report from the Weather Alert System.</p>
                </div>
                <div class="footer">
                    <p>Weather Alert System - Automated Daily Report</p>
                    <p>You are receiving this email because you are registered as an owner for these sites.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"Daily Weather Status Report - {datetime.now().strftime('%Y-%m-%d')}\n\n"
            text_body += "Here is the daily weather status for all your registered sites:\n\n"
            
            for site in sites:
                status = site.get('status', 'green')
                status_label = get_status_label(status)
                building_code = site.get('building_code', 'Unknown')
                windspeed = site.get('windspeed', 0)
                precipitation = site.get('precipitation', 0)
                timestamp = site.get('timestamp', '')
                
                try:
                    if timestamp:
                        ts = datetime.fromisoformat(timestamp.replace('Z', '+00:00').split('+')[0])
                        formatted_time = ts.strftime('%Y-%m-%d %H:%M')
                    else:
                        formatted_time = 'N/A'
                except:
                    formatted_time = timestamp
                
                text_body += f"{building_code} - Status: {status_label}\n"
                text_body += f"  Wind Speed: {windspeed:.2f} m/s\n"
                text_body += f"  Precipitation: {precipitation:.2f} mm\n"
                text_body += f"  Last Update: {formatted_time}\n\n"
            
            text_body += "\nThis is an automated daily weather status report."
            
            # Send email
            if self.use_resend:
                params = {
                    "from": self.sender_email,
                    "to": [recipient_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                }
                email = self.resend_client.Emails.send(params)
                print(f"Daily status email sent to {recipient_email} via Resend")
                return True
            else:
                # Use SMTP
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                
                # Add both plain text and HTML versions
                part1 = MIMEText(text_body, 'plain')
                part2 = MIMEText(html_body, 'html')
                
                msg.attach(part1)
                msg.attach(part2)
                
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                
                if self.use_tls:
                    server.starttls()
                
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
                server.send_message(msg)
                server.quit()
                
                print(f"Daily status email sent to {recipient_email} via SMTP")
                return True
        
        except Exception as e:
            print(f"Error sending daily status email to {recipient_email}: {e}")
            return False
    
    def send_status_change_alert(self, recipient_email: str, building_code: str, 
                                 new_status: str, alert_type: Optional[str] = None) -> bool:
        """
        Send an immediate alert email when a site status changes from green to another color.
        
        Args:
            recipient_email: Email address to send to
            building_code: Building code that changed status
            new_status: New status ('red', 'yellow', or 'purple')
            alert_type: Type of alert that triggered ('Windspeed' or 'Precipitation')
        
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            from datetime import datetime
            from status_calculator import get_status_label
            
            status_label = get_status_label(new_status)
            alert_type_label = "High Wind Alert" if alert_type == "Windspeed" else "Precipitation Alert" if alert_type == "Precipitation" else "Weather Alert"
            
            subject = f"⚠️ Weather Alert: {building_code} - {status_label}"
            
            # Build HTML email body
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .header {{ background-color: #ef4444; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; }}
                    .alert-box {{ 
                        border: 2px solid #ef4444; 
                        border-radius: 8px; 
                        margin: 20px 0; 
                        padding: 20px; 
                        background-color: #fef2f2;
                    }}
                    .status-badge {{
                        display: inline-block;
                        padding: 8px 20px;
                        border-radius: 20px;
                        font-weight: bold;
                        font-size: 16px;
                        margin: 10px 0;
                    }}
                    .badge-red {{ background-color: #ef4444; color: white; }}
                    .badge-yellow {{ background-color: #f59e0b; color: white; }}
                    .badge-purple {{ background-color: #a855f7; color: white; }}
                    .building-code {{ font-size: 24px; font-weight: bold; margin: 15px 0; color: #1e293b; }}
                    .alert-type {{ font-size: 18px; color: #64748b; margin: 10px 0; }}
                    .footer {{ 
                        margin-top: 30px; 
                        padding-top: 20px; 
                        border-top: 1px solid #ddd; 
                        color: #666; 
                        font-size: 12px; 
                        text-align: center;
                    }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h1>⚠️ Weather Alert</h1>
                    <p>{datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
                </div>
                <div class="content">
                    <p>Hello,</p>
                    <p><strong>A weather alert has been triggered for one of your registered sites.</strong></p>
                    
                    <div class="alert-box">
                        <div class="building-code">{building_code}</div>
                        <div class="status-badge badge-{new_status}">{status_label}</div>
                        <div class="alert-type">Alert Type: <strong>{alert_type_label}</strong></div>
                    </div>
                    
                    <p>Please review the weather conditions and take appropriate action as needed.</p>
                    <p>You will receive a daily status report at 8:00 AM with updates on all your sites.</p>
                </div>
                <div class="footer">
                    <p>Weather Alert System - Immediate Alert Notification</p>
                    <p>You are receiving this email because you are registered as an owner for this site.</p>
                </div>
            </body>
            </html>
            """
            
            # Plain text version
            text_body = f"Weather Alert - {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
            text_body += "A weather alert has been triggered for one of your registered sites.\n\n"
            text_body += f"Building Code: {building_code}\n"
            text_body += f"Status: {status_label}\n"
            text_body += f"Alert Type: {alert_type_label}\n\n"
            text_body += "Please review the weather conditions and take appropriate action as needed.\n"
            text_body += "You will receive a daily status report at 8:00 AM with updates on all your sites.\n"
            
            # Send email
            if self.use_resend:
                params = {
                    "from": self.sender_email,
                    "to": [recipient_email],
                    "subject": subject,
                    "html": html_body,
                    "text": text_body,
                }
                email = self.resend_client.Emails.send(params)
                print(f"Status change alert email sent to {recipient_email} via Resend")
                return True
            else:
                # Use SMTP
                msg = MIMEMultipart('alternative')
                msg['From'] = self.sender_email
                msg['To'] = recipient_email
                msg['Subject'] = subject
                
                # Add both plain text and HTML versions
                part1 = MIMEText(text_body, 'plain')
                part2 = MIMEText(html_body, 'html')
                
                msg.attach(part1)
                msg.attach(part2)
                
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                
                if self.use_tls:
                    server.starttls()
                
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
                server.send_message(msg)
                server.quit()
                
                print(f"Status change alert email sent to {recipient_email} via SMTP")
                return True
        
        except Exception as e:
            print(f"Error sending status change alert email to {recipient_email}: {e}")
            return False

