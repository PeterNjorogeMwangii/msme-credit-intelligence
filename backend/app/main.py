from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.config import settings


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Backend API for MSME customer intelligence, "
        "credit assessment and portfolio risk monitoring."
    ),
    debug=settings.app_debug,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.api_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    api_router,
    prefix=settings.api_v1_prefix,
)


@app.get(
    "/",
    tags=["Root"],
    summary="API information",
)
def root() -> dict:
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.app_environment,
        "documentation": "/docs",
        "health": (
            f"{settings.api_v1_prefix}/health"
        ),
    }