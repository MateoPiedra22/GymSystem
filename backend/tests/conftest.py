import pytest
import asyncio
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import tempfile
from unittest.mock import Mock

# Set testing environment
os.environ["TESTING"] = "true"
os.environ["ENVIRONMENT"] = "testing"
os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["EMAIL_ENABLED"] = "false"
os.environ["RATE_LIMIT_ENABLED"] = "false"

from app.main import app
from app.core.database import Base, get_db
from app.core.auth import get_current_user, get_current_active_user
from app.models.user import User
from app.models.role import Role
from app.core.security import create_access_token, get_password_hash
from app.core.config import settings

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    # Create session
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with database dependency override."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()


@pytest.fixture
def mock_user():
    """Create a mock user for testing."""
    return User(
        id=1,
        email="test@example.com",
        username="testuser",
        first_name="Test",
        last_name="User",
        hashed_password=get_password_hash("testpassword"),
        is_active=True,
        is_verified=True,
        role_id=1
    )


@pytest.fixture
def mock_admin_user():
    """Create a mock admin user for testing."""
    return User(
        id=2,
        email="admin@example.com",
        username="admin",
        first_name="Admin",
        last_name="User",
        hashed_password=get_password_hash("adminpassword"),
        is_active=True,
        is_verified=True,
        role_id=2
    )


@pytest.fixture
def mock_owner_user():
    """Create a mock owner user for testing."""
    return User(
        id=3,
        email="owner@example.com",
        username="owner",
        first_name="Owner",
        last_name="User",
        hashed_password=get_password_hash("ownerpassword"),
        is_active=True,
        is_verified=True,
        role_id=6
    )


@pytest.fixture
def access_token(mock_user):
    """Create an access token for testing."""
    return create_access_token(data={"sub": mock_user.email})


@pytest.fixture
def admin_access_token(mock_admin_user):
    """Create an admin access token for testing."""
    return create_access_token(data={"sub": mock_admin_user.email})


@pytest.fixture
def owner_access_token(mock_owner_user):
    """Create an owner access token for testing."""
    return create_access_token(data={"sub": mock_owner_user.email})


@pytest.fixture
def auth_headers(access_token):
    """Create authorization headers for testing."""
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def admin_auth_headers(admin_access_token):
    """Create admin authorization headers for testing."""
    return {"Authorization": f"Bearer {admin_access_token}"}


@pytest.fixture
def owner_auth_headers(owner_access_token):
    """Create owner authorization headers for testing."""
    return {"Authorization": f"Bearer {owner_access_token}"}


@pytest.fixture
def authenticated_client(client, mock_user, auth_headers):
    """Create an authenticated test client."""
    def override_get_current_user():
        return mock_user
    
    def override_get_current_active_user():
        return mock_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def admin_authenticated_client(client, mock_admin_user, admin_auth_headers):
    """Create an admin authenticated test client."""
    def override_get_current_user():
        return mock_admin_user
    
    def override_get_current_active_user():
        return mock_admin_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def owner_authenticated_client(client, mock_owner_user, owner_auth_headers):
    """Create an owner authenticated test client."""
    def override_get_current_user():
        return mock_owner_user
    
    def override_get_current_active_user():
        return mock_owner_user
    
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_current_active_user] = override_get_current_active_user
    
    yield client
    
    app.dependency_overrides.clear()


@pytest.fixture
def temp_file():
    """Create a temporary file for testing file uploads."""
    with tempfile.NamedTemporaryFile(delete=False) as tmp:
        tmp.write(b"test file content")
        tmp.flush()
        yield tmp.name
    os.unlink(tmp.name)


@pytest.fixture
def mock_email_service():
    """Mock email service for testing."""
    return Mock()


@pytest.fixture
def mock_redis():
    """Mock Redis service for testing."""
    return Mock()


@pytest.fixture
def mock_celery():
    """Mock Celery service for testing."""
    return Mock()


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "email": "newuser@example.com",
        "username": "newuser",
        "password": "newpassword123",
        "first_name": "New",
        "last_name": "User",
        "phone": "+1234567890",
        "date_of_birth": "1990-01-01"
    }


@pytest.fixture
def sample_membership_data():
    """Sample membership data for testing."""
    return {
        "user_id": 1,
        "membership_type_id": 1,
        "start_date": "2024-01-01",
        "end_date": "2024-12-31",
        "status": "ACTIVE"
    }


@pytest.fixture
def sample_exercise_data():
    """Sample exercise data for testing."""
    return {
        "name": "Push Up",
        "description": "A basic push up exercise",
        "category": "STRENGTH",
        "muscle_groups": ["CHEST", "TRICEPS"],
        "equipment": "BODYWEIGHT",
        "difficulty_level": "BEGINNER",
        "instructions": ["Start in plank position", "Lower body", "Push up"]
    }


@pytest.fixture
def sample_class_data():
    """Sample class data for testing."""
    return {
        "name": "Morning Yoga",
        "description": "Relaxing morning yoga session",
        "instructor_id": 1,
        "class_type": "YOGA",
        "duration": 60,
        "max_capacity": 20,
        "price": 25.00
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "api: mark test as API test"
    )


def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on test location."""
    for item in items:
        # Add markers based on test file location
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)
        elif "api" in str(item.fspath):
            item.add_marker(pytest.mark.api)
        
        # Add slow marker for tests that might be slow
        if "test_database" in item.name or "test_email" in item.name:
            item.add_marker(pytest.mark.slow)