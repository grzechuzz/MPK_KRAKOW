from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.common.app_common.config import build_database_url

engine = create_engine(build_database_url(), pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
