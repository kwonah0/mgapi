"""Start command implementation for TCL server."""

import json
import subprocess
import time
from datetime import datetime
from pathlib import Path

import click
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from ..api_client import MGAPIClient
from ..config import get_server_info
from ..utils.formatters import print_success, print_error
from ..utils.logger import logger

console = Console()


class ConfigFileHandler(FileSystemEventHandler):
    """Monitor mgapi_config.json for changes."""
    
    def __init__(self):
        self.config_updated = False
        self.config_data = None
        
    def on_created(self, event):
        """Handle file creation."""
        if event.src_path.endswith("mgapi_config.json"):
            console.print(f"[green]✓ Config file created: {event.src_path}[/green]")
            self.config_updated = True
            self._load_config()
    
    def on_modified(self, event):
        """Handle file modification."""
        if event.src_path.endswith("mgapi_config.json"):
            console.print(f"[yellow]Config file updated: {event.src_path}[/yellow]")
            self.config_updated = True
            self._load_config()
    
    def _load_config(self):
        """Load configuration from file."""
        try:
            # Wait a bit for file write to complete
            time.sleep(0.1)
            config_file = Path("mgapi_config.json")
            if config_file.exists():
                with open(config_file) as f:
                    self.config_data = json.load(f)
                    url = self.config_data.get("mgapi_url", "N/A")
                    job_id = self.config_data.get("bjob_id", "N/A")
                    console.print(f"[cyan]Loaded config: URL={url}, Job ID={job_id}[/cyan]")
        except Exception as e:
            console.print(f"[red]Error loading config: {e}[/red]")
            self.config_data = None


def print_job_info(job_info: dict):
    """Format and print job information."""
    console.print(Panel(
        f"""[bold]Server Information[/bold]

Job ID: {job_info.get('job_id', 'N/A')}
Status: {job_info.get('status', 'Unknown')}
Host: {job_info.get('host', 'N/A')}
Queue: {job_info.get('queue', 'N/A')}
Submit Time: {job_info.get('submit_time', 'N/A')}
Start Time: {job_info.get('start_time', 'N/A')}
CPU Time: {job_info.get('cpu_time', 'N/A')}
Memory: {job_info.get('memory', 'N/A')}

Additional Info:
{json.dumps(job_info.get('extra', {}), indent=2) if job_info.get('extra') else 'None'}
        """,
        title="Job Information",
        border_style="green"
    ))


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
    config_file = Path("mgapi_config.json")
    
    # 1. Check for existing server
    if not force and config_file.exists():
        console.print("[yellow]Found existing mgapi_config.json, checking server status...[/yellow]")
        
        server_info = get_server_info()
        url = server_info.get("mgapi_url")
        
        if url:
            client = MGAPIClient(url)
            if client.check_health():
                console.print(f"[green]✓ Server is already running at {url}[/green]")
                
                # Display job info
                job_info = client.get_job_info()
                if job_info:
                    print_job_info(job_info)
                else:
                    console.print("[yellow]Could not retrieve job information[/yellow]")
                
                return 0
            else:
                console.print("[yellow]Server not responding, starting new server...[/yellow]")
                # Backup old config
                backup_path = config_file.with_suffix(f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}")
                config_file.rename(backup_path)
                console.print(f"[yellow]Backed up old config to {backup_path}[/yellow]")
    
    # 2. Set up file monitoring
    console.print(f"[cyan]Setting up monitoring for mgapi_config.json...[/cyan]")
    handler = ConfigFileHandler()
    observer = Observer()
    observer.schedule(handler, ".", recursive=False)
    observer.start()
    
    # 3. Start server
    console.print(f"[bold]Starting server with command:[/bold] {command}")
    
    try:
        process = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        console.print(f"[green]✓ Server process started (PID: {process.pid})[/green]")
        
    except Exception as e:
        console.print(f"[red]Failed to start server: {e}[/red]")
        observer.stop()
        observer.join()
        return 1
    
    # 4. Monitor for server readiness
    console.print(f"[cyan]Monitoring for server readiness (timeout: {timeout}s)...[/cyan]")
    
    start_time = time.time()
    last_check = 0
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%")
    ) as progress:
        task = progress.add_task("Waiting for server...", total=timeout)
        
        while time.time() - start_time < timeout:
            elapsed = time.time() - start_time
            progress.update(task, completed=elapsed)
            
            # Check if config file was updated
            if handler.config_updated and handler.config_data:
                url = handler.config_data.get("mgapi_url")
                if url:
                    console.print(f"\n[cyan]Testing connection to {url}...[/cyan]")
                    
                    client = MGAPIClient(url)
                    if client.check_health():
                        console.print(f"[green]✓ Server is ready at {url}[/green]")
                        
                        # Get and display job info
                        job_info = client.get_job_info()
                        if job_info:
                            print_job_info(job_info)
                        else:
                            # Use config data as fallback
                            fallback_info = {
                                "job_id": handler.config_data.get("bjob_id", "N/A"),
                                "status": "Running",
                                "host": "N/A",
                                "queue": "N/A"
                            }
                            print_job_info(fallback_info)
                        
                        observer.stop()
                        observer.join()
                        return 0
                    else:
                        console.print("[yellow]Server not ready yet, continuing to monitor...[/yellow]")
                        handler.config_updated = False  # Reset flag
            
            # Check process status
            if process.poll() is not None:
                console.print(f"\n[red]Server process terminated with code: {process.returncode}[/red]")
                
                # Show error output
                try:
                    stdout, stderr = process.communicate(timeout=1)
                    if stderr:
                        console.print(f"[red]Error output:[/red]\n{stderr}")
                    if stdout:
                        console.print(f"[yellow]Output:[/yellow]\n{stdout}")
                except subprocess.TimeoutExpired:
                    pass
                
                observer.stop()
                observer.join()
                return 1
            
            time.sleep(1)
    
    # Timeout reached
    observer.stop()
    observer.join()
    console.print(f"\n[red]Timeout: Server did not start within {timeout} seconds[/red]")
    
    # Terminate process
    if process.poll() is None:
        console.print("[yellow]Terminating server process...[/yellow]")
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            console.print("[red]Process did not terminate gracefully, killing...[/red]")
            process.kill()
            process.wait()
    
    return 1