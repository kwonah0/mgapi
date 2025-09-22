"""Output formatting utilities."""

import json
from typing import Any, Dict, Optional

import yaml
from colorama import Fore, Style, init

# Initialize colorama
init(autoreset=True)


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
        print(f"{Fore.GREEN}✓ Server is running{Style.RESET_ALL}")
        print(f"URL: {url}")
    else:
        print(f"{Fore.RED}✗ Server is not responding{Style.RESET_ALL}")
        print(f"URL: {url}")


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

    print(f"{Fore.CYAN}{title}{Style.RESET_ALL}")
    print("-" * len(title))

    if isinstance(config, dict):
        json_str = json.dumps(config, indent=2)
        print(json_str)
    else:
        print(str(config))


def print_error(message: str, suggestion: Optional[str] = None) -> None:
    """Print an error message with optional suggestion.

    Args:
        message: Error message
        suggestion: Optional suggestion for fixing the error
    """
    print(f"{Fore.RED}Error: {message}{Style.RESET_ALL}")
    if suggestion:
        print(f"{Fore.YELLOW}Suggestion: {suggestion}{Style.RESET_ALL}")


def print_success(message: str) -> None:
    """Print a success message.

    Args:
        message: Success message
    """
    print(f"{Fore.GREEN}✓ {message}{Style.RESET_ALL}")


def print_job_info(job_info: Dict[str, Any]) -> None:
    """Print job information in a formatted way.

    Args:
        job_info: Job information dictionary
    """
    print(f"{Fore.CYAN}Server Information{Style.RESET_ALL}")
    print("=" * 20)

    print(f"Job ID: {job_info.get('job_id', 'N/A')}")
    print(f"Status: {job_info.get('status', 'Unknown')}")
    print(f"Host: {job_info.get('host', 'N/A')}")
    print(f"Queue: {job_info.get('queue', 'N/A')}")
    print(f"Submit Time: {job_info.get('submit_time', 'N/A')}")
    print(f"Start Time: {job_info.get('start_time', 'N/A')}")
    print(f"CPU Time: {job_info.get('cpu_time', 'N/A')}")
    print(f"Memory: {job_info.get('memory', 'N/A')}")

    extra = job_info.get('extra', {})
    if extra:
        print(f"\nAdditional Info:")
        print(json.dumps(extra, indent=2))


def print_query_result(result: Dict[str, Any]) -> None:
    """Print query result in a formatted way.

    Args:
        result: Query result dictionary
    """
    if "error" in result:
        print_error(f"Query execution failed: {result['error']}")
    else:
        print(f"{Fore.CYAN}Query Result{Style.RESET_ALL}")
        print("-" * 12)
        print(str(result.get("result", result)))
        print_success("Query executed successfully")