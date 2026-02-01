from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from endpoints.user import router as user_router
from endpoints.item import router as item_router
from endpoints.pickup import router as pickup_router
from endpoints.storage import router as storage_router
from endpoints.dropoff import router as dropoff_router
from endpoints.pickuprequests import router as pickup_requests_router
from endpoints.default import router as default_router

from .database import engine, Base
from .logging_config import logger
from .config import settings
from .middleware.error_handler import error_handler_middleware
from .middleware.request_id import request_id_middleware

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version
)

# Add custom middleware
app.middleware("http")(request_id_middleware)
app.middleware("http")(error_handler_middleware)

# Configure CORS (restricted for security)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)

# Include routers
app.include_router(default_router)
app.include_router(user_router)
app.include_router(item_router)
app.include_router(pickup_router)
app.include_router(storage_router)
app.include_router(dropoff_router)
app.include_router(pickup_requests_router)

Base.metadata.create_all(bind=engine)

logger.info(f"Started {settings.app_name} v{settings.app_version}")
logger.info(f"CORS origins: {settings.cors_origins}")
