"""Start command implementation for TCL server."""

import click

from ..core.server import start_server
from ..utils.formatters import print_success, print_error, print_job_info
from ..utils.logger import logger


@click.command()
@click.option("--command", "-c", help="Server start command", required=True)
@click.option("--timeout", "-t", default=600, help="Monitoring timeout in seconds (default: 600)")
@click.option("--force", "-f", is_flag=True, help="Force start even if server is running")
def start(command, timeout, force):
    """Start the TCL server and monitor for config file creation.

    Examples:
        mgapi start --command "bsub -q gpu -n 4 python server.py"
        mgapi start --command "./start_server.sh" --timeout 300
        mgapi start --command "tcl_server --port 8080" --force
    """
    logger.info(f"Starting server with command: {command}")

    result = start_server(command, timeout, force)

    # Helper function to print process output
    def print_process_output(result):
        if result.get("stdout"):
            print(f"\nServer Output:\n{result['stdout']}")
        if result.get("stderr"):
            print(f"\nServer Errors:\n{result['stderr']}")

    if result["status"] == "success":
        print_success(f"Server is ready at {result['url']}")
        if result.get("job_info"):
            print_job_info(result["job_info"])
        print_process_output(result)
        return 0
    elif result["status"] == "already_running":
        print_success(f"Server is already running at {result['url']}")
        if result.get("job_info"):
            print_job_info(result["job_info"])
        return 0
    elif result["status"] == "timeout":
        print_error("Server start timeout", f"Server did not start within {timeout} seconds")
        print("Server process continues running in background. Check manually with 'mgapi status'")
        print_process_output(result)
        return 1
    else:
        print_error("Failed to start server", result.get("error", "Unknown error"))
        print_process_output(result)
        return 1