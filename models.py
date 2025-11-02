"""Database models for the weather alert system."""
import csv
import os
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Location:
    """Represents a location with building code and coordinates."""
    building_code: str
    owner_emails: List[str]
    longitude: float
    latitude: float


@dataclass
class WeatherAlert:
    """Represents a weather alert rule."""
    building_code: str
    alert_type: str  # 'Windspeed' or 'Precipitation'
    value: float
    operator: str  # '>', '<', '>=', '<=', '=='
    intervention_id: str


@dataclass
class Intervention:
    """Represents an intervention/alert message."""
    id: str
    title: str
    description: str


@dataclass
class WeatherResult:
    """Represents a weather check result."""
    building_code: str
    timestamp: datetime
    windspeed_val: float
    precipitation_val: float
    intervention_id: str


class Database:
    """Database manager for the weather alert system using CSV files."""
    
    def __init__(self, data_dir: str = "data"):
        """Initialize the CSV database connection and create CSV files if needed."""
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        self.locations_file = os.path.join(data_dir, "locations.csv")
        self.weather_alerts_file = os.path.join(data_dir, "weather_alerts.csv")
        self.interventions_file = os.path.join(data_dir, "interventions.csv")
        self.results_file = os.path.join(data_dir, "results.csv")
        
        self._initialize_csv_files()
    
    def _initialize_csv_files(self):
        """Create CSV files with headers if they don't exist."""
        files_and_headers = [
            (self.locations_file, ["building_code", "owner_emails", "longitude", "latitude"]),
            (self.weather_alerts_file, ["building_code", "alert_type", "value", "operator", "intervention_id"]),
            (self.interventions_file, ["id", "title", "description"]),
            (self.results_file, ["building_code", "timestamp", "windspeed_val", "precipitation_val", "intervention_id"])
        ]
        
        for file_path, headers in files_and_headers:
            if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                with open(file_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()
    
    def add_location(self, location: Location):
        """Add or update a location in the CSV file."""
        # Read existing locations
        locations = self.get_all_locations()
        
        # Remove existing location with same building_code if it exists
        locations = [loc for loc in locations if loc.building_code != location.building_code]
        locations.append(location)
        
        # Write all locations back
        with open(self.locations_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["building_code", "owner_emails", "longitude", "latitude"])
            writer.writeheader()
            for loc in locations:
                writer.writerow({
                    "building_code": loc.building_code,
                    "owner_emails": ','.join(loc.owner_emails) if loc.owner_emails else "",
                    "longitude": loc.longitude,
                    "latitude": loc.latitude
                })
    
    def get_all_locations(self) -> List[Location]:
        """Get all locations from the CSV file."""
        locations = []
        if not os.path.exists(self.locations_file):
            return locations
        
        with open(self.locations_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if not row.get('building_code'):
                    continue
                emails = row['owner_emails'].split(',') if row.get('owner_emails') else []
                emails = [e.strip() for e in emails if e.strip()]
                locations.append(Location(
                    building_code=row['building_code'],
                    owner_emails=emails,
                    longitude=float(row['longitude']),
                    latitude=float(row['latitude'])
                ))
        return locations
    
    def add_weather_alert(self, alert: WeatherAlert):
        """Add a weather alert rule to the CSV file."""
        with open(self.weather_alerts_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["building_code", "alert_type", "value", "operator", "intervention_id"])
            writer.writerow({
                "building_code": alert.building_code,
                "alert_type": alert.alert_type,
                "value": alert.value,
                "operator": alert.operator,
                "intervention_id": alert.intervention_id
            })
    
    def get_weather_alerts_for_location(self, building_code: str) -> List[WeatherAlert]:
        """Get all weather alerts for a specific location."""
        alerts = []
        if not os.path.exists(self.weather_alerts_file):
            return alerts
        
        with open(self.weather_alerts_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('building_code') == building_code:
                    alerts.append(WeatherAlert(
                        building_code=row['building_code'],
                        alert_type=row['alert_type'],
                        value=float(row['value']),
                        operator=row['operator'],
                        intervention_id=row['intervention_id']
                    ))
        return alerts
    
    def add_intervention(self, intervention: Intervention):
        """Add or update an intervention in the CSV file."""
        # Read existing interventions
        interventions = []
        if os.path.exists(self.interventions_file):
            with open(self.interventions_file, 'r', newline='', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if row.get('id') != intervention.id:
                        interventions.append(Intervention(
                            id=row['id'],
                            title=row['title'],
                            description=row['description']
                        ))
        
        interventions.append(intervention)
        
        # Write all interventions back
        with open(self.interventions_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["id", "title", "description"])
            writer.writeheader()
            for interv in interventions:
                writer.writerow({
                    "id": interv.id,
                    "title": interv.title,
                    "description": interv.description
                })
    
    def get_intervention(self, intervention_id: str) -> Optional[Intervention]:
        """Get an intervention by ID."""
        if not os.path.exists(self.interventions_file):
            return None
        
        with open(self.interventions_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('id') == intervention_id:
                    return Intervention(
                        id=row['id'],
                        title=row['title'],
                        description=row['description']
                    )
        return None
    
    def save_result(self, result: WeatherResult):
        """Save a weather check result to the CSV file."""
        with open(self.results_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["building_code", "timestamp", "windspeed_val", "precipitation_val", "intervention_id"])
            writer.writerow({
                "building_code": result.building_code,
                "timestamp": result.timestamp.isoformat() if isinstance(result.timestamp, datetime) else result.timestamp,
                "windspeed_val": result.windspeed_val,
                "precipitation_val": result.precipitation_val,
                "intervention_id": result.intervention_id
            })
    
    def get_location_emails(self, building_code: str) -> List[str]:
        """Get owner emails for a location."""
        locations = self.get_all_locations()
        for location in locations:
            if location.building_code == building_code:
                return location.owner_emails
        return []
    
    def get_latest_result(self, building_code: str) -> Optional[dict]:
        """Get the most recent result for a location.
        
        Returns:
            Dictionary with result data or None if no results found
        """
        if not os.path.exists(self.results_file):
            return None
        
        latest_result = None
        latest_timestamp = None
        
        with open(self.results_file, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('building_code') == building_code:
                    timestamp_str = row['timestamp']
                    # Parse timestamp to compare
                    try:
                        timestamp = datetime.fromisoformat(timestamp_str)
                        if latest_timestamp is None or timestamp > latest_timestamp:
                            latest_timestamp = timestamp
                            latest_result = {
                                'building_code': row['building_code'],
                                'timestamp': row['timestamp'],
                                'windspeed_val': float(row['windspeed_val']),
                                'precipitation_val': float(row['precipitation_val']),
                                'intervention_id': row['intervention_id']
                            }
                    except (ValueError, TypeError):
                        # If timestamp parsing fails, keep the last one found
                        if latest_result is None:
                            latest_result = {
                                'building_code': row['building_code'],
                                'timestamp': row['timestamp'],
                                'windspeed_val': float(row['windspeed_val']),
                                'precipitation_val': float(row['precipitation_val']),
                                'intervention_id': row['intervention_id']
                            }
        
        return latest_result

