import pytest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from tests.config import TEST_DATABASE_URL, TEST_REDIS_URL

from app.main import app
from app.db.sessions_postgres import get_db_session


# Test PostgreSQL connection
test_engine = create_engine(TEST_DATABASE_URL)

TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    autocommit=False
)


# Override application database dependency
def override_get_test_db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    app.state.start_scheduler = False
    app.state.redis_url = TEST_REDIS_URL

    app.dependency_overrides[get_db_session] = override_get_test_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="session", autouse=True)
def dispose_test_engine():
    yield
    test_engine.dispose()
