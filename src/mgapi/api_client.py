"""HTTP client for MGAPI server interactions."""

import asyncio
from typing import Any, Dict, Optional

import httpx
from rich.console import Console

from .config import get_mgapi_url

console = Console()


class MGAPIClient:
    """Client for interacting with MGAPI server."""
    
    def __init__(self, base_url: Optional[str] = None):
        """Initialize the client.
        
        Args:
            base_url: Base URL for the API server. If None, uses config value.
        """
        self.base_url = base_url or get_mgapi_url()
        self.timeout = httpx.Timeout(30.0, connect=5.0)
        
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Make an async HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body for POST requests
            params: Query parameters
            
        Returns:
            Response data or None if request failed
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    json=json,
                    params=params,
                )
                response.raise_for_status()
                
                if response.content:
                    return response.json()
                return {"status": "success"}
                
        except httpx.ConnectError:
            console.print(f"[red]Failed to connect to server at {self.base_url}[/red]")
            return None
        except httpx.TimeoutException:
            console.print("[red]Request timed out[/red]")
            return None
        except httpx.HTTPStatusError as e:
            console.print(f"[red]HTTP Error {e.response.status_code}: {e.response.text}[/red]")
            return None
        except Exception as e:
            console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return None
    
    def make_request(
        self,
        method: str,
        endpoint: str,
        json: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Sync wrapper for making requests.
        
        Args:
            method: HTTP method (GET, POST, etc.)
            endpoint: API endpoint path
            json: JSON body for POST requests
            params: Query parameters
            
        Returns:
            Response data or None if request failed
        """
        return asyncio.run(self._make_request(method, endpoint, json, params))
    
    def check_health(self) -> bool:
        """Check if the server is healthy.
        
        Returns:
            True if server is healthy, False otherwise
        """
        result = self.make_request("GET", "/health")
        return result is not None
    
    def get_api_info(self) -> Optional[Dict[str, Any]]:
        """Get API information and available endpoints.
        
        Returns:
            API info including endpoints or None if request failed
        """
        return self.make_request("GET", "/")
    
    def get_job_info(self) -> Optional[Dict[str, Any]]:
        """Get LSF job information from the server.
        
        Returns:
            Job info including job_id or None if request failed
        """
        return self.make_request("GET", "/job_info")
    
    def execute_query(self, query: str) -> Optional[Dict[str, Any]]:
        """Execute a query on the server.
        
        Args:
            query: Query string to execute
            
        Returns:
            Query result or None if request failed
        """
        return self.make_request("POST", "/execute", json={"query": query})