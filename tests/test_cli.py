"""Tests for CLI main entry point."""

import pytest
from click.testing import CliRunner

from mgapi.cli import cli


def test_cli_version(cli_runner):
    """Test version command."""
    result = cli_runner.invoke(cli, ['version'])
    assert result.exit_code == 0
    assert "MGAPI version" in result.output


def test_cli_help(cli_runner):
    """Test help output."""
    result = cli_runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "MGAPI - CLI tool" in result.output
    assert "status" in result.output
    assert "start" in result.output
    assert "close" in result.output
    assert "send" in result.output
    assert "endpoints" in result.output


def test_cli_config_command(cli_runner, tmp_path, monkeypatch):
    """Test config command."""
    # Use Click's isolated filesystem to completely isolate the test
    with cli_runner.isolated_filesystem():
        # Test when no config files exist and user cancels creation
        result = cli_runner.invoke(cli, ['config'], input='n\n')
        print(f"Exit code: {result.exit_code}")
        print(f"Output: {repr(result.output)}")
        assert result.exit_code == 1  # Click abort gives exit code 1
        assert "No configuration files found" in result.output

        # Test when user creates default config
        result = cli_runner.invoke(cli, ['config'], input='y\n')
        assert result.exit_code == 0
        assert "Created default settings.toml" in result.output
        import os
        assert os.path.exists("settings.toml")

        # Test when config file already exists
        result = cli_runner.invoke(cli, ['config'])
        assert result.exit_code == 0
        assert "Found configuration files:" in result.output


def test_cli_with_custom_config(cli_runner, temp_config_file):
    """Test CLI with custom config file."""
    result = cli_runner.invoke(cli, ['--config', temp_config_file, 'version'])
    assert result.exit_code == 0


def test_cli_with_environment(cli_runner):
    """Test CLI with environment option."""
    result = cli_runner.invoke(cli, ['--env', 'production', 'version'])
    assert result.exit_code == 0


def test_cli_verbose_mode(cli_runner):
    """Test CLI with verbose mode."""
    result = cli_runner.invoke(cli, ['--verbose', 'version'])
    assert result.exit_code == 0