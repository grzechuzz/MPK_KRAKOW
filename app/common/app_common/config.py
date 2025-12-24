import os
from pathlib import Path
from urllib.parse import quote_plus


def _read_text_file(path: str | Path) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8").strip()


def get_setting(name: str, default: str | None = None, required: bool = False) -> str | None:
    """
    Read config value from environment.

    Priority:
      1) ENV[NAME]
      2) ENV[NAME + "_FILE"] -> read file content
      3) default
    """
    val = os.environ.get(name)
    if val is not None and val != "":
        return val

    file_key = f"{name}_FILE"
    file_path = os.environ.get(file_key)
    if file_path:
        return _read_text_file(file_path)

    if default is not None:
        return default

    if required:
        raise RuntimeError(f"Missing required setting: {name} (or {name}_FILE)")

    return None


def build_database_url() -> str:
    host = get_setting("DB_HOST", default="gtfs_db")
    port = get_setting("DB_PORT", default="5432")
    name = get_setting("DB_NAME", default="test")
    user = get_setting("DB_USER", default="test")
    password = get_setting("DB_PASSWORD", required=True)
    password = quote_plus(password)

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"
