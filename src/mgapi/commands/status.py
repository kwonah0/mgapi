"""Status command implementation."""

import click

from ..api_client import MGAPIClient
from ..config import get_mgapi_url
from ..utils.formatters import print_status
from ..utils.logger import logger


@click.command()
def status():
    """Check the status of the MGAPI server."""
    url = get_mgapi_url()
    logger.info(f"Checking server status at {url}")
    
    client = MGAPIClient(url)
    is_healthy = client.check_health()
    
    print_status(is_healthy, url)
    
    if is_healthy:
        logger.info("Server is healthy")
        return 0
    else:
        logger.warning("Server is not responding")
        return 1