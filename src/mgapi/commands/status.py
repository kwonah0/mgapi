"""Status command implementation."""

import click

from ..core.server import check_server_status
from ..utils.formatters import print_status, print_job_info
from ..utils.logger import logger


@click.command()
@click.pass_context
def status(ctx):
    """Check the status of the MGAPI server."""
    logger.info("Checking server status...")

    result = check_server_status()

    if result["status"] == "running":
        print_status(True, result["url"])
        if result.get("job_info"):
            print_job_info(result["job_info"])
        logger.info("Server is healthy")
        ctx.exit(0)
    elif result["status"] == "not_responding":
        print_status(False, result["url"])
        logger.warning("Server is not responding")
        ctx.exit(1)
    else:
        print(f"Status: {result.get('message', 'Unknown status')}")
        logger.warning(f"Server status: {result['status']}")
        ctx.exit(1)