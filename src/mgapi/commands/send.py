"""Send command implementation."""

import sys
from typing import Optional

import click
from InquirerPy import inquirer
from colorama import Fore, Style

from ..core.client import check_server_health, send_query
from ..utils.formatters import print_error, print_query_result, format_output
from ..utils.validators import validate_query
from ..utils.logger import logger


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
            print(f"\n{Fore.YELLOW}Cancelled{Style.RESET_ALL}")
            return 1
        except Exception as e:
            print_error(f"Failed to get input: {str(e)}")
            return 1
    
    validated_query = validate_query(query)
    if not validated_query:
        print_error("Invalid query", "Query cannot be empty")
        return 1
    
    logger.info("Sending query to server...")

    if not check_server_health():
        print_error(
            "Server is not responding",
            "Make sure the server is running (use 'mgapi start')"
        )
        return 1

    print(f"{Fore.CYAN}Sending query...{Style.RESET_ALL}")

    result = send_query(validated_query)

    if result is None:
        print_error("Failed to execute query")
        return 1

    if format == "rich":
        print_query_result(result)
    else:
        output = format_output(result, format)
        click.echo(output)

    logger.info("Query executed successfully")
    return 0