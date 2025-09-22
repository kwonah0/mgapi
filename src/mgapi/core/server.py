"""Core server management functionality."""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from loguru import logger
from watchdog.observers.polling import PollingObserver
from watchdog.events import FileSystemEventHandler

from .client import MGAPIClient
from ..config import get_server_info, get_config_file_path


class ConfigFileHandler(FileSystemEventHandler):
    """Monitor mgapi_config.json for changes."""

    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config_updated = False
        self.config_data = None

    def on_created(self, event):
        """Handle file creation."""
        if Path(event.src_path).name == self.config_path.name:
            logger.info(f"Config file created: {event.src_path}")
            self.config_updated = True
            self._load_config()

    def on_modified(self, event):
        """Handle file modification."""
        if Path(event.src_path).name == self.config_path.name:
            logger.info(f"Config file updated: {event.src_path}")
            self.config_updated = True
            self._load_config()

    def _load_config(self):
        """Load configuration from file."""
        try:
            time.sleep(0.1)
            if self.config_path.exists():
                with open(self.config_path) as f:
                    self.config_data = json.load(f)
                    url = self.config_data.get("mgapi_url", "N/A")
                    job_id = self.config_data.get("bjob_id", "N/A")
                    logger.info(f"Loaded config: URL={url}, Job ID={job_id}")
        except Exception as e:
            logger.error(f"Error loading config: {e}")
            self.config_data = None


def start_server(command: str, timeout: int = 600, force: bool = False) -> Dict[str, Any]:
    """Start the server and monitor for config file creation.

    Args:
        command: Server start command
        timeout: Monitoring timeout in seconds
        force: Force start even if server is running

    Returns:
        Dictionary with result status and info
    """
    config_file = get_config_file_path()

    # Check for existing server
    if not force and config_file.exists():
        logger.info("Found existing config file, checking server status...")

        server_info = get_server_info()
        url = server_info.get("mgapi_url")

        if url:
            client = MGAPIClient(url)
            if client.check_health():
                logger.info(f"Server is already running at {url}")
                job_info = client.get_job_info()
                return {
                    "status": "already_running",
                    "url": url,
                    "job_info": job_info
                }
            else:
                logger.warning("Server not responding, starting new server...")
                backup_path = config_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                config_file.rename(backup_path)
                logger.info(f"Backed up old config to {backup_path}")

    # Set up file monitoring with polling for NFS compatibility
    logger.info("Setting up config file monitoring with polling...")
    handler = ConfigFileHandler(config_file)
    observer = PollingObserver(timeout=1)  # Poll every 1 second
    observer.schedule(handler, str(config_file.parent), recursive=False)
    observer.start()

    # Start server in background
    logger.info(f"Starting server with command: {command}")

    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True  # Detach from parent process
        )
        logger.info(f"Server process started in background (PID: {process.pid})")

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        observer.stop()
        observer.join()
        return {"status": "failed", "error": str(e)}

    # Monitor for server readiness using only config file observer
    logger.info(f"Monitoring for server readiness (timeout: {timeout}s)...")
    logger.info("Server process is running in background, monitoring config file for readiness...")

    start_time = time.time()

    while time.time() - start_time < timeout:
        # Check if config file was updated and server is ready
        if handler.config_updated and handler.config_data:
            url = handler.config_data.get("mgapi_url")
            if url:
                logger.info(f"Config file updated with URL: {url}, testing connection...")

                client = MGAPIClient(url)
                if client.check_health():
                    logger.info(f"Server is ready at {url}")

                    job_info = client.get_job_info()
                    if not job_info:
                        job_info = {
                            "job_id": handler.config_data.get("bjob_id", "N/A"),
                            "status": "Running",
                            "host": "N/A",
                            "queue": "N/A"
                        }

                    # Collect any output from the process
                    stdout, stderr = "", ""
                    try:
                        stdout, stderr = process.communicate(timeout=0.1)
                    except subprocess.TimeoutExpired:
                        # Process is still running, which is expected
                        pass
                    except Exception:
                        # Process might have finished, try to get output
                        try:
                            stdout, stderr = process.communicate(timeout=0.1)
                        except:
                            pass

                    observer.stop()
                    observer.join()

                    result = {
                        "status": "success",
                        "url": url,
                        "job_info": job_info
                    }
                    if stdout:
                        result["stdout"] = stdout
                    if stderr:
                        result["stderr"] = stderr

                    return result
                else:
                    logger.warning("Server not ready yet, continuing to monitor...")
                    handler.config_updated = False

        time.sleep(2)  # Check every 2 seconds

    # Timeout reached - collect any available output
    observer.stop()
    observer.join()
    logger.error(f"Timeout: Server did not start within {timeout} seconds")
    logger.warning("Server process continues running in background. Check manually with 'mgapi status'")

    # Try to collect output for debugging
    stdout, stderr = "", ""
    try:
        stdout, stderr = process.communicate(timeout=0.1)
    except subprocess.TimeoutExpired:
        # Process is still running, which is expected for background processes
        logger.info("Server process is still running in background")
    except Exception:
        # Process might have finished, try to get output
        try:
            stdout, stderr = process.communicate(timeout=0.1)
        except:
            pass

    result = {
        "status": "timeout",
        "error": f"Server did not start within {timeout} seconds"
    }
    if stdout:
        result["stdout"] = stdout
    if stderr:
        result["stderr"] = stderr

    return result


def check_server_status() -> Dict[str, Any]:
    """Check current server status.

    Returns:
        Dictionary with server status info
    """
    config_file = get_config_file_path()

    if not config_file.exists():
        return {"status": "no_config", "message": "No config file found"}

    server_info = get_server_info()
    url = server_info.get("mgapi_url")

    if not url:
        return {"status": "no_url", "message": "No server URL in config"}

    client = MGAPIClient(url)
    is_healthy = client.check_health()

    if is_healthy:
        job_info = client.get_job_info()
        return {
            "status": "running",
            "url": url,
            "healthy": True,
            "job_info": job_info
        }
    else:
        return {
            "status": "not_responding",
            "url": url,
            "healthy": False
        }


def get_endpoints_info(url: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Get available endpoints from server.

    Args:
        url: Server URL. If None, uses config value.

    Returns:
        Endpoints info or None if request failed
    """
    client = MGAPIClient(url)
    return client.get_api_info()