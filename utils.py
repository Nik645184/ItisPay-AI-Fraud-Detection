import json
import logging
import requests
import pandas as pd
from typing import Dict, Any, List, Tuple, Optional

logger = logging.getLogger(__name__)

def is_valid_ip(ip: str) -> bool:
    """
    Validate if the provided string is a valid IP address
    
    Args:
        ip: The IP address to validate
    
    Returns:
        bool: True if valid IP, False otherwise
    """
    import re
    pattern = r'^(\d{1,3})\.(\d{1,3})\.(\d{1,3})\.(\d{1,3})$'
    match = re.match(pattern, ip)
    if not match:
        return False
    
    # Check if each octet is between 0 and 255
    for octet in match.groups():
        if int(octet) > 255:
            return False
    
    return True

def is_valid_eth_address(address: str) -> bool:
    """
    Validate if the provided string is a valid Ethereum address
    
    Args:
        address: The Ethereum address to validate
    
    Returns:
        bool: True if valid Ethereum address, False otherwise
    """
    import re
    # Basic Ethereum address validation (starts with 0x followed by 40 hex chars)
    pattern = r'^0x[a-fA-F0-9]{40}$'
    return bool(re.match(pattern, address))

def get_country_from_ip(ip: str) -> Optional[str]:
    """
    Get the country code from an IP address using ipinfo.io API
    
    Args:
        ip: The IP address to lookup
    
    Returns:
        str: Two-letter country code or None if lookup failed
    """
    try:
        response = requests.get(f"https://ipinfo.io/{ip}/json")
        if response.status_code == 200:
            data = response.json()
            return data.get("country")
        return None
    except Exception as e:
        logger.error(f"Error getting country from IP: {e}")
        return None
    
def normalize_score(score: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """
    Normalize a score to the 0-100 range
    
    Args:
        score: The score to normalize
        min_val: The minimum possible value of the score
        max_val: The maximum possible value of the score
    
    Returns:
        float: Normalized score in the 0-100 range
    """
    # Ensure the score is within the min_val to max_val range
    clamped_score = max(min(score, max_val), min_val)
    
    # Normalize to 0-100
    normalized = ((clamped_score - min_val) / (max_val - min_val)) * 100
    
    return round(normalized, 2)

def format_alerts(alerts: List[str]) -> str:
    """
    Format the list of alerts into a readable string
    
    Args:
        alerts: List of alert messages
    
    Returns:
        str: Formatted alert string
    """
    if not alerts:
        return "No alerts detected"
    
    return "\n".join([f"• {alert}" for alert in alerts])

def get_risk_level(score: float) -> str:
    """
    Get the risk level based on the score
    
    Args:
        score: Risk score (0-100)
    
    Returns:
        str: Risk level (Low, Medium, High, Critical)
    """
    from config import LOW_RISK_THRESHOLD, MEDIUM_RISK_THRESHOLD, HIGH_RISK_THRESHOLD
    
    if score < LOW_RISK_THRESHOLD:
        return "Low"
    elif score < MEDIUM_RISK_THRESHOLD:
        return "Medium"
    elif score < HIGH_RISK_THRESHOLD:
        return "High"
    else:
        return "Critical"
