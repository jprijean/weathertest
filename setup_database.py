"""Utility script to set up sample data in the database."""
from models import Database, Location, WeatherAlert, Intervention


def setup_sample_data():
    """Create sample data for testing."""
    db = Database()
    
    # Create sample intervention
    intervention = Intervention(
        id="high_wind_alert",
        title="High Wind Warning",
        description="High wind speeds detected. Please secure outdoor items and stay indoors."
    )
    db.add_intervention(intervention)
    
    intervention2 = Intervention(
        id="heavy_rain_alert",
        title="Heavy Precipitation Warning",
        description="Heavy rainfall expected. Please take necessary precautions."
    )
    db.add_intervention(intervention2)
    
    # Create sample location (Montreal, Canada)
    location = Location(
        building_code="BLD001",
        owner_emails=["owner1@example.com", "owner2@example.com"],
        longitude=-73.5673,
        latitude=45.5017
    )
    db.add_location(location)
    
    # Create weather alerts
    alert1 = WeatherAlert(
        building_code="BLD001",
        alert_type="Windspeed",
        value=15.0,
        operator=">",
        intervention_id="high_wind_alert"
    )
    db.add_weather_alert(alert1)
    
    alert2 = WeatherAlert(
        building_code="BLD001",
        alert_type="Precipitation",
        value=10.0,
        operator=">",
        intervention_id="heavy_rain_alert"
    )
    db.add_weather_alert(alert2)
    
    print("Sample data created successfully!")
    print("\nSample Location:")
    print(f"  Building Code: BLD001")
    print(f"  Coordinates: 45.5017, -73.5673 (Montreal)")
    print(f"  Owner Emails: owner1@example.com, owner2@example.com")
    print("\nSample Alerts:")
    print(f"  - Windspeed > 15.0 m/s -> high_wind_alert")
    print(f"  - Precipitation > 10.0 mm -> heavy_rain_alert")


if __name__ == "__main__":
    setup_sample_data()

