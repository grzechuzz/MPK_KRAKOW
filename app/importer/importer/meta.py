from sqlalchemy import text
from sqlalchemy.engine import Connection


def get_current_static_hash(conn: Connection) -> str | None:
    """
    Returns current static hash from gtfs_meta (id=1),
    or None if not set yet.
    """
    return conn.execute(
        text("SELECT current_hash FROM gtfs_meta WHERE id = 1")
    ).scalar_one_or_none()


def set_current_static_hash(conn: Connection, new_hash: str) -> None:
    """
    Inserts or updates current static hash in gtfs_meta (id=1).
    """
    conn.execute(
        text(
            """
            INSERT INTO gtfs_meta (id, current_hash)
            VALUES (1, :h) ON CONFLICT (id) DO
            UPDATE
                SET current_hash = EXCLUDED.current_hash,
                updated_at = now()
            """
        ),
        {"h": new_hash},
    )
