import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.api.deps import get_db
from app.core.config import get_settings
from app.db.base import Base
from app.main import app

get_settings.cache_clear()
settings = get_settings()

if "test" not in settings.test_database_url:
    raise RuntimeError("TEST_DATABASE_URL must point to a test database")

engine = create_engine(settings.test_database_url)
TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(scope="session", autouse=True)
def prepare_test_database() -> None:
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session() -> Session:
    connection = engine.connect()
    transaction = connection.begin()

    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(db_session: Session) -> TestClient:
    def override_get_db() -> Session:
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
