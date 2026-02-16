from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.controllers.shapes_controller import router as shapes_router
from app.api.controllers.stats_controller import router as stats_router
from app.api.controllers.vehicles_controller import router as vehicles_router
from app.api.exceptions import setup_exception_handlers
from app.api.middleware import setup_middleware
from app.api.response import MsgspecJSONResponse
from app.common.db.connection import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_engine()
    yield
    get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="KRKtransit API",
        version="0.1.0",
        description="Public API for Kraków public transport delay statistics",
        default_response_class=MsgspecJSONResponse,
        lifespan=lifespan,
    )

    setup_middleware(app)
    setup_exception_handlers(app)

    app.include_router(stats_router, prefix="/v1")
    app.include_router(vehicles_router, prefix="/v1")
    app.include_router(shapes_router, prefix="/v1")

    return app


mpk_app = create_app()
