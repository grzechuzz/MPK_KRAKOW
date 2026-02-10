from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.response import MsgspecJSONResponse
from app.api.stats import router
from app.common.db.connection import get_engine


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    get_engine()
    yield
    get_engine().dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title="MPK Kraków API",
        version="0.1.0",
        description="Public API for Kraków public transport delay statistics",
        default_response_class=MsgspecJSONResponse,
        lifespan=lifespan,
    )

    app.include_router(router, prefix="/api/v1")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


mpk_app = create_app()
