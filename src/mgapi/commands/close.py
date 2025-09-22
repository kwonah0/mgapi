"""Close command implementation."""

import click

from ..core.close import close_server
from ..utils.formatters import print_success, print_error
from ..utils.logger import logger


@click.command()
def close():
    """Close the running MGAPI server."""
    logger.info("Closing server...")

    result = close_server()

    if result["status"] == "success":
        print_success(result["message"])
        return 0
    elif result["status"] == "not_running":
        print_error(result["message"])
        return 1
    else:
        suggestion = result.get("suggestion")
        print_error(result["message"], suggestion)
        return 1