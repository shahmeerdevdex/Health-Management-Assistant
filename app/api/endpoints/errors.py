from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
import logging

logger = logging.getLogger("errors")

async def http_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, HTTPException):
        return JSONResponse(status_code=exc.status_code, content={"error": exc.detail})
    return JSONResponse(status_code=500, content={"error": "Internal Server Error"})
async def validation_exception_handler(request: Request, exc):
    """Handle validation errors from Pydantic."""
    return await JSONResponse(status_code=422, content={"error": "Validation error", "details": exc.errors()})

async def sqlalchemy_exception_handler(request: Request, exc: IntegrityError):
    """Handle database integrity errors."""
    logger.error(f"Database error: {str(exc)}")
    return await JSONResponse(status_code=400, content={"error": "Database integrity error"})
