"""Pytest configuration and fixtures."""

import os
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from click.testing import CliRunner
from fastapi.testclient import TestClient


@pytest.fixture
def cli_runner():
    """Create a Click CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def temp_config_file():
    """Create a temporary configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.toml', delete=False) as f:
        f.write("""
[default]
mgapi_url = "http://test-server:8000"
server_host = "127.0.0.1"
server_port = 8001
log_level = "DEBUG"
        """)
        temp_path = f.name
    
    yield temp_path
    
    os.unlink(temp_path)


@pytest.fixture
def mock_settings():
    """Mock dynaconf settings."""
    with patch('mgapi.config.settings') as mock:
        mock.get.return_value = "http://test-server:8000"
        mock.to_dict.return_value = {
            "mgapi_url": "http://test-server:8000",
            "server_host": "127.0.0.1",
            "server_port": 8001,
        }
        yield mock


@pytest.fixture
def mock_api_client():
    """Mock API client."""
    with patch('mgapi.core.client.MGAPIClient') as mock_class:
        mock_instance = Mock()
        mock_class.return_value = mock_instance

        mock_instance.check_health.return_value = True
        mock_instance.get_bjobid.return_value = "12345"
        mock_instance.execute_query.return_value = {"result": "success"}

        yield mock_instance


@pytest.fixture
def test_client():
    """Create a test client for FastAPI app."""
    from mgapi.server import app
    return TestClient(app)


@pytest.fixture
def mock_httpx_client():
    """Mock httpx async client."""
    with patch('mgapi.core.client.httpx.AsyncClient') as mock_class:
        mock_instance = Mock()
        mock_class.return_value.__aenter__.return_value = mock_instance

        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_response.content = b'{"status": "ok"}'
        mock_response.raise_for_status = Mock()

        mock_instance.request.return_value = mock_response

        yield mock_instance