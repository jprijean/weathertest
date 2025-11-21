"""Status calculator for determining site status based on weather results."""
import os
import csv
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from models import Database


def calculate_site_status(db: Database, building_code: str) -> str:
    """
    Calculate site status based on alert dates.
    Status logic:
    - Green: No alert (no alert today)
    - Red: Alert raised for today (same day)
    - Yellow/Amber: Alert will occur in future days (D+1 to D+3) but not today
    - Purple: Alert was raised yesterday (past)
    
    Args:
        db: Database instance
        building_code: Building code to calculate status for
        
    Returns:
        Status string: 'green', 'red', 'yellow', or 'purple'
    """
    # Get all results for this building
    if not hasattr(db, 'results_file') or not os.path.exists(db.results_file):
        return 'green'
    
    now = datetime.now()
    today = datetime(now.year, now.month, now.day)
    yesterday = today - timedelta(days=1)
    yesterday_end = today
    day1_start = today + timedelta(days=1)
    day1_end = today + timedelta(days=2)
    day2_start = today + timedelta(days=2)
    day2_end = today + timedelta(days=3)
    day3_start = today + timedelta(days=3)
    day3_end = today + timedelta(days=4)
    
    building_results = []
    with open(db.results_file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('building_code') == building_code:
                building_results.append(row)
    
    if not building_results:
        return 'green'
    
    # Group results by day
    today_results = []
    yesterday_results = []
    future_results = []
    
    for result in building_results:
        try:
            timestamp_str = result.get('timestamp', '')
            if not timestamp_str:
                continue
            result_date = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00').split('+')[0])
            
            # Check today
            if today <= result_date < day1_start:
                today_results.append(result)
            # Check yesterday
            elif yesterday <= result_date < yesterday_end:
                yesterday_results.append(result)
            # Check future (D+1 to D+3)
            elif day1_start <= result_date < day3_end:
                future_results.append(result)
        except (ValueError, TypeError) as e:
            continue
    
    # Check today's status
    today_has_alert = any(
        r.get('intervention_id') and r.get('intervention_id') != 'no-alert' 
        for r in today_results
    )
    
    # Check future days
    future_has_alert = any(
        r.get('intervention_id') and r.get('intervention_id') != 'no-alert' 
        for r in future_results
    )
    
    # Check yesterday
    yesterday_has_alert = any(
        r.get('intervention_id') and r.get('intervention_id') != 'no-alert' 
        for r in yesterday_results
    )
    
    # Determine status priority: Red > Purple > Yellow > Green
    if today_has_alert:
        return 'red'  # Alert raised for today - highest priority
    elif yesterday_has_alert and not today_has_alert and not future_has_alert:
        return 'purple'  # Alert was yesterday, but not today or future
    elif future_has_alert:
        return 'yellow'  # Alert will occur in future (D+1 to D+3)
    else:
        return 'green'  # No alert


def get_status_label(status: str) -> str:
    """Get human-readable label for status."""
    status_map = {
        'green': 'Normal',
        'red': 'Alert Today',
        'yellow': 'Future Alert',
        'purple': 'Past Alert'
    }
    return status_map.get(status, 'Unknown')


def get_status_description(status: str) -> str:
    """Get description for status."""
    status_map = {
        'green': 'No weather alerts. All conditions normal.',
        'red': 'Weather alert is active for today. Immediate attention may be required.',
        'yellow': 'Weather alert is forecasted for the next few days. Monitor conditions.',
        'purple': 'Weather alert was active yesterday but is no longer active today.'
    }
    return status_map.get(status, 'Status unknown.')


def determine_alert_type(db: Database, building_code: str, latest_result: dict) -> Optional[str]:
    """
    Determine which alert type (Windspeed or Precipitation) triggered the current status.
    
    Args:
        db: Database instance
        building_code: Building code
        latest_result: Latest result dictionary with windspeed_val, precipitation_val, intervention_id
        
    Returns:
        'Windspeed', 'Precipitation', or None if no alert triggered
    """
    if not latest_result or latest_result.get('intervention_id') == 'no-alert':
        return None
    
    # Get all weather alerts
    alerts = db.get_weather_alerts()
    if not alerts:
        return None
    
    windspeed_val = latest_result.get('windspeed_val', 0)
    precipitation_val = latest_result.get('precipitation_val', 0)
    intervention_id = latest_result.get('intervention_id')
    
    # Check which alert type matches the intervention_id and is triggered
    for alert in alerts:
        if alert.intervention_id == intervention_id:
            # Check if this alert is actually triggered by the current values
            if alert.alert_type == "Windspeed":
                # Evaluate the condition
                if evaluate_alert_condition(windspeed_val, alert.operator, alert.value):
                    return "Windspeed"
            elif alert.alert_type == "Precipitation":
                # Evaluate the condition
                if evaluate_alert_condition(precipitation_val, alert.operator, alert.value):
                    return "Precipitation"
    
    # If we can't determine, check which one is triggered
    for alert in alerts:
        if alert.alert_type == "Windspeed":
            if evaluate_alert_condition(windspeed_val, alert.operator, alert.value):
                if alert.intervention_id == intervention_id:
                    return "Windspeed"
        elif alert.alert_type == "Precipitation":
            if evaluate_alert_condition(precipitation_val, alert.operator, alert.value):
                if alert.intervention_id == intervention_id:
                    return "Precipitation"
    
    return None


def evaluate_alert_condition(actual_value: float, operator: str, threshold: float) -> bool:
    """Evaluate a single condition (same logic as ComparisonEngine)."""
    if operator == ">":
        return actual_value > threshold
    elif operator == "<":
        return actual_value < threshold
    elif operator == ">=":
        return actual_value >= threshold
    elif operator == "<=":
        return actual_value <= threshold
    elif operator == "==":
        return abs(actual_value - threshold) < 0.01
    return False

