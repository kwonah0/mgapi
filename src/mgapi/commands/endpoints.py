"""Endpoints command implementation."""

import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..api_client import MGAPIClient
from ..config import get_mgapi_url
from ..utils.formatters import print_error, format_output
from ..utils.logger import logger

console = Console()


@click.command()
@click.option(
    "--format",
    "-f", 
    type=click.Choice(["rich", "json", "yaml", "plain"]),
    default="rich",
    help="Output format"
)
def endpoints(format):
    """Display available API endpoints from the server.
    
    Calls the root endpoint (/) to get endpoint information and displays
    it in a formatted table or other requested format.
    """
    url = get_mgapi_url()
    client = MGAPIClient(url)
    
    logger.info(f"Getting API information from {url}")
    
    # Check if server is reachable
    if not client.check_health():
        print_error(
            "Server is not responding",
            f"Make sure the server is running at {url}"
        )
        return 1
    
    # Get API information
    api_info = client.get_api_info()
    
    if not api_info:
        print_error("Failed to get API information from server")
        return 1
    
    if format == "rich":
        display_endpoints_rich(api_info, url)
    else:
        output = format_output(api_info, format)
        click.echo(output)
    
    return 0


def display_endpoints_rich(api_info: dict, server_url: str):
    """Display endpoints information in rich format."""
    
    # Display server info
    message = api_info.get("message", "MGAPI Server")
    console.print(Panel(
        f"[bold]{message}[/bold]\n[cyan]Server URL: {server_url}[/cyan]",
        title="API Information",
        border_style="blue"
    ))
    
    # Display endpoints table
    endpoints_data = api_info.get("endpoints", {})
    
    if not endpoints_data:
        console.print("[yellow]No endpoints information available[/yellow]")
        return
    
    table = Table(
        title="Available Endpoints",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Endpoint", style="cyan", min_width=15)
    table.add_column("Method", style="green", min_width=8)
    table.add_column("Description", style="white")
    
    # Add endpoints to table
    for endpoint, description in endpoints_data.items():
        # Determine HTTP method based on endpoint pattern
        if endpoint == "/execute":
            method = "POST"
        else:
            method = "GET"
        
        # Handle different description formats
        if isinstance(description, dict):
            desc = description.get("description", str(description))
        else:
            desc = str(description)
        
        table.add_row(endpoint, method, desc)
    
    console.print()
    console.print(table)
    
    # Additional info
    if "version" in api_info:
        console.print(f"\n[dim]Server Version: {api_info['version']}[/dim]")
    
    if "timestamp" in api_info:
        console.print(f"[dim]Timestamp: {api_info['timestamp']}[/dim]")
    
    # Usage examples
    console.print("\n[bold]Usage Examples:[/bold]")
    console.print("  mgapi status          - Check server health")
    console.print("  mgapi send -q 'ping'  - Send a query")
    console.print("  mgapi info            - View configuration")
    console.print("  mgapi close           - Stop the server")