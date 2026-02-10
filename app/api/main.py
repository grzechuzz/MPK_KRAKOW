from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import msgspec
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.common.db.connection import get_engine


class MsgspecJSONResponse(JSONResponse):
    def render(self, content: Any) -> bytes:
        return msgspec.json.encode(content)


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

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


mpk_app = create_app()
