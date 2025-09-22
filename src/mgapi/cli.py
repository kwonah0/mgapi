"""Main CLI entry point for MGAPI."""

import sys

import click
from colorama import Fore, Style

from . import __version__
from .commands.status import status
from .commands.start import start
from .commands.close import close
from .commands.send import send
from .commands.endpoints import endpoints



@click.group()
@click.version_option(version=__version__, prog_name="mgapi")
@click.option(
    "--config",
    "-c",
    envvar="MGAPI_CONFIG",
    help="Path to configuration file",
)
@click.option(
    "--env",
    "-e",
    envvar="MGAPI_ENV",
    help="Environment to use (e.g., development, production)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.pass_context
def cli(ctx, config, env, verbose):
    """MGAPI - CLI tool for managing and interacting with MGAPI server."""
    ctx.ensure_object(dict)
    
    if config:
        import os
        os.environ["MGAPI_SETTINGS_FILE"] = config
    
    if env:
        import os
        os.environ["ENV_FOR_DYNACONF"] = env
    
    if verbose:
        import os
        os.environ["MGAPI_LOG_LEVEL"] = "DEBUG"
        from .utils.logger import setup_logger
        setup_logger(level="DEBUG")


cli.add_command(status)
cli.add_command(start)
cli.add_command(close)
cli.add_command(send)
cli.add_command(endpoints)


@cli.command()
def version():
    """Show the version of MGAPI."""
    print(f"MGAPI version {__version__}")


@cli.command()
@click.pass_context
def config(ctx):
    """Initialize or validate configuration."""
    from pathlib import Path
    from .utils.formatters import print_success, print_error
    
    config_files = ["settings.toml", "mgapi_config.json", ".env"]
    found_files = []
    
    for file in config_files:
        if Path(file).exists():
            found_files.append(file)
    
    if found_files:
        print_success(f"Found configuration files: {', '.join(found_files)}")
        ctx.exit(0)
    else:
        print_error(
            "No configuration files found",
            "Create settings.toml, mgapi_config.json, or .env file"
        )
        
        create = click.confirm("Would you like to create a default settings.toml?")
        if create:
            default_config = """[default]
# Logging settings
log_level = "INFO"
log_file = "logs/mgapi.log"

# API client settings
timeout = 30
retry_count = 3
retry_delay = 1

# Output settings
output_format = "rich"  # rich, json, yaml, plain

[development]
log_level = "DEBUG"

[production]
log_level = "WARNING"
"""
            Path("settings.toml").write_text(default_config)
            print_success("Created default settings.toml")
            ctx.exit(0)
        else:
            ctx.exit(1)


def main():
    """Main entry point for the CLI."""
    try:
        sys.exit(cli())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Interrupted by user{Style.RESET_ALL}")
        sys.exit(1)
    except Exception as e:
        print(f"{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()