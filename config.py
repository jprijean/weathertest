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
ALERT_HOUR = int(os.getenv("ALERT_HOUR", "8"))  # Hour of day to send daily status emails (24-hour format, default 8:00 AM)
WEATHER_CHECK_INTERVAL_HOURS = int(os.getenv("WEATHER_CHECK_INTERVAL_HOURS", "3"))

