from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api.v1.routers.government import (
    filings,
    bills,
    contracts,
    lobbying,
)

from app.api.v1.routers.market import market_router
from app.api.v1.routers.fundamentals import fundamentals


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs on startup and shutdown.
    Good place for DB connection checks,
    cache warming, and cleanup.
    """
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    print(f"Environment: {settings.ENVIRONMENT}")
    print(f"Database: {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Argos — Global Financial Intelligence Terminal API",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS — allows the React frontend to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_HOSTS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check — used by Docker and AWS ECS
# to verify the API is running
@app.get("/health", tags=["Health"])
async def health() -> JSONResponse:
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "environment": settings.ENVIRONMENT,
        }
    )


# Mount all government routers
app.include_router(
    filings.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    bills.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    contracts.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    lobbying.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    market_router.router,
    prefix=settings.API_V1_PREFIX,
)
app.include_router(
    fundamentals.router,
    prefix=settings.API_V1_PREFIX,
)