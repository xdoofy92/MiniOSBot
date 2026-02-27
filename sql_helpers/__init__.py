import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from Config import Config

# Usar SQLite si no hay DATABASE_URL (ej. desarrollo local sin PostgreSQL)
DATABASE_URL = Config.DATABASE_URL or "sqlite:///forcesubscribe.db"


def start() -> scoped_session:
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    BASE.metadata.bind = engine
    BASE.metadata.create_all(engine)
    return scoped_session(sessionmaker(bind=engine, autoflush=False))


try:
    BASE = declarative_base()
    SESSION = start()
except Exception as e:
    print("Database error. Using SQLite fallback might help if DATABASE_URL was missing.")
    raise