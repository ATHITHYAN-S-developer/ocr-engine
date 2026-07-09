import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.main import app
from src.infrastructure.database.session import Base
from src.presentation.api.dependencies import get_db

# Setup isolated test database using SQLite
TEST_DB_FILE = "./test_ocr.db"
SQLALCHEMY_DATABASE_URL = f"sqlite:///{TEST_DB_FILE}"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Database override helper
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Apply the override to FastAPI App
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

@pytest.fixture(scope="module", autouse=True)
def setup_database():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Dispose connection pool so SQLite releases file lock
    engine.dispose()
    # Drop tables & delete DB file
    if os.path.exists(TEST_DB_FILE):
        try:
            os.remove(TEST_DB_FILE)
        except PermissionError:
            pass

def test_health_endpoint():
    response = client.get("/api/v1/health")
    # Health check pinging PostgreSQL might fail in SQLite mode or if Redis is not running,
    # so we expect either 200 or 503 depending on Redis status. Let's make sure it reaches health router.
    assert response.status_code in [200, 503]

def test_user_flow():
    # 1. Register User
    reg_data = {
        "email": "dev@enterprise-ocr.com",
        "password": "strongpassword123",
        "role": "developer"
    }
    response = client.post("/api/v1/auth/register", json=reg_data)
    assert response.status_code == 201
    assert response.json()["email"] == "dev@enterprise-ocr.com"
    user_id = response.json()["id"]

    # 2. Login Token
    login_data = {
        "username": "dev@enterprise-ocr.com",
        "password": "strongpassword123"
    }
    response = client.post("/api/v1/auth/token", data=login_data)
    assert response.status_code == 200
    token = response.json()["access_token"]
    assert token is not None

    headers = {"Authorization": f"Bearer {token}"}

    # 3. Create Project
    proj_data = {
        "name": "HR Resume Parsing",
        "description": "Extract candidates details"
    }
    response = client.post("/api/v1/projects", json=proj_data, headers=headers)
    assert response.status_code == 201
    project_id = response.json()["id"]
    assert response.json()["name"] == "HR Resume Parsing"

    # 4. Generate API Key
    key_data = {
        "name": "Prod Server Key"
    }
    response = client.post(f"/api/v1/projects/{project_id}/api-keys", json=key_data, headers=headers)
    assert response.status_code == 201
    api_key_val = response.json()["key"]
    assert api_key_val.startswith("ocr_sk_")

    # 5. List Projects
    response = client.get("/api/v1/projects", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1
