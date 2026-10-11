from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
from typing import Generator

from app.core.config import DATABASE_URL
"""
Database Sessions

Responsibilities:
- create postgres db session 
"""

engine = create_engine(
    DATABASE_URL,
    echo=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

def get_db_session() -> Generator[Session,None,None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
