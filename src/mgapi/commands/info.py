"""Info command implementation."""

import click

from ..config import get_config_value
from ..utils.formatters import print_config, print_error
from ..utils.validators import validate_keypath
from ..utils.logger import logger


@click.command()
@click.argument("keypath", required=False)
@click.option(
    "--format",
    "-f",
    type=click.Choice(["rich", "json", "yaml", "plain"]),
    default="rich",
    help="Output format",
)
def info(keypath: str, format: str):
    """Show configuration information.
    
    If KEYPATH is provided, shows the value at that path.
    Otherwise, shows the entire configuration.
    """
    if keypath and not validate_keypath(keypath):
        print_error(
            f"Invalid keypath: {keypath}",
            "Use dot notation like 'server.host' or 'mgapi_url'"
        )
        return 1
    
    logger.info(f"Getting config {'for ' + keypath if keypath else 'all'}")
    
    config_value = get_config_value(keypath)
    
    if config_value is None and keypath:
        print_error(f"Key '{keypath}' not found in configuration")
        return 1
    
    if format == "rich":
        print_config(config_value, keypath)
    else:
        from ..utils.formatters import format_output
        output = format_output(config_value, format)
        click.echo(output)
    
    return 0