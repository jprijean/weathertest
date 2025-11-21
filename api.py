"""
FastAPI backend server for Weather Alerts Dashboard.

This module provides a REST API that reads CSV files from the data directory
and serves them as JSON endpoints. The API is designed to be consumed by
the React frontend dashboard.

Endpoints:
    GET /              - API information and available endpoints
    GET /locations     - Building locations data
    POST /locations    - Add a new location
    PUT /locations/{building_code} - Update a location
    DELETE /locations/{building_code} - Delete a location
    GET /results       - Weather check results
    GET /interventions - Intervention definitions
    GET /interventions/{intervention_id} - Get a single intervention
    POST /interventions - Add a new intervention
    PUT /interventions/{intervention_id} - Update an intervention
    DELETE /interventions/{intervention_id} - Delete an intervention
    GET /weather-alerts - Get all weather alert rules
    GET /weather-alerts/{alert_id} - Get a single weather alert
    POST /weather-alerts - Create a new weather alert
    PUT /weather-alerts/{alert_id} - Update a weather alert
    DELETE /weather-alerts/{alert_id} - Delete a weather alert
    GET /dashboard     - Merged dashboard data (all sources combined)

CORS is enabled to allow cross-origin requests from the frontend.
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import csv
from typing import List, Dict, Any, Optional
from pathlib import Path

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================

# API metadata
API_TITLE: str = "Weather Alerts API"
API_VERSION: str = "1.0.0"

# Data directory (relative to this file)
DATA_DIR: Path = Path("data")

# CSV filenames
CSV_LOCATIONS: str = "locations.csv"
CSV_RESULTS: str = "results.csv"
CSV_INTERVENTIONS: str = "interventions.csv"
CSV_WEATHER_ALERTS: str = "weather_alerts.csv"

# HTTP status codes
HTTP_NOT_FOUND: int = 404
HTTP_INTERNAL_ERROR: int = 500
HTTP_BAD_REQUEST: int = 400

# ============================================================================
# PYDANTIC MODELS FOR REQUEST VALIDATION
# ============================================================================

class LocationCreate(BaseModel):
    """Model for creating a new location."""
    building_code: str
    owner_emails: str  # Comma-separated email addresses
    longitude: float
    latitude: float

class LocationUpdate(BaseModel):
    """Model for updating an existing location."""
    owner_emails: Optional[str] = None
    longitude: Optional[float] = None
    latitude: Optional[float] = None

class InterventionCreate(BaseModel):
    """Model for creating a new intervention."""
    id: str
    title: str
    description: str

class InterventionUpdate(BaseModel):
    """Model for updating an existing intervention."""
    title: Optional[str] = None
    description: Optional[str] = None

class WeatherAlertCreate(BaseModel):
    """Model for creating a new weather alert (global, applies to all buildings)."""
    alert_type: str  # 'Windspeed' or 'Precipitation'
    value: float
    operator: str  # '>', '<', '>=', '<=', '=='
    intervention_id: str

class WeatherAlertUpdate(BaseModel):
    """Model for updating an existing weather alert."""
    value: Optional[float] = None
    operator: Optional[str] = None
    intervention_id: Optional[str] = None

# ============================================================================
# FASTAPI APPLICATION SETUP
# ============================================================================

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description="REST API for Weather Alerts Dashboard data"
)

# ============================================================================
# CORS MIDDLEWARE CONFIGURATION
# ============================================================================
# CORS (Cross-Origin Resource Sharing) allows the frontend (port 3000)
# to make requests to this API (port 8000) from the browser.
# 
# In production, you should restrict allow_origins to specific domains
# instead of using "*" for security.
# ============================================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (development only)
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def read_csv_file(filename: str) -> List[Dict[str, str]]:
    """
    Read a CSV file and convert it to a list of dictionaries.

    Each row in the CSV becomes a dictionary where:
    - Keys are column names from the header row
    - Values are the cell values as strings
    
    Args:
        filename: Name of the CSV file in the data directory
        
    Returns:
        List of dictionaries, one per row in the CSV file
        
    Raises:
        HTTPException: 
            - 404 if the file doesn't exist
            - 500 if there's an error reading the file
            
    Example:
        CSV file (locations.csv):
            building_code,longitude,latitude
            BLD001,-4.4861,48.3904
            BLD002,-4.4890,48.3950
        
        Returns:
            [
                {"building_code": "BLD001", "longitude": "-4.4861", "latitude": "48.3904"},
                {"building_code": "BLD002", "longitude": "-4.4890", "latitude": "48.3950"}
            ]
    """
    filepath: Path = DATA_DIR / filename
    
    # Validate file exists
    if not filepath.exists():
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"File {filename} not found in data directory"
        )
    
    # Read and parse CSV file
    try:
        with open(filepath, 'r', encoding='utf-8', newline='') as file:
            reader = csv.DictReader(file)
            # Convert None values to empty strings for JSON serialization
            return [
                {key: (value if value is not None else '') for key, value in row.items()}
                for row in reader
            ]
    except csv.Error as e:
        raise HTTPException(
            status_code=HTTP_INTERNAL_ERROR,
            detail=f"Error parsing CSV file {filename}: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=HTTP_INTERNAL_ERROR,
            detail=f"Error reading CSV file {filename}: {str(e)}"
        )
    except IOError as e:
        raise HTTPException(
            status_code=HTTP_INTERNAL_ERROR,
            detail=f"Error reading file {filename}: {str(e)}"
        )


def write_csv_file(filename: str, data: List[Dict[str, str]], fieldnames: List[str]) -> None:
    """
    Write data to a CSV file.
    
    Args:
        filename: Name of the CSV file in the data directory
        data: List of dictionaries to write
        fieldnames: List of column names (CSV headers)
        
    Raises:
        HTTPException: If there's an error writing the file
    """
    filepath: Path = DATA_DIR / filename
    
    # Ensure data directory exists
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    except IOError as e:
        raise HTTPException(
            status_code=HTTP_INTERNAL_ERROR,
            detail=f"Error writing file {filename}: {str(e)}"
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/")
def get_api_info() -> Dict[str, Any]:
    """
    Root endpoint - returns API information.
    
    Returns:
        Dictionary containing API metadata and available endpoints
    """
    return {
        "name": API_TITLE,
        "version": API_VERSION,
        "endpoints": ["/locations", "/results", "/interventions", "/weather-alerts", "/dashboard"]
    }


@app.get("/locations")
def get_locations() -> List[Dict[str, str]]:
    """
    Get all building locations.
    
    Reads from locations.csv and returns all location records.
    
    Returns:
        List of location dictionaries with keys:
        - building_code: Unique building identifier
        - owner_emails: Comma-separated email addresses
        - longitude: Longitude coordinate
        - latitude: Latitude coordinate
    """
    return read_csv_file(CSV_LOCATIONS)


@app.post("/locations")
def create_location(location: LocationCreate) -> Dict[str, Any]:
    """
    Create a new location.
    
    Args:
        location: Location data (building_code, owner_emails, longitude, latitude)
        
    Returns:
        Success message and the created location
        
    Raises:
        HTTPException: 400 if building_code already exists
    """
    # Read existing locations
    locations = read_csv_file(CSV_LOCATIONS)
    
    # Check if building_code already exists
    if any(loc["building_code"] == location.building_code for loc in locations):
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"Location with building_code '{location.building_code}' already exists"
        )
    
    # Add new location
    new_location = {
        "building_code": location.building_code,
        "owner_emails": location.owner_emails,
        "longitude": str(location.longitude),
        "latitude": str(location.latitude)
    }
    locations.append(new_location)
    
    # Write back to CSV
    write_csv_file(CSV_LOCATIONS, locations, ["building_code", "owner_emails", "longitude", "latitude"])
    
    return {
        "message": "Location created successfully",
        "location": new_location
    }


@app.put("/locations/{building_code}")
def update_location(building_code: str, location_update: LocationUpdate) -> Dict[str, Any]:
    """
    Update an existing location.
    
    Args:
        building_code: Building code to update
        location_update: Fields to update (owner_emails, longitude, latitude)
        
    Returns:
        Success message and updated location
        
    Raises:
        HTTPException: 404 if building_code not found
    """
    # Read existing locations
    locations = read_csv_file(CSV_LOCATIONS)
    
    # Find the location to update
    location_index = None
    for i, loc in enumerate(locations):
        if loc["building_code"] == building_code:
            location_index = i
            break
    
    if location_index is None:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Location with building_code '{building_code}' not found"
        )
    
    # Update fields
    if location_update.owner_emails is not None:
        locations[location_index]["owner_emails"] = location_update.owner_emails
    if location_update.longitude is not None:
        locations[location_index]["longitude"] = str(location_update.longitude)
    if location_update.latitude is not None:
        locations[location_index]["latitude"] = str(location_update.latitude)
    
    # Write back to CSV
    write_csv_file(CSV_LOCATIONS, locations, ["building_code", "owner_emails", "longitude", "latitude"])
    
    return {
        "message": "Location updated successfully",
        "location": locations[location_index]
    }


@app.delete("/locations/{building_code}")
def delete_location(building_code: str) -> Dict[str, str]:
    """
    Delete a location and all related results.
    
    When a location is deleted, all weather results for that building are also removed
    to keep the dashboard clean and prevent orphaned data.
    
    Args:
        building_code: Building code to delete
        
    Returns:
        Success message with count of deleted results
        
    Raises:
        HTTPException: 404 if building_code not found
    """
    # Read existing locations
    locations = read_csv_file(CSV_LOCATIONS)
    
    # Find and remove the location
    original_count = len(locations)
    locations = [loc for loc in locations if loc["building_code"] != building_code]
    
    if len(locations) == original_count:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Location with building_code '{building_code}' not found"
        )
    
    # Write back to CSV
    write_csv_file(CSV_LOCATIONS, locations, ["building_code", "owner_emails", "longitude", "latitude"])
    
    # Also delete all results for this building
    results_deleted = 0
    filepath: Path = DATA_DIR / CSV_RESULTS
    if filepath.exists():
        try:
            results = read_csv_file(CSV_RESULTS)
            original_results_count = len(results)
            results = [r for r in results if r.get("building_code") != building_code]
            results_deleted = original_results_count - len(results)
            
            if results_deleted > 0 or original_results_count > 0:
                # Get fieldnames from the first row or use defaults
                if results:
                    fieldnames = list(results[0].keys())
                else:
                    # If no results left, read the file to get headers
                    import csv as csv_module
                    with open(filepath, 'r', encoding='utf-8', newline='') as f:
                        reader = csv_module.DictReader(f)
                        fieldnames = reader.fieldnames or ["building_code", "timestamp", "windspeed_val", "precipitation_val", "intervention_id", "severity"]
                
                # Write back results without the deleted building's data
                write_csv_file(CSV_RESULTS, results, fieldnames)
        except Exception as e:
            # Log error but don't fail the location deletion
            print(f"Warning: Could not delete results for {building_code}: {e}")
    
    message = f"Location '{building_code}' deleted successfully"
    if results_deleted > 0:
        message += f" ({results_deleted} result(s) also removed)"
    
    return {"message": message}


@app.get("/results")
def get_results() -> List[Dict[str, str]]:
    """
    Get all weather check results.
    
    Reads from results.csv and returns all result records.
    
    Returns:
        List of result dictionaries with keys:
        - building_code: Building identifier
        - timestamp: When the check was performed (ISO format)
        - windspeed_val: Wind speed value
        - precipitation_val: Precipitation amount
        - intervention_id: ID of triggered intervention or "no-alert"
        - severity: Severity level of the alert
    """
    return read_csv_file(CSV_RESULTS)


@app.get("/interventions")
def get_interventions() -> List[Dict[str, str]]:
    """
    Get all intervention definitions.
    
    Reads from interventions.csv and returns all intervention records.
    
    Returns:
        List of intervention dictionaries with keys:
        - id: Unique intervention identifier
        - title: Short title of the intervention
        - description: Detailed description of the intervention
    """
    return read_csv_file(CSV_INTERVENTIONS)


@app.get("/interventions/{intervention_id}")
def get_intervention_by_id(intervention_id: str) -> Dict[str, str]:
    """
    Get a single intervention by its ID.
    
    Args:
        intervention_id: The intervention identifier
        
    Returns:
        Intervention dictionary with id, title, and description
        
    Raises:
        HTTPException: 404 if intervention_id not found
    """
    interventions = read_csv_file(CSV_INTERVENTIONS)
    
    for intervention in interventions:
        if intervention["id"] == intervention_id:
            return intervention
    
    raise HTTPException(
        status_code=HTTP_NOT_FOUND,
        detail=f"Intervention with id '{intervention_id}' not found"
    )


@app.post("/interventions")
def create_intervention(intervention: InterventionCreate) -> Dict[str, Any]:
    """
    Create a new intervention.
    
    Args:
        intervention: Intervention data (id, title, description)
        
    Returns:
        Success message and the created intervention
        
    Raises:
        HTTPException: 400 if intervention id already exists
    """
    # Read existing interventions
    interventions = read_csv_file(CSV_INTERVENTIONS)
    
    # Check if intervention id already exists
    if any(interv["id"] == intervention.id for interv in interventions):
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"Intervention with id '{intervention.id}' already exists"
        )
    
    # Add new intervention
    new_intervention = {
        "id": intervention.id,
        "title": intervention.title,
        "description": intervention.description
    }
    interventions.append(new_intervention)
    
    # Write back to CSV
    write_csv_file(CSV_INTERVENTIONS, interventions, ["id", "title", "description"])
    
    return {
        "message": "Intervention created successfully",
        "intervention": new_intervention
    }


@app.put("/interventions/{intervention_id}")
def update_intervention(intervention_id: str, intervention_update: InterventionUpdate) -> Dict[str, Any]:
    """
    Update an existing intervention.
    
    Args:
        intervention_id: Intervention ID to update
        intervention_update: Fields to update (title, description)
        
    Returns:
        Success message and updated intervention
        
    Raises:
        HTTPException: 404 if intervention_id not found
    """
    # Read existing interventions
    interventions = read_csv_file(CSV_INTERVENTIONS)
    
    # Find the intervention to update
    intervention_index = None
    for i, interv in enumerate(interventions):
        if interv["id"] == intervention_id:
            intervention_index = i
            break
    
    if intervention_index is None:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Intervention with id '{intervention_id}' not found"
        )
    
    # Update fields
    if intervention_update.title is not None:
        interventions[intervention_index]["title"] = intervention_update.title
    if intervention_update.description is not None:
        interventions[intervention_index]["description"] = intervention_update.description
    
    # Write back to CSV
    write_csv_file(CSV_INTERVENTIONS, interventions, ["id", "title", "description"])
    
    return {
        "message": "Intervention updated successfully",
        "intervention": interventions[intervention_index]
    }


@app.delete("/interventions/{intervention_id}")
def delete_intervention(intervention_id: str) -> Dict[str, str]:
    """
    Delete an intervention.
    
    Args:
        intervention_id: Intervention ID to delete
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if intervention_id not found
    """
    # Read existing interventions
    interventions = read_csv_file(CSV_INTERVENTIONS)
    
    # Find and remove the intervention
    original_count = len(interventions)
    interventions = [interv for interv in interventions if interv["id"] != intervention_id]
    
    if len(interventions) == original_count:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Intervention with id '{intervention_id}' not found"
        )
    
    # Write back to CSV
    write_csv_file(CSV_INTERVENTIONS, interventions, ["id", "title", "description"])
    
    return {"message": f"Intervention '{intervention_id}' deleted successfully"}


# ============================================================================
# API ENDPOINTS FOR WEATHER ALERTS MANAGEMENT
# ============================================================================

@app.get("/weather-alerts")
def get_weather_alerts() -> List[Dict[str, str]]:
    """
    Get all global weather alert rules (applies to all buildings).
    
    Only 2 alerts are supported: Windspeed and Precipitation.
    Reads from weather_alerts.csv and returns all alert records.
    Returns empty list if file doesn't exist yet.
    
    Returns:
        List of weather alert dictionaries with keys:
        - id: Unique identifier (alert_type)
        - alert_type: Type of alert ('Windspeed' or 'Precipitation')
        - value: Threshold value
        - operator: Comparison operator ('>', '<', '>=', '<=', '==')
        - intervention_id: Intervention ID to trigger
    """
    filepath: Path = DATA_DIR / CSV_WEATHER_ALERTS
    
    # Return empty list if file doesn't exist yet
    if not filepath.exists():
        return []
    
    alerts = read_csv_file(CSV_WEATHER_ALERTS)
    # Use alert_type as ID (since we only have 2 global alerts)
    for alert in alerts:
        alert['id'] = alert.get('alert_type', '')
    return alerts


@app.get("/weather-alerts/{alert_id}")
def get_weather_alert_by_id(alert_id: str) -> Dict[str, str]:
    """
    Get a single weather alert by its alert_type (Windspeed or Precipitation).
    
    Args:
        alert_id: The alert type ('Windspeed' or 'Precipitation')
        
    Returns:
        Weather alert dictionary
        
    Raises:
        HTTPException: 404 if alert_id not found
    """
    filepath: Path = DATA_DIR / CSV_WEATHER_ALERTS
    if not filepath.exists():
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Weather alert with id '{alert_id}' not found"
        )
    
    alerts = read_csv_file(CSV_WEATHER_ALERTS)
    
    # Find alert by alert_type
    for alert in alerts:
        if alert.get('alert_type') == alert_id:
            alert_copy = alert.copy()
            alert_copy['id'] = alert_id
            return alert_copy
    
    raise HTTPException(
        status_code=HTTP_NOT_FOUND,
        detail=f"Weather alert with id '{alert_id}' not found"
    )


@app.post("/weather-alerts")
def create_weather_alert(alert: WeatherAlertCreate) -> Dict[str, Any]:
    """
    Create or update a global weather alert rule (applies to all buildings).
    Only 2 alerts are supported: Windspeed and Precipitation.
    
    Args:
        alert: Weather alert data (alert_type, value, operator, intervention_id)
        
    Returns:
        Success message and the created/updated alert
        
    Raises:
        HTTPException: 400 if validation fails
    """
    # Validate alert_type
    if alert.alert_type not in ["Windspeed", "Precipitation"]:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"alert_type must be 'Windspeed' or 'Precipitation', got '{alert.alert_type}'"
        )
    
    # Validate operator
    if alert.operator not in [">", "<", ">=", "<=", "=="]:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"operator must be one of: '>', '<', '>=', '<=', '==', got '{alert.operator}'"
        )
    
    # Validate value
    if alert.value < 0:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail="value must be non-negative"
        )
    
    # Read existing alerts (or empty list if file doesn't exist)
    filepath: Path = DATA_DIR / CSV_WEATHER_ALERTS
    if filepath.exists():
        alerts = read_csv_file(CSV_WEATHER_ALERTS)
    else:
        alerts = []
    
    # Check if alert of this type already exists
    existing_index = None
    for i, existing_alert in enumerate(alerts):
        if existing_alert.get('alert_type') == alert.alert_type:
            existing_index = i
            break
    
    new_alert = {
        "alert_type": alert.alert_type,
        "value": str(alert.value),
        "operator": alert.operator,
        "intervention_id": alert.intervention_id
    }
    
    if existing_index is not None:
        # Update existing alert
        alerts[existing_index] = new_alert
        message = "Weather alert updated successfully"
    else:
        # Add new alert
        alerts.append(new_alert)
        message = "Weather alert created successfully"
    
    # Write back to CSV (no building_code column)
    write_csv_file(CSV_WEATHER_ALERTS, alerts, ["alert_type", "value", "operator", "intervention_id"])
    
    return {
        "message": message,
        "alert": new_alert
    }


@app.put("/weather-alerts/{alert_id}")
def update_weather_alert(alert_id: str, alert_update: WeatherAlertUpdate) -> Dict[str, Any]:
    """
    Update an existing global weather alert by alert_type (Windspeed or Precipitation).
    
    Args:
        alert_id: Alert type to update ('Windspeed' or 'Precipitation')
        alert_update: Fields to update (value, operator, intervention_id)
        
    Returns:
        Success message and updated alert
        
    Raises:
        HTTPException: 404 if alert_id not found, 400 if validation fails
    """
    # Validate alert_id
    if alert_id not in ["Windspeed", "Precipitation"]:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"alert_id must be 'Windspeed' or 'Precipitation', got '{alert_id}'"
        )
    
    # Read existing alerts (or empty list if file doesn't exist)
    filepath: Path = DATA_DIR / CSV_WEATHER_ALERTS
    if filepath.exists():
        alerts = read_csv_file(CSV_WEATHER_ALERTS)
    else:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Weather alert with id '{alert_id}' not found"
        )
    
    # Find the alert to update by alert_type
    alert_index = None
    for i, alert in enumerate(alerts):
        if alert.get('alert_type') == alert_id:
            alert_index = i
            break
    
    if alert_index is None:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Weather alert with id '{alert_id}' not found"
        )
    
    # Validate updates
    if alert_update.operator is not None and alert_update.operator not in [">", "<", ">=", "<=", "=="]:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail=f"operator must be one of: '>', '<', '>=', '<=', '=='"
        )
    
    if alert_update.value is not None and alert_update.value < 0:
        raise HTTPException(
            status_code=HTTP_BAD_REQUEST,
            detail="value must be non-negative"
        )
    
    # Update fields (alert_type cannot be changed)
    if alert_update.value is not None:
        alerts[alert_index]["value"] = str(alert_update.value)
    if alert_update.operator is not None:
        alerts[alert_index]["operator"] = alert_update.operator
    if alert_update.intervention_id is not None:
        alerts[alert_index]["intervention_id"] = alert_update.intervention_id
    
    # Write back to CSV (no building_code column)
    write_csv_file(CSV_WEATHER_ALERTS, alerts, ["alert_type", "value", "operator", "intervention_id"])
    
    updated_alert = alerts[alert_index].copy()
    updated_alert['id'] = alert_id
    
    return {
        "message": "Weather alert updated successfully",
        "alert": updated_alert
    }


@app.delete("/weather-alerts/{alert_id}")
def delete_weather_alert(alert_id: str) -> Dict[str, str]:
    """
    Delete a global weather alert by alert_type (Windspeed or Precipitation).
    
    Args:
        alert_id: Alert type to delete ('Windspeed' or 'Precipitation')
        
    Returns:
        Success message
        
    Raises:
        HTTPException: 404 if alert_id not found
    """
    # Read existing alerts (or empty list if file doesn't exist)
    filepath: Path = DATA_DIR / CSV_WEATHER_ALERTS
    if filepath.exists():
        alerts = read_csv_file(CSV_WEATHER_ALERTS)
    else:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Weather alert with id '{alert_id}' not found"
        )
    
    # Find and remove the alert by alert_type
    alert_index = None
    for i, alert in enumerate(alerts):
        if alert.get('alert_type') == alert_id:
            alert_index = i
            break
    
    if alert_index is None:
        raise HTTPException(
            status_code=HTTP_NOT_FOUND,
            detail=f"Weather alert with id '{alert_id}' not found"
        )
    
    # Remove the alert
    alerts.pop(alert_index)
    
    # Write back to CSV (no building_code column)
    write_csv_file(CSV_WEATHER_ALERTS, alerts, ["alert_type", "value", "operator", "intervention_id"])
    
    return {"message": f"Weather alert '{alert_id}' deleted successfully"}


@app.get("/dashboard")
def get_dashboard() -> List[Dict[str, str]]:
    """
    Get merged dashboard data combining all data sources.
    
    This endpoint merges data from three CSV files:
    - locations.csv: Building location information
    - results.csv: Weather check results
    - interventions.csv: Intervention definitions
    
    The merge is performed by:
    1. Using building_code to match results with locations
    2. Using intervention_id to match results with interventions
    
    Returns:
        List of merged records, one per result, containing:
        - building_code: Building identifier
        - owner_emails: Owner email addresses (from locations)
        - longitude: Longitude coordinate (from locations)
        - latitude: Latitude coordinate (from locations)
        - windspeed_val: Wind speed value (from results)
        - precipitation_val: Precipitation amount (from results)
        - intervention_title: Intervention title (from interventions)
        - intervention_description: Intervention description (from interventions)
        - timestamp: When the check was performed (from results)
        - intervention_id: Intervention identifier (from results)
    """
    # Read all data sources
    locations: List[Dict[str, str]] = read_csv_file(CSV_LOCATIONS)
    results: List[Dict[str, str]] = read_csv_file(CSV_RESULTS)
    interventions: List[Dict[str, str]] = read_csv_file(CSV_INTERVENTIONS)
    
    # Create lookup dictionaries for efficient O(1) lookups
    # Key: building_code, Value: location dictionary
    locations_map: Dict[str, Dict[str, str]] = {
        loc["building_code"]: loc for loc in locations
    }
    
    # Key: intervention_id, Value: intervention dictionary
    interventions_map: Dict[str, Dict[str, str]] = {
        interv["id"]: interv for interv in interventions
    }
    
    # Merge results with location and intervention data
    merged_data: List[Dict[str, str]] = []
    
    for result in results:
        building_code: str = result.get("building_code", "")
        intervention_id: str = result.get("intervention_id", "")
        
        # Get related data (default to empty dict if not found)
        location: Dict[str, str] = locations_map.get(building_code, {})
        intervention: Dict[str, str] = interventions_map.get(intervention_id, {})
        
        # Build merged record
        merged_record: Dict[str, str] = {
            "building_code": building_code,
            "owner_emails": location.get("owner_emails", ""),
            "longitude": location.get("longitude", ""),
            "latitude": location.get("latitude", ""),
            "windspeed_val": result.get("windspeed_val", ""),
            "precipitation_val": result.get("precipitation_val", ""),
            "intervention_title": intervention.get("title", ""),
            "intervention_description": intervention.get("description", ""),
            "timestamp": result.get("timestamp", ""),
            "intervention_id": intervention_id
        }
        
        merged_data.append(merged_record)
    
    return merged_data
