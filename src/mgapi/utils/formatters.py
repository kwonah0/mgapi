"""Output formatting utilities."""

import json
from typing import Any, Dict, Optional

import yaml
from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

console = Console()


def format_output(
    data: Any,
    format_type: str = "rich",
    title: Optional[str] = None,
) -> str:
    """Format output data in various formats.
    
    Args:
        data: Data to format
        format_type: Output format (rich, json, yaml, plain)
        title: Optional title for the output
        
    Returns:
        Formatted string
    """
    if format_type == "json":
        return json.dumps(data, indent=2, ensure_ascii=False)
    
    elif format_type == "yaml":
        return yaml.dump(data, default_flow_style=False, allow_unicode=True)
    
    elif format_type == "plain":
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        return str(data)
    
    else:
        return data


def print_status(status: bool, url: str) -> None:
    """Print server status in a formatted way.
    
    Args:
        status: Server health status
        url: Server URL
    """
    if status:
        console.print(Panel(
            f"[green]✓ Server is running[/green]\n"
            f"URL: {url}",
            title="MGAPI Status",
            border_style="green",
        ))
    else:
        console.print(Panel(
            f"[red]✗ Server is not responding[/red]\n"
            f"URL: {url}",
            title="MGAPI Status",
            border_style="red",
        ))


def print_config(config: Dict[str, Any], keypath: Optional[str] = None) -> None:
    """Print configuration in a formatted way.
    
    Args:
        config: Configuration dictionary
        keypath: Optional keypath that was queried
    """
    if keypath:
        title = f"Configuration: {keypath}"
    else:
        title = "MGAPI Configuration"
    
    if isinstance(config, dict):
        json_str = json.dumps(config, indent=2)
        syntax = Syntax(json_str, "json", theme="monokai")
        console.print(Panel(syntax, title=title))
    else:
        console.print(Panel(str(config), title=title))


def print_error(message: str, suggestion: Optional[str] = None) -> None:
    """Print an error message with optional suggestion.
    
    Args:
        message: Error message
        suggestion: Optional suggestion for fixing the error
    """
    error_text = f"[red]Error: {message}[/red]"
    if suggestion:
        error_text += f"\n[yellow]Suggestion: {suggestion}[/yellow]"
    
    console.print(Panel(
        error_text,
        title="Error",
        border_style="red",
    ))


def print_success(message: str) -> None:
    """Print a success message.
    
    Args:
        message: Success message
    """
    console.print(f"[green]✓[/green] {message}")