from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.api import api_router  
from app.core.config import settings
from app.api.endpoints.errors import http_exception_handler
from app.services.auth_service import verify_access_token
import logging

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Initialize FastAPI app
app = FastAPI(title=settings.APP_NAME, version="1.0")

# CORS Middleware (Allow frontend access if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(Exception, http_exception_handler)

logger.info(" Application startup successful!")

# List of public endpoints (should NOT require authentication)
EXCLUDED_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/users/create",  
    "/docs",  
    "/redoc",  
    "/openapi.json",
    "/"
]

@app.middleware("http")
async def check_authentication_middleware(request: Request, call_next):
    """Middleware to enforce authentication globally except for login, user creation, and API documentation."""
    path = request.url.path

    # Allow access to public endpoints
    if any(path.startswith(excluded) for excluded in EXCLUDED_PATHS):
        return await call_next(request)

    # Check for authentication token in headers
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f" Unauthorized access attempt to {path}")  # Log failed authentication
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid authentication token"})

    # Extract the token (remove "Bearer " prefix)
    token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
    if not token:
        logger.warning(f" Invalid token format for {path}")
        return JSONResponse(status_code=401, content={"detail": "Invalid token format"})

    # Verify access token
    try:
        _ = await verify_access_token(token)
    except Exception as e:
        logger.warning(f" Invalid token for {path}: {str(e)}")  # Log token failures
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    logger.info(f" Authorized access to {path}")
    return await call_next(request)

# Include API routers
app.include_router(api_router, prefix="/api/v1")  

@app.get("/")
def root():
    """Public API endpoint."""
    return {"message": "Welcome to the Health Management Assistant API!"}
