"""Configuration management using Dynaconf."""

import json
from pathlib import Path
from typing import Any, Optional

from dynaconf import Dynaconf

BASE_DIR = Path(__file__).parent.parent.parent

# Client-only settings
settings = Dynaconf(
    envvar_prefix="MGAPI",
    settings_files=[
        "settings.toml",
        ".secrets.toml",
    ],
    environments=True,
    load_dotenv=True,
    merge_enabled=True,
    root_path=BASE_DIR,
)


def get_config_value(keypath: Optional[str] = None) -> Any:
    """Get configuration value by keypath.
    
    Args:
        keypath: Dot-separated path to config value (e.g., "server.host")
        
    Returns:
        Configuration value or entire config if keypath is None
    """
    if keypath:
        try:
            value = settings
            for key in keypath.split("."):
                if hasattr(value, key):
                    value = getattr(value, key)
                else:
                    value = value.get(key)
            return value
        except (AttributeError, KeyError, TypeError):
            return None
    return settings.to_dict()


def get_server_info() -> dict:
    """Get server information from TCL server's mgapi_config.json.
    
    Returns:
        Server configuration dict or empty dict if file doesn't exist
    """
    config_file = Path("mgapi_config.json")
    if config_file.exists():
        try:
            with open(config_file) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}
    return {}


def get_mgapi_url() -> str:
    """Get the MGAPI server URL from TCL server's config or fallback.
    
    Returns:
        Server URL from mgapi_config.json or default
    """
    server_info = get_server_info()
    return server_info.get("mgapi_url", settings.get("mgapi_url", "http://localhost:8000"))


def get_bjob_id() -> Optional[str]:
    """Get the LSF job ID from TCL server's config.
    
    Returns:
        Job ID or None if not found
    """
    server_info = get_server_info()
    return server_info.get("bjob_id")


def get_client_config() -> dict:
    """Get client configuration."""
    return {
        "timeout": settings.get("timeout", 30),
        "retry_count": settings.get("retry_count", 3),
        "retry_delay": settings.get("retry_delay", 1),
        "log_level": settings.get("log_level", "INFO"),
        "log_file": settings.get("log_file", "logs/mgapi.log"),
        "output_format": settings.get("output_format", "rich"),
    }