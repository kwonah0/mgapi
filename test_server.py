#!/usr/bin/env python3
"""
Mock MGAPI Server for Testing

This server mimics the behavior of a real TCL MGAPI server for testing purposes.
It provides all the expected endpoints and creates mgapi_config.json automatically.
"""

import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn


class QueryRequest(BaseModel):
    """Request model for /execute endpoint."""
    query: str


class QueryResponse(BaseModel):
    """Response model for /execute endpoint."""
    exit_code: int = 0
    message: str = ""
    result: dict = None
    timestamp: str = None


app = FastAPI(
    title="Mock MGAPI Server",
    description="Test server that mimics TCL MGAPI server behavior",
    version="1.0.0"
)

# Mock job information
MOCK_JOB_INFO = {
    "job_id": "12345",
    "status": "RUN",
    "host": "test-node-001",
    "queue": "normal",
    "submit_time": "2024-01-01 10:00:00",
    "start_time": "2024-01-01 10:01:00",
    "cpu_time": "00:15:30",
    "memory": "2.5GB",
    "extra": {
        "user": "testuser",
        "project": "test_project",
        "exec_host": "test-node-001"
    }
}


@app.on_event("startup")
async def startup_event():
    """Create mgapi_config.json on server startup."""
    # Wait a moment to simulate server initialization
    time.sleep(1)
    
    # Get server info from uvicorn
    host = getattr(app, 'host', 'localhost')
    port = getattr(app, 'port', 8000)
    
    config = {
        "mgapi_url": f"http://{host}:{port}",
        "bjob_id": MOCK_JOB_INFO["job_id"]
    }
    
    config_file = Path("mgapi_config.json")
    with open(config_file, 'w') as f:
        json.dump(config, f, indent=2)
    
    print(f"✓ Created {config_file}")
    print(f"✓ Mock server ready at http://{host}:{port}")


@app.on_event("shutdown") 
async def shutdown_event():
    """Clean up on server shutdown."""
    config_file = Path("mgapi_config.json")
    if config_file.exists():
        config_file.unlink()
        print("✓ Cleaned up mgapi_config.json")


@app.get("/")
async def root():
    """API information and endpoints."""
    return {
        "message": "Mock MGAPI Server v1.0.0",
        "timestamp": datetime.now().isoformat(),
        "endpoints": {
            "/": "API information and endpoints list",
            "/health": "Health check endpoint",
            "/job_info": "Get LSF job information",
            "/execute": "Execute queries and commands"
        },
        "version": "1.0.0"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0"
    }


@app.get("/job_info")
async def get_job_info():
    """Get LSF job information."""
    return MOCK_JOB_INFO


@app.post("/execute")
async def execute_query(request: QueryRequest):
    """Execute a query and return mock results."""
    query = request.query.strip().lower()
    timestamp = datetime.now().isoformat()
    
    # Handle different query types
    if query == "ping":
        return QueryResponse(
            exit_code=0,
            message="pong",
            result={"response": "pong"},
            timestamp=timestamp
        )
    
    elif query.startswith("echo "):
        echo_text = request.query[5:]  # Remove "echo " prefix
        return QueryResponse(
            exit_code=0,
            message=echo_text,
            result={"echo": echo_text},
            timestamp=timestamp
        )
    
    elif query == "status":
        return QueryResponse(
            exit_code=0,
            message="Server status retrieved",
            result={
                "server": "running",
                "environment": "test",
                "uptime": "00:15:30",
                "connections": 1
            },
            timestamp=timestamp
        )
    
    elif query == "error":
        # Simulate server error
        return QueryResponse(
            exit_code=1,
            message="Simulated server error",
            result=None,
            timestamp=timestamp
        )
    
    elif query == "timeout":
        # Simulate timeout
        time.sleep(5)
        return QueryResponse(
            exit_code=0,
            message="Delayed response",
            result={"delay": "5 seconds"},
            timestamp=timestamp
        )
    
    # Handle JSON queries (from batch processing)
    try:
        query_data = json.loads(request.query)
        tool = query_data.get("tool")
        action = query_data.get("action")
        params = query_data.get("params", {})
        
        if tool == "user_manager":
            return handle_user_manager(action, params, timestamp)
        elif tool == "config_manager":
            return handle_config_manager(action, params, timestamp)
        else:
            return QueryResponse(
                exit_code=1,
                message=f"Unknown tool: {tool}",
                timestamp=timestamp
            )
    
    except json.JSONDecodeError:
        # Handle as plain text query
        return QueryResponse(
            exit_code=0,
            message=f"Processed query: {request.query}",
            result={"query": request.query, "type": "text"},
            timestamp=timestamp
        )


def handle_user_manager(action: str, params: dict, timestamp: str) -> QueryResponse:
    """Handle user management operations."""
    username = params.get("username", "unknown")
    
    if action == "create":
        email = params.get("email", "")
        # Simulate email validation
        if "@" not in email:
            return QueryResponse(
                exit_code=2,
                message=f"Invalid email format: {email}",
                timestamp=timestamp
            )
        
        return QueryResponse(
            exit_code=0,
            message=f"User '{username}' created successfully",
            result={"username": username, "action": "created"},
            timestamp=timestamp
        )
    
    elif action == "update":
        updates = params.get("updates", {})
        return QueryResponse(
            exit_code=0,
            message=f"User '{username}' updated successfully",
            result={"username": username, "action": "updated", "updates": updates},
            timestamp=timestamp
        )
    
    elif action == "delete":
        # Simulate some users not found
        if username == "nonexistent":
            return QueryResponse(
                exit_code=1,
                message=f"User '{username}' not found",
                timestamp=timestamp
            )
        
        return QueryResponse(
            exit_code=0,
            message=f"User '{username}' deleted successfully",
            result={"username": username, "action": "deleted"},
            timestamp=timestamp
        )
    
    else:
        return QueryResponse(
            exit_code=1,
            message=f"Unknown action: {action}",
            timestamp=timestamp
        )


def handle_config_manager(action: str, params: dict, timestamp: str) -> QueryResponse:
    """Handle configuration management operations."""
    component = params.get("component", "unknown")
    key = params.get("key", "unknown")
    environment = params.get("environment", "unknown")
    
    if action == "set":
        value = params.get("value")
        return QueryResponse(
            exit_code=0,
            message=f"Config {component}.{key} set in {environment}",
            result={
                "component": component,
                "key": key,
                "value": value,
                "environment": environment,
                "action": "set"
            },
            timestamp=timestamp
        )
    
    elif action == "get":
        # Simulate getting config value
        return QueryResponse(
            exit_code=0,
            message=f"Config {component}.{key} retrieved from {environment}",
            result={
                "component": component,
                "key": key,
                "value": "mock_value",
                "environment": environment,
                "action": "get"
            },
            timestamp=timestamp
        )
    
    elif action == "delete":
        return QueryResponse(
            exit_code=0,
            message=f"Config {component}.{key} deleted from {environment}",
            result={
                "component": component,
                "key": key,
                "environment": environment,
                "action": "deleted"
            },
            timestamp=timestamp
        )
    
    else:
        return QueryResponse(
            exit_code=1,
            message=f"Unknown action: {action}",
            timestamp=timestamp
        )


def main():
    """Run the mock server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Mock MGAPI Server for Testing")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    
    args = parser.parse_args()
    
    # Store host and port in app for startup event
    app.host = args.host
    app.port = args.port
    
    print(f"Starting Mock MGAPI Server...")
    print(f"Host: {args.host}")
    print(f"Port: {args.port}")
    print(f"Swagger UI: http://{args.host}:{args.port}/docs")
    print()
    
    try:
        uvicorn.run(
            "test_server:app",
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\nServer stopped.")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()