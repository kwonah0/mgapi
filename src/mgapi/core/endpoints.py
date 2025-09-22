"""Core endpoints management functionality."""

from typing import Dict, Any, Optional, List

from .client import MGAPIClient


def get_available_endpoints(url: Optional[str] = None) -> Dict[str, Any]:
    """Get available endpoints from the server.

    Args:
        url: Server URL. If None, uses config value.

    Returns:
        Dictionary containing endpoints info or error status
    """
    client = MGAPIClient(url)

    if not client.check_health():
        return {
            "status": "error",
            "message": "Server is not responding"
        }

    api_info = client.get_api_info()
    if not api_info:
        return {
            "status": "error",
            "message": "Failed to get API information"
        }

    return {
        "status": "success",
        "url": client.base_url,
        "endpoints": api_info
    }


def format_endpoints_simple(endpoints_data: Dict[str, Any]) -> List[str]:
    """Format endpoints data for simple text output.

    Args:
        endpoints_data: Endpoints data from get_available_endpoints

    Returns:
        List of formatted endpoint strings
    """
    if endpoints_data.get("status") != "success":
        return [f"Error: {endpoints_data.get('message', 'Unknown error')}"]

    lines = []
    url = endpoints_data.get("url", "Unknown URL")
    lines.append(f"Server: {url}")
    lines.append("")

    endpoints = endpoints_data.get("endpoints", {})

    if "endpoints" in endpoints:
        lines.append("Available Endpoints:")
        for endpoint in endpoints["endpoints"]:
            method = endpoint.get("method", "").upper()
            path = endpoint.get("path", "")
            description = endpoint.get("description", "")
            lines.append(f"  {method:6} {path:20} - {description}")
    else:
        lines.append("Endpoints information not available")

    return lines