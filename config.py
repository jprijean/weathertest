"""Configuration utilities for the weather alert system."""
import os
from dotenv import load_dotenv

load_dotenv()

# OpenWeatherMap API configuration
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHER_UNITS = os.getenv("WEATHER_UNITS", "metric")  # metric, imperial, or kelvin

# Email configuration (optional)
USE_RESEND = os.getenv("USE_RESEND", "false").lower() == "true"  # Use Resend API instead of SMTP
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")

SMTP_HOST = os.getenv("SMTP_HOST", "")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SENDER_EMAIL = os.getenv("SENDER_EMAIL", "")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD", "")
SMTP_USE_TLS = os.getenv("SMTP_USE_TLS", "true").lower() == "true"

# Alert timing
ALERT_HOUR = int(os.getenv("ALERT_HOUR", "9"))  # Hour of day to send alerts (24-hour format)
ALERT_START_HOUR = int(os.getenv("ALERT_START_HOUR", "6"))  # Start of alert sending window
ALERT_END_HOUR = int(os.getenv("ALERT_END_HOUR", "11"))  # End of alert sending window
WEATHER_CHECK_INTERVAL_HOURS = int(os.getenv("WEATHER_CHECK_INTERVAL_HOURS", "3"))

