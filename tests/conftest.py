"""
Pytest configuration and shared fixtures for test suite.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.main import app
from app.db.database import Base, get_db
from app.db import models
from app.core.config import settings
import os

# Use in-memory SQLite for testing
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db():
    """Database session fixture for each test."""
    Base.metadata.create_all(bind=engine)
    db_session = TestingSessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db: Session):
    """FastAPI test client fixture with test database."""
    
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db: Session):
    """Create a test user."""
    from app.db.models import User
    from app.core.security import pwd_context
    
    user = User(
        email="testuser@example.com",
        username="testuser",
        hashed_password=pwd_context.hash("TestPassword123"),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture(scope="function")
def test_url(db: Session, test_user: models.User):
    """Create a test shortened URL."""
    url = models.URL(
        original_url="https://github.com",
        short_code="abc123",
        user_id=test_user.id,
    )
    db.add(url)
    db.commit()
    db.refresh(url)
    return url


@pytest.fixture(scope="function")
def test_token(client: TestClient):
    """Get a valid JWT token for testing."""
    response = client.post(
        "/auth/register",
        json={
            "email": "tokentest@example.com",
            "username": "tokentest",
            "password": "TestPassword123",
        },
    )
    assert response.status_code == 201
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(test_token: str):
    """Create authorization headers with valid JWT."""
    return {"Authorization": f"Bearer {test_token}"}
