"""Tests for status command."""

import pytest
from unittest.mock import patch, Mock

from mgapi.cli import cli


def test_status_command_healthy(cli_runner):
    """Test status command when server is healthy."""
    with patch('mgapi.commands.status.check_server_status') as mock_check:
        mock_check.return_value = {
            "status": "running",
            "url": "http://localhost:8000",
            "healthy": True,
            "job_info": {"job_id": "12345"}
        }

        result = cli_runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        mock_check.assert_called_once()


def test_status_command_unhealthy(cli_runner):
    """Test status command when server is not responding."""
    with patch('mgapi.commands.status.check_server_status') as mock_check:
        mock_check.return_value = {
            "status": "not_responding",
            "url": "http://localhost:8000",
            "healthy": False
        }

        result = cli_runner.invoke(cli, ['status'])
        assert result.exit_code == 1
        mock_check.assert_called_once()