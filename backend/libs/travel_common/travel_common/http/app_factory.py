"""Build a FastAPI app the same way in every service.

CORS, the domain-error handlers and the versioned router prefix are the
same everywhere; only the routers and the settings differ.
"""

from collections.abc import Sequence

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from travel_common.config import CommonSettings
from travel_common.http.error_handlers import register_error_handlers


def create_app(settings: CommonSettings, routers: Sequence[APIRouter]) -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )

    # CORS middleware must be registered before routers.
    # allow_credentials=True requires explicit origins (never "*").
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_error_handlers(app)
    for router in routers:
        app.include_router(router, prefix=settings.API_V1_STR)
    return app
