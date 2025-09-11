"""Tests for status command."""

import pytest
from unittest.mock import patch, Mock

from mgapi.cli import cli


def test_status_command_healthy(cli_runner):
    """Test status command when server is healthy."""
    with patch('mgapi.commands.status.MGAPIClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.check_health.return_value = True
        
        result = cli_runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        mock_client.check_health.assert_called_once()


def test_status_command_unhealthy(cli_runner):
    """Test status command when server is not responding."""
    with patch('mgapi.commands.status.MGAPIClient') as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        mock_client.check_health.return_value = False
        
        result = cli_runner.invoke(cli, ['status'])
        assert result.exit_code == 1
        mock_client.check_health.assert_called_once()