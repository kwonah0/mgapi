"""FastAPI server implementation for MGAPI."""

import os
import subprocess
from datetime import datetime
from typing import Dict, Any, Optional

from fastapi import FastAPI, HTTPException, status
from fastapi_offline import FastAPIOffline
from pydantic import BaseModel, Field

from .config import settings
from .utils.logger import logger


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(description="Server status")
    timestamp: datetime = Field(description="Current server time")
    version: str = Field(description="Server version")


class JobIDResponse(BaseModel):
    """LSF Job ID response model."""
    job_id: Optional[str] = Field(description="LSF Job ID if available")
    message: str = Field(description="Status message")


class QueryRequest(BaseModel):
    """Query request model."""
    query: str = Field(description="Query to execute", min_length=1)


class QueryResponse(BaseModel):
    """Query response model."""
    query: str = Field(description="Original query")
    result: Optional[Any] = Field(description="Query result")
    error: Optional[str] = Field(description="Error message if failed")
    timestamp: datetime = Field(description="Execution timestamp")


app = FastAPIOffline(
    title="MGAPI Server",
    description="API server for MGAPI operations",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.on_event("startup")
async def startup_event():
    """Log server startup."""
    logger.info("MGAPI server starting up")
    logger.info(f"Environment: {settings.current_env}")


@app.on_event("shutdown")
async def shutdown_event():
    """Log server shutdown."""
    logger.info("MGAPI server shutting down")


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check if the server is healthy."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now(),
        version="0.1.0"
    )


@app.get("/bjobid", response_model=JobIDResponse)
async def get_bjobid():
    """Get the LSF job ID if running under LSF."""
    job_id = os.environ.get("LSB_JOBID")
    
    if not job_id:
        try:
            result = subprocess.run(
                ["bjobs", "-o", "jobid", "-noheader"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.strip().split("\n")
                if lines:
                    job_id = lines[0].strip()
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            logger.warning(f"Failed to get job ID: {e}")
    
    if job_id:
        return JobIDResponse(
            job_id=job_id,
            message="Job ID retrieved successfully"
        )
    else:
        return JobIDResponse(
            job_id=None,
            message="Not running under LSF or job ID not available"
        )


@app.post("/execute", response_model=QueryResponse)
async def execute_query(request: QueryRequest):
    """Execute a query and return the result."""
    logger.info(f"Executing query: {request.query[:100]}...")
    
    try:
        result = process_query(request.query)
        
        return QueryResponse(
            query=request.query,
            result=result,
            error=None,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Query execution failed: {e}")
        return QueryResponse(
            query=request.query,
            result=None,
            error=str(e),
            timestamp=datetime.now()
        )


def process_query(query: str) -> Any:
    """Process the query and return results.
    
    This is a placeholder implementation. Replace with actual query processing logic.
    
    Args:
        query: Query string to process
        
    Returns:
        Query result
    """
    query_lower = query.lower().strip()
    
    if query_lower == "ping":
        return "pong"
    elif query_lower.startswith("echo "):
        return query[5:]
    elif query_lower == "status":
        return {
            "server": "running",
            "environment": settings.current_env,
            "config": {
                "mgapi_url": settings.get("mgapi_url"),
                "server_port": settings.get("server_port"),
            }
        }
    else:
        return f"Query processed: {query}"


if __name__ == "__main__":
    import uvicorn
    from .config import get_server_config
    
    config = get_server_config()
    uvicorn.run(
        app,
        host=config["host"],
        port=config["port"],
        log_level="info"
    )