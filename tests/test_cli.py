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
    assert "info" in result.output
    assert "start" in result.output
    assert "close" in result.output
    assert "send" in result.output


def test_cli_config_command(cli_runner, tmp_path, monkeypatch):
    """Test config command."""
    monkeypatch.chdir(tmp_path)
    
    result = cli_runner.invoke(cli, ['config'])
    assert result.exit_code == 0
    assert "No configuration files found" in result.output
    
    result = cli_runner.invoke(cli, ['config'], input='y\n')
    assert result.exit_code == 0
    assert "Created default settings.toml" in result.output
    assert (tmp_path / "settings.toml").exists()


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