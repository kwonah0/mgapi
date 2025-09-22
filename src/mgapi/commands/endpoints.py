"""Endpoints command implementation."""

import click
from colorama import Fore, Style

from ..core.endpoints import get_available_endpoints, format_endpoints_simple
from ..utils.formatters import print_error, format_output
from ..utils.logger import logger


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
    logger.info("Getting API endpoints information...")

    result = get_available_endpoints()

    if result["status"] != "success":
        print_error("Failed to get endpoints", result.get("message", "Unknown error"))
        return 1

    if format == "rich":
        lines = format_endpoints_simple(result)
        for line in lines:
            print(line)

        print(f"\n{Fore.CYAN}Usage Examples:{Style.RESET_ALL}")
        print("  mgapi status          - Check server health")
        print("  mgapi send -q 'ping'  - Send a query")
        print("  mgapi close           - Stop the server")
    else:
        output = format_output(result["endpoints"], format)
        click.echo(output)

    return 0


