from datetime import date

import msgspec
import redis

from app.common.constants import DEFAULT_TTL, LONG_TTL
from app.common.redis.connection import get_client


def _ttl(start_date: date, end_date: date) -> int:
    span = (end_date - start_date).days
    return LONG_TTL if span >= 7 else DEFAULT_TTL


def _key(endpoint: str, line_number: str, start_date: date, end_date: date) -> str:
    return f"stats:{endpoint}:{line_number}:{start_date}:{end_date}"


def get_cached(endpoint: str, line_number: str, start_date: date, end_date: date) -> bytes | None:
    try:
        client = get_client()
        return client.get(_key(endpoint, line_number, start_date, end_date))  # type: ignore
    except redis.RedisError:
        return None


def set_cached(endpoint: str, line_number: str, start_date: date, end_date: date, data: msgspec.Struct) -> bytes:
    raw = msgspec.json.encode(data)
    try:
        client = get_client()
        client.setex(_key(endpoint, line_number, start_date, end_date), _ttl(start_date, end_date), raw)
    except redis.RedisError:
        pass
    return raw
