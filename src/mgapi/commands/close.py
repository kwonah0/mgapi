"""Close command implementation."""

import subprocess
import sys

import click

from ..api_client import MGAPIClient
from ..config import get_mgapi_url, get_bjob_id
from ..utils.formatters import print_success, print_error
from ..utils.logger import logger


@click.command()
def close():
    """Close the running MGAPI server."""
    url = get_mgapi_url()
    client = MGAPIClient(url)
    
    logger.info("Checking server status")
    
    if not client.check_health():
        print_error("Server is not running")
        return 1
    
    # Try to get job ID from config file first
    logger.info("Getting job ID from configuration")
    job_id = get_bjob_id()
    
    if not job_id:
        # Fallback to API call
        logger.info("Getting job ID from server API")
        job_info = client.get_job_info()
        if job_info:
            job_id = job_info.get("job_id") or job_info.get("bjob_id")
    
    if not job_id:
        print_error(
            "Could not retrieve job ID",
            "Check mgapi_config.json or server /job_info endpoint"
        )
        return 1
    
    logger.info(f"Attempting to kill job {job_id}")
    
    try:
        result = subprocess.run(
            ["bkill", str(job_id)],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode == 0:
            print_success(f"Successfully closed server (job ID: {job_id})")
            logger.info(f"Server closed successfully")
            return 0
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            print_error(f"Failed to kill job: {error_msg}")
            logger.error(f"bkill failed: {error_msg}")
            return 1
            
    except FileNotFoundError:
        print_error(
            "bkill command not found",
            "Make sure LSF is installed and available in PATH"
        )
        logger.error("bkill command not found")
        return 1
    except Exception as e:
        print_error(f"Unexpected error: {str(e)}")
        logger.error(f"Unexpected error during close: {e}")
        return 1