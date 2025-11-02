# Weather Alert System

A Python-based weather monitoring and alerting system that tracks weather conditions for multiple locations and sends email alerts when specific thresholds are exceeded.

## Features

- **Multi-location support**: Track weather for multiple buildings/locations
- **Customizable alerts**: Set thresholds for windspeed and precipitation
- **Automatic monitoring**: Runs weather checks every 3 hours
- **Email notifications**: Sends alerts via email at 9am when conditions are met
- **OpenWeatherMap integration**: Uses OpenWeatherMap API for accurate weather data
- **CSV storage**: Stores all locations, alerts, and results in CSV files

## Data Storage Schema

### Location DB
- Building Code (ID)
- Owner email List []
- Longitude
- Latitude

### Weather Alerts DB
- Building Code (ID)
- Type (Windspeed, Precipitation)
- Value (threshold)
- Operator (>, <, >=, <=, ==)
- Intervention ID

### Intervention DB
- ID
- Title
- Description

### Result DB
- Building Code
- Time-stamp
- Windspeed Val
- Precipitation Val
- Intervention ID

## Installation

1. **Clone or download this repository**

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables:**
   - Copy `.env.example` to `.env`
   - Fill in your OpenWeatherMap API key
   - Optionally configure email settings

4. **Get an OpenWeatherMap API key:**
   - Sign up at [openweathermap.org](https://openweathermap.org/api)
   - Get your free API key from the dashboard
   - Add it to your `.env` file

## Configuration

Create a `.env` file with the following variables:

```env
# Required
OPENWEATHER_API_KEY=your_api_key_here
WEATHER_UNITS=metric

# Optional - Email configuration
# Option 1: Use Resend (Recommended - easier setup)
USE_RESEND=true
RESEND_API_KEY=your_resend_api_key_here
SENDER_EMAIL=your_verified_resend_email@example.com

# Option 2: Use SMTP
# USE_RESEND=false
# SMTP_HOST=smtp.gmail.com
# SMTP_PORT=587
# SENDER_EMAIL=your_email@gmail.com
# SENDER_PASSWORD=your_password_or_app_password
# SMTP_USE_TLS=true

# Optional - Timing configuration
ALERT_HOUR=9
ALERT_START_HOUR=6
ALERT_END_HOUR=11
WEATHER_CHECK_INTERVAL_HOURS=3
```

### Email Setup Notes

**Using Resend (Recommended):**
1. Sign up for a free account at [resend.com](https://resend.com)
2. Get your API key from the dashboard
3. Verify your sending domain or use the default test domain for development
4. Set `USE_RESEND=true` in your `.env` file
5. Add your `RESEND_API_KEY` and verified `SENDER_EMAIL`

**Using SMTP:**
- For Gmail, you may need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password
- For other email providers, check their SMTP settings
- Set `USE_RESEND=false` in your `.env` file (or omit it)

## Usage

### 1. Set up sample data (optional)

```bash
python setup_database.py
```

This creates a sample location and alerts for testing.

### 2. Run the system

```bash
python main.py
```

The system will:
- Start immediately with a weather check
- Run weather checks every 3 hours
- Check for alerts every hour (sends emails between 6am and 11am)

### 3. Managing Data

You can create a custom script to add locations and alerts using the `Database` class from `models.py`.

Example:
```python
from models import Database, Location, WeatherAlert, Intervention

db = Database()

# Add a location
location = Location(
    building_code="BLD001",
    owner_emails=["owner@example.com"],
    longitude=-73.5673,
    latitude=45.5017
)
db.add_location(location)

# Add an intervention
intervention = Intervention(
    id="high_wind_alert",
    title="High Wind Warning",
    description="High wind speeds detected."
)
db.add_intervention(intervention)

# Add a weather alert
alert = WeatherAlert(
    building_code="BLD001",
    alert_type="Windspeed",
    value=15.0,
    operator=">",
    intervention_id="high_wind_alert"
)
db.add_weather_alert(alert)
```

## Logic Flow

1. **Timer**: Runs every 3 hours
2. **API Call**: For each location, fetches weather data from OpenWeatherMap
3. **Data Cleaning**: Extracts windspeed and precipitation for 3 days
4. **Save Data**: Stores raw weather data
5. **Comparison Engine**: Compares alert thresholds against weather data
6. **Store Results**: Saves comparison results to database
7. **Send Alerts**: If intervention ID is not "no-alert" and current time is 9am, sends emails

## Project Structure

```
.
├── main.py              # Main application entry point
├── models.py            # Database models and schema
├── weather_api.py       # OpenWeatherMap API integration
├── comparison_engine.py # Weather alert comparison logic
├── email_service.py     # Email notification service
├── config.py            # Configuration management
├── setup_database.py     # Sample data setup script
├── requirements.txt     # Python dependencies
├── README.md           # This file
└── .env                # Environment variables (create this)
```

## Notes

- The system runs continuously until stopped (Ctrl+C)
- Weather data is fetched for 3-day forecasts (24 data points, 3-hour intervals)
- Alerts are only sent between 6am and 11am, even if conditions are met at other times
- CSV files in the `data/` directory will be created automatically
- All times are in local server time
- Supports both Resend API and traditional SMTP for email sending

## Troubleshooting

- **API errors**: Verify your OpenWeatherMap API key is correct and active
- **Email not sending**: Check SMTP settings and credentials
- **No locations found**: Run `setup_database.py` or add locations manually
- **CSV file errors**: Ensure you have write permissions in the `data/` directory

## License

This project is provided as-is for educational and development purposes.

