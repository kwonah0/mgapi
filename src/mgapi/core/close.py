"""Core server closing functionality."""

import subprocess
from typing import Dict, Any, Optional

from loguru import logger

from .client import check_server_health, get_job_status
from ..config import get_bjob_id


def close_server() -> Dict[str, Any]:
    """Close the running MGAPI server.

    Returns:
        Dictionary with result status and info
    """
    logger.info("Checking server status before closing...")

    if not check_server_health():
        return {"status": "not_running", "message": "Server is not running"}

    # Try to get job ID from config file first
    logger.info("Getting job ID from configuration...")
    job_id = get_bjob_id()

    if not job_id:
        # Fallback to API call
        logger.info("Getting job ID from server API...")
        job_info = get_job_status()
        if job_info:
            job_id = job_info.get("job_id") or job_info.get("bjob_id")

    if not job_id:
        return {
            "status": "error",
            "message": "Could not retrieve job ID",
            "suggestion": "Check mgapi_config.json or server /job_info endpoint"
        }

    logger.info(f"Attempting to kill job {job_id}")

    try:
        result = subprocess.run(
            ["bkill", str(job_id)],
            capture_output=True,
            text=True,
            check=False
        )

        if result.returncode == 0:
            logger.info(f"Server closed successfully (job ID: {job_id})")
            return {
                "status": "success",
                "job_id": job_id,
                "message": f"Successfully closed server (job ID: {job_id})"
            }
        else:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            logger.error(f"bkill failed: {error_msg}")
            return {
                "status": "error",
                "message": f"Failed to kill job: {error_msg}"
            }

    except FileNotFoundError:
        logger.error("bkill command not found")
        return {
            "status": "error",
            "message": "bkill command not found",
            "suggestion": "Make sure LSF is installed and available in PATH"
        }
    except Exception as e:
        logger.error(f"Unexpected error during close: {e}")
        return {
            "status": "error",
            "message": f"Unexpected error: {str(e)}"
        }