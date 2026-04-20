from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.uploads import router as uploads_router
from app.core.config import settings


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        description="Inalyze ingestion and validation API",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_allowed_origins),
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
    )
    app.include_router(uploads_router, prefix=settings.api_v1_prefix)
    return app


app = create_app()
