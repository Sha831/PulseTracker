
import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from tests.config import TEST_DATABASE_URL


test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


@pytest.fixture
def db_session():
    session = TestingSessionLocal()

    try:
        yield session
    finally:
        session.close()
