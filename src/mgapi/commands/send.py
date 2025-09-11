"""Send command implementation."""

import sys
from typing import Optional

import click
from InquirerPy import inquirer
from rich.console import Console
from rich.panel import Panel

from ..api_client import MGAPIClient
from ..config import get_mgapi_url
from ..utils.formatters import print_error, print_success, format_output
from ..utils.validators import validate_query
from ..utils.logger import logger

console = Console()


@click.command()
@click.option(
    "--query",
    "-q",
    help="Query to send to the server",
)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["rich", "json", "yaml", "plain"]),
    default="rich",
    help="Output format",
)
def send(query: Optional[str], format: str):
    """Send a query to the MGAPI server."""
    if not query:
        try:
            query = inquirer.text(
                message="Enter your query:",
                validate=lambda text: len(text.strip()) > 0,
                invalid_message="Query cannot be empty",
                multiline=True,
            ).execute()
        except KeyboardInterrupt:
            console.print("\n[yellow]Cancelled[/yellow]")
            return 1
        except Exception as e:
            print_error(f"Failed to get input: {str(e)}")
            return 1
    
    validated_query = validate_query(query)
    if not validated_query:
        print_error("Invalid query", "Query cannot be empty")
        return 1
    
    url = get_mgapi_url()
    client = MGAPIClient(url)
    
    logger.info(f"Sending query to {url}")
    
    if not client.check_health():
        print_error(
            "Server is not responding",
            "Make sure the server is running (use 'mgapi start')"
        )
        return 1
    
    console.print(f"[cyan]Sending query...[/cyan]")
    
    result = client.execute_query(validated_query)
    
    if result is None:
        print_error("Failed to execute query")
        return 1
    
    if format == "rich":
        if "error" in result:
            print_error(f"Query execution failed: {result['error']}")
        else:
            console.print(Panel(
                str(result.get("result", result)),
                title="Query Result",
                border_style="green",
            ))
            print_success("Query executed successfully")
    else:
        output = format_output(result, format)
        click.echo(output)
    
    logger.info("Query executed successfully")
    return 0