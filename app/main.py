from fastapi import FastAPI, Request, Depends
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints.api import api_router  
from app.core.config import settings
from app.api.endpoints.errors import http_exception_handler
from app.services.auth_service import verify_access_token
from fastapi.security import OAuth2PasswordBearer
from app.crud.subscription import save_sub_plan_to_db
import stripe
from app.db.session import engine  
from contextlib import asynccontextmanager
import logging
from app.db.session import SessionLocal


oauth2_scheme = OAuth2PasswordBearer(tokenUrl=settings.TOKEN_URL)  
stripe.api_key = settings.STRIPE_SECRET_KEY

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("main")

# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with SessionLocal() as session:
            # Fetch Stripe products (blocking call)
            products = stripe.Product.list(active=True, limit=100)
            for product in products.auto_paging_iter():
                prices = stripe.Price.list(product=product.id, active=True)
                for price in prices.auto_paging_iter():
                    if price.currency != "usd":
                        continue
                    await save_sub_plan_to_db(
                        db=session,
                        name=product.name,
                        description=product.get("description", ""),
                        stripe_product_id=product.id,
                        stripe_price_id=price.id,
                        amount=price.unit_amount,
                        currency=price.currency
                    )
        logger.info("Stripe products synced during app startup.")
        
    except Exception as e:
        logger.error(f"Startup error while syncing Stripe products: {e}")
    yield
    await engine.dispose()

# Single app instance with lifespan
app = FastAPI(title=settings.APP_NAME, version="1.0", lifespan=lifespan)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
app.add_exception_handler(Exception, http_exception_handler)
logger.info("Application startup successful!")

# Public endpoints excluded from auth
EXCLUDED_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/users/create",  
    "/docs",  
    "/redoc",  
    "/openapi.json",
    "/"
]

# Middleware for token-based authentication
@app.middleware("http")
async def check_authentication_middleware(request: Request, call_next):
    path = request.url.path
    if request.method == "HEAD" or any(path.startswith(excluded) for excluded in EXCLUDED_PATHS):
        return await call_next(request)

    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        logger.warning(f"Unauthorized access attempt to {path}")
        return JSONResponse(status_code=401, content={"detail": "Missing or invalid authentication token"})

    token = auth_header.split(" ")[1] if len(auth_header.split(" ")) > 1 else None
    if not token:
        logger.warning(f"Invalid token format for {path}")
        return JSONResponse(status_code=401, content={"detail": "Invalid token format"})

    try:
        _ = await verify_access_token(token)
    except Exception as e:
        logger.warning(f"Invalid token for {path}: {str(e)}")
        return JSONResponse(status_code=401, content={"detail": "Invalid or expired token"})

    return await call_next(request)

# Include API routers
app.include_router(api_router)

@app.get("/")
def root():
    return {"message": "Welcome to the Health Management Assistant API!"}
