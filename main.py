"""Main application entry point for the weather alert system."""
import schedule
import time
import os
from datetime import datetime
from dotenv import load_dotenv

from typing import Dict, List, Optional
from models import Database
from weather_api import WeatherAPI
from comparison_engine import ComparisonEngine
from email_service import EmailService
from status_calculator import calculate_site_status, determine_alert_type
from datetime import datetime, timedelta


class WeatherAlertSystem:
    """Main weather alert system coordinator."""
    
    def __init__(self):
        """Initialize the weather alert system."""
        load_dotenv()
        
        # Initialize database
        self.db = Database()
        
        # Initialize weather API
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if not api_key:
            raise ValueError("OPENWEATHER_API_KEY not found in environment variables")
        units = os.getenv("WEATHER_UNITS", "metric")
        self.weather_api = WeatherAPI(api_key, units)
        
        # Initialize comparison engine
        self.comparison_engine = ComparisonEngine(self.db)
        
        # Initialize email service (optional, only if configured)
        self.email_service = None
        use_resend = os.getenv("USE_RESEND", "false").lower() == "true"
        sender_email = os.getenv("SENDER_EMAIL")
        
        if use_resend and sender_email:
            # Use Resend API
            resend_api_key = os.getenv("RESEND_API_KEY")
            if resend_api_key:
                self.email_service = EmailService(
                    sender_email=sender_email,
                    use_resend=True,
                    resend_api_key=resend_api_key
                )
                print("Email service configured with Resend API")
        else:
            # Use SMTP
            smtp_host = os.getenv("SMTP_HOST")
            if smtp_host and sender_email:
                smtp_port = int(os.getenv("SMTP_PORT", "587"))
                sender_password = os.getenv("SENDER_PASSWORD")
                use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
                
                self.email_service = EmailService(
                    smtp_host, smtp_port, sender_email, 
                    sender_password, use_tls
                )
                print("Email service configured with SMTP")
    
    def process_weather_check(self):
        """Main processing function: fetch weather, compare, and save results."""
        print(f"\n[{datetime.now()}] Starting weather check...")
        
        locations = self.db.get_all_locations()
        
        if not locations:
            print("No locations found in database")
            return
        
        for location in locations:
            print(f"Processing location: {location.building_code}")
            
            # Get previous status BEFORE saving new results
            previous_status = calculate_site_status(self.db, location.building_code)
            
            # Fetch weather data
            weather_data = self.weather_api.get_weather_for_location(
                location.latitude, 
                location.longitude
            )
            
            if not weather_data:
                print(f"  Failed to fetch weather data for {location.building_code}")
                continue
            
            print(f"  Fetched {len(weather_data)} weather data points")
            
            # Run comparison engine
            results = self.comparison_engine.compare_weather_data(
                location.building_code,
                weather_data
            )
            
            # Save results to database
            for result in results:
                self.db.save_result(result)
            
            print(f"  Saved {len(results)} results to database")
            
            # Check for status change from green to non-green
            if previous_status == 'green':
                # Calculate new status after saving results
                new_status = calculate_site_status(self.db, location.building_code)
                
                # If status changed from green to non-green, send alert
                if new_status != 'green' and new_status != previous_status:
                    print(f"  Status changed from {previous_status} to {new_status} - sending alert emails")
                    self.send_status_change_alerts(location, new_status)
        
        print(f"[{datetime.now()}] Weather check completed")
    
    def send_status_change_alerts(self, location, new_status: str):
        """
        Send immediate alert emails when status changes from green to non-green.
        
        Args:
            location: Location object
            new_status: New status ('red', 'yellow', or 'purple')
        """
        if not self.email_service:
            print("  Email service not configured. Skipping status change alerts.")
            return
        
        # Get latest result to determine alert type
        latest_result = self.db.get_latest_result(location.building_code)
        if not latest_result:
            print(f"  No latest result found for {location.building_code}")
            return
        
        # Determine which alert type triggered the status change
        alert_type = determine_alert_type(self.db, location.building_code, latest_result)
        
        # Get owner emails
        owner_emails = location.owner_emails
        if not owner_emails:
            print(f"  No owner emails found for {location.building_code}")
            return
        
        # Send alert email to each owner
        sent_count = 0
        for email in owner_emails:
            email = email.strip()
            if email:
                if self.email_service.send_status_change_alert(
                    email, 
                    location.building_code, 
                    new_status, 
                    alert_type
                ):
                    sent_count += 1
                    print(f"    ✓ Alert email sent to {email}")
                else:
                    print(f"    ✗ Failed to send alert email to {email}")
        
        print(f"  Sent {sent_count} status change alert email(s) for {location.building_code}")
    
    def send_daily_status_emails(self):
        """
        Send daily status emails at 8:00 AM.
        One email per owner with all their sites' statuses.
        """
        from config import ALERT_HOUR
        current_hour = datetime.now().hour
        
        if current_hour != ALERT_HOUR:
            print(f"Current time is {datetime.now().strftime('%H:%M')}, not {ALERT_HOUR}:00. Skipping daily emails.")
            return
        
        if not self.email_service:
            print("Email service not configured. Skipping daily emails.")
            return
        
        print(f"\n[{datetime.now()}] Starting daily status email check...")
        
        # Get all locations
        locations = self.db.get_all_locations()
        
        if not locations:
            print("No locations found. Skipping daily emails.")
            return
        
        # Group sites by owner email
        # Dictionary: email -> list of sites
        email_to_sites: Dict[str, List[Dict]] = {}
        
        for location in locations:
            # Calculate status for this site
            status = calculate_site_status(self.db, location.building_code)
            
            # Get latest result for current data
            latest_result = self.db.get_latest_result(location.building_code)
            
            site_data = {
                'building_code': location.building_code,
                'status': status,
                'windspeed': latest_result.get('windspeed_val', 0) if latest_result else 0,
                'precipitation': latest_result.get('precipitation_val', 0) if latest_result else 0,
                'timestamp': latest_result.get('timestamp', '') if latest_result else ''
            }
            
            # Add this site to each owner's email list
            owner_emails = location.owner_emails
            for email in owner_emails:
                email = email.strip()
                if email:
                    if email not in email_to_sites:
                        email_to_sites[email] = []
                    email_to_sites[email].append(site_data)
        
        # Send one email per owner
        total_sent = 0
        for recipient_email, sites in email_to_sites.items():
            if sites:  # Only send if owner has at least one site
                print(f"Sending daily status email to {recipient_email} ({len(sites)} site(s))")
                if self.email_service.send_daily_status_email(recipient_email, sites):
                    total_sent += 1
                    print(f"  ✓ Email sent successfully")
                else:
                    print(f"  ✗ Failed to send email")
        
        print(f"[{datetime.now()}] Daily status email check completed. Sent {total_sent} email(s).")
    
    def run(self):
        """Run the weather alert system with scheduled tasks."""
        print("Weather Alert System started")
        print(f"Current time: {datetime.now()}")
        
        # Schedule weather check every 3 hours
        schedule.every(3).hours.do(self.process_weather_check)
        
        # Schedule daily status emails at 8:00 AM
        from config import ALERT_HOUR
        schedule.every().day.at(f"{ALERT_HOUR:02d}:00").do(self.send_daily_status_emails)
        
        # Run immediately on startup
        self.process_weather_check()
        # Don't send emails on startup, only at scheduled time
        
        # Main loop
        print("\nSystem running. Press Ctrl+C to stop.")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            print("\nShutting down...")


if __name__ == "__main__":
    try:
        system = WeatherAlertSystem()
        system.run()
    except Exception as e:
        print(f"Error starting system: {e}")
        raise

