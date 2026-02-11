from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker,Session
from typing import Generator

DATABASE_URL = "postgresql://postgres:postgres123@localhost:5432/pulsetrack"
#path to db = "C:\Program Files\PostgreSQL\18\bin\psql.exe"

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
