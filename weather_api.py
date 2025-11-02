"""OpenWeatherMap API integration for fetching weather data."""
import requests
from typing import Dict, List, Optional
from datetime import datetime


class WeatherAPI:
    """Handles weather data fetching from OpenWeatherMap."""
    
    def __init__(self, api_key: str, units: str = "metric"):
        """Initialize the weather API client.
        
        Args:
            api_key: OpenWeatherMap API key
            units: Unit system ('metric', 'imperial', or 'kelvin')
        """
        self.api_key = api_key
        self.units = units
        self.base_url = "https://api.openweathermap.org/data/2.5"
    
    def get_weather_forecast(self, latitude: float, longitude: float) -> Optional[Dict]:
        """Fetch 3-day weather forecast for given coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            Dictionary containing weather data including windspeed and precipitation
            for the next 3 days, or None if API call fails
        """
        try:
            url = f"{self.base_url}/forecast"
            params = {
                "lat": latitude,
                "lon": longitude,
                "appid": self.api_key,
                "units": self.units,
                "cnt": 24  # Get 24 forecasts (approximately 3 days, 3-hour intervals)
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            return response.json()
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching weather data: {e}")
            return None
    
    def extract_weather_data(self, weather_response: Dict) -> List[Dict]:
        """Extract and clean weather data from API response.
        
        Args:
            weather_response: Raw API response dictionary
            
        Returns:
            List of dictionaries with cleaned weather data containing:
            - timestamp: datetime object
            - windspeed: float (m/s)
            - precipitation: float (mm)
        """
        if not weather_response or "list" not in weather_response:
            return []
        
        cleaned_data = []
        
        for forecast in weather_response.get("list", []):
            timestamp_str = forecast.get("dt_txt")
            if not timestamp_str:
                continue
            
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            
            # Extract wind speed (m/s in metric units)
            wind_data = forecast.get("wind", {})
            windspeed = wind_data.get("speed", 0.0)
            
            # Extract precipitation (rain and snow)
            rain = forecast.get("rain", {}).get("3h", 0.0)
            snow = forecast.get("snow", {}).get("3h", 0.0)
            precipitation = rain + snow
            
            cleaned_data.append({
                "timestamp": timestamp,
                "windspeed": float(windspeed),
                "precipitation": float(precipitation)
            })
        
        return cleaned_data
    
    def get_weather_for_location(self, latitude: float, longitude: float) -> List[Dict]:
        """Get cleaned weather data for a location.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            
        Returns:
            List of cleaned weather data dictionaries
        """
        raw_data = self.get_weather_forecast(latitude, longitude)
        if raw_data:
            return self.extract_weather_data(raw_data)
        return []

