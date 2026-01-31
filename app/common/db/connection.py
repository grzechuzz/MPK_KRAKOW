from collections.abc import Generator
from contextlib import contextmanager
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.common.config import get_config


@lru_cache(maxsize=1)
def get_engine() -> Engine:
    config = get_config()

    return create_engine(
        config.database.url,
        pool_pre_ping=True,
        pool_size=5,
        max_overflow=10,
        echo=False,
    )


@lru_cache(maxsize=1)
def get_session_factory() -> sessionmaker[Session]:
    return sessionmaker(bind=get_engine(), expire_on_commit=False)


@contextmanager
def get_session() -> Generator[Session]:
    factory = get_session_factory()
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
