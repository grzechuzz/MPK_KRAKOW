from collections.abc import Generator

from sqlalchemy.orm import Session

from app.common.db.connection import get_session


def get_db() -> Generator[Session]:
    with get_session() as session:
        yield session
