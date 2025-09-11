"""Input validation utilities."""

import re
from typing import Optional
from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """Validate if a string is a valid URL.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if valid URL, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False


def validate_port(port: int) -> bool:
    """Validate if a port number is valid.
    
    Args:
        port: Port number to validate
        
    Returns:
        True if valid port (1-65535), False otherwise
    """
    return isinstance(port, int) and 1 <= port <= 65535


def validate_query(query: str) -> Optional[str]:
    """Validate and clean a query string.
    
    Args:
        query: Query string to validate
        
    Returns:
        Cleaned query or None if invalid
    """
    if not query or not isinstance(query, str):
        return None
    
    cleaned = query.strip()
    if not cleaned:
        return None
    
    return cleaned


def validate_keypath(keypath: str) -> bool:
    """Validate a configuration keypath.
    
    Args:
        keypath: Dot-separated keypath (e.g., "server.host")
        
    Returns:
        True if valid keypath format, False otherwise
    """
    if not keypath or not isinstance(keypath, str):
        return False
    
    pattern = r'^[a-zA-Z_][a-zA-Z0-9_]*(\.[a-zA-Z_][a-zA-Z0-9_]*)*$'
    return bool(re.match(pattern, keypath))