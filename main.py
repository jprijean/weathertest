"""Main application entry point for the weather alert system."""
import schedule
import time
import os
from datetime import datetime
from dotenv import load_dotenv

from models import Database
from weather_api import WeatherAPI
from comparison_engine import ComparisonEngine
from email_service import EmailService


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
        
        print(f"[{datetime.now()}] Weather check completed")
    
    def send_scheduled_alerts(self):
        """Send email alerts if within the alert time window and there are active alerts."""
        from config import ALERT_START_HOUR, ALERT_END_HOUR
        current_hour = datetime.now().hour
        
        if not (ALERT_START_HOUR <= current_hour < ALERT_END_HOUR):
            print(f"Current time is {datetime.now().strftime('%H:%M')}, not within alert window ({ALERT_START_HOUR}:00-{ALERT_END_HOUR}:00). Skipping alerts.")
            return
        
        if not self.email_service:
            print("Email service not configured. Skipping alerts.")
            return
        
        print(f"\n[{datetime.now()}] Starting scheduled alert check...")
        
        # Get all locations
        locations = self.db.get_all_locations()
        
        for location in locations:
            # Get the most recent result for this location
            result = self.db.get_latest_result(location.building_code)
            
            if result and result['intervention_id'] != 'no-alert':
                intervention_id = result['intervention_id']
                print(f"Sending alerts for {location.building_code} (Intervention: {intervention_id})")
                sent = self.email_service.send_alerts_for_location(
                    self.db, 
                    location.building_code, 
                    intervention_id
                )
                print(f"  Sent {sent} email(s)")
        
        print(f"[{datetime.now()}] Scheduled alert check completed")
    
    def run(self):
        """Run the weather alert system with scheduled tasks."""
        print("Weather Alert System started")
        print(f"Current time: {datetime.now()}")
        
        # Schedule weather check every 3 hours
        schedule.every(3).hours.do(self.process_weather_check)
        
        # Schedule alert sending check every hour (will only send at 9am)
        schedule.every().hour.do(self.send_scheduled_alerts)
        
        # Run immediately on startup
        self.process_weather_check()
        self.send_scheduled_alerts()
        
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

