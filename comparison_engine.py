"""Comparison engine to evaluate weather alerts against actual weather data."""
from typing import List, Optional, Dict
from datetime import datetime
from models import WeatherAlert, WeatherResult, Database


class ComparisonEngine:
    """Compares weather alerts against actual weather data."""
    
    def __init__(self, db: Database):
        """Initialize the comparison engine.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def evaluate_condition(self, actual_value: float, operator: str, threshold: float) -> bool:
        """Evaluate a single condition.
        
        Args:
            actual_value: Actual weather value
            operator: Comparison operator ('>', '<', '>=', '<=', '==')
            threshold: Threshold value to compare against
            
        Returns:
            True if condition is met, False otherwise
        """
        if operator == ">":
            return actual_value > threshold
        elif operator == "<":
            return actual_value < threshold
        elif operator == ">=":
            return actual_value >= threshold
        elif operator == "<=":
            return actual_value <= threshold
        elif operator == "==":
            return abs(actual_value - threshold) < 0.01  # Small tolerance for float comparison
        else:
            print(f"Unknown operator: {operator}")
            return False
    
    def compare_weather_data(self, building_code: str, weather_data: List[Dict]) -> List[WeatherResult]:
        """Compare weather alerts against weather data for a location.
        
        Args:
            building_code: Building code for the location
            weather_data: List of weather data dictionaries with timestamp, windspeed, precipitation
            
        Returns:
            List of WeatherResult objects indicating which alerts were triggered
        """
        alerts = self.db.get_weather_alerts_for_location(building_code)
        results = []
        
        if not alerts:
            # No alerts configured, create default "no-alert" results
            for data_point in weather_data:
                results.append(WeatherResult(
                    building_code=building_code,
                    timestamp=data_point["timestamp"],
                    windspeed_val=data_point["windspeed"],
                    precipitation_val=data_point["precipitation"],
                    intervention_id="no-alert"
                ))
            return results
        
        # Process each weather data point
        for data_point in weather_data:
            triggered_intervention_id = None
            max_priority_intervention = None
            
            # Check all alerts to find which ones are triggered
            triggered_alerts = []
            for alert in alerts:
                if alert.alert_type == "Windspeed":
                    if self.evaluate_condition(data_point["windspeed"], alert.operator, alert.value):
                        triggered_alerts.append(alert)
                elif alert.alert_type == "Precipitation":
                    if self.evaluate_condition(data_point["precipitation"], alert.operator, alert.value):
                        triggered_alerts.append(alert)
            
            # Determine which intervention to use
            # Priority: If multiple alerts trigger, use the first non-"no-alert" one
            # If all are "no-alert", use "no-alert"
            if triggered_alerts:
                for alert in triggered_alerts:
                    if alert.intervention_id != "no-alert":
                        max_priority_intervention = alert.intervention_id
                        break
                
                if max_priority_intervention is None:
                    max_priority_intervention = "no-alert"
            else:
                max_priority_intervention = "no-alert"
            
            # Create result
            result = WeatherResult(
                building_code=building_code,
                timestamp=data_point["timestamp"],
                windspeed_val=data_point["windspeed"],
                precipitation_val=data_point["precipitation"],
                intervention_id=max_priority_intervention
            )
            results.append(result)
        
        return results

