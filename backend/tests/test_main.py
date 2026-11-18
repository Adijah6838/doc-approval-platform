import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.db.session import Base, get_db
from app import models

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

def get_token(email: str, org_name: str):
    client.post("/auth/register", json={"email": email, "password": "password123", "org_name": org_name})
    res = client.post("/auth/login", json={"email": email, "password": "password123"})
    if res.status_code != 200:
        print(f"LOGIN FAILED for {email}: {res.json()}")
    return res.json().get("access_token", "")

def test_register_and_login():
    res = client.post("/auth/register", json={"email": "test@example.com", "password": "password123", "org_name": "TestCorp"})
    assert res.status_code == 201
    
    res = client.post("/auth/login", json={"email": "test@example.com", "password": "password123"})
    if res.status_code != 200:
        print(f"LOGIN FAILED: {res.json()}")
    assert res.status_code == 200
    assert "access_token" in res.json()

def test_multi_tenancy_isolation():
    tokenA = get_token("a@example.com", "Org A")
    tokenB = get_token("b@example.com", "Org B")

    res = client.post("/documents/upload", 
        headers={"Authorization": f"Bearer {tokenA}"}, 
        data={"title": "Secret Doc A"}, 
        files={"file": ("test.txt", b"hello world", "text/plain")}
    )
    assert res.status_code == 201
    doc_id = res.json()["id"]

    res = client.get(f"/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tokenB}"})
    assert res.status_code == 404

def test_rbac_review():
    tokenOwner = get_token("owner@example.com", "ReviewOrg")
    client.post("/auth/register", json={"email": "emp@example.com", "password": "password123", "org_name": "ReviewOrg"})
    res = client.post("/auth/login", json={"email": "emp@example.com", "password": "password123"})
    tokenEmp = res.json().get("access_token", "")

    res = client.post("/documents/upload", 
        headers={"Authorization": f"Bearer {tokenOwner}"}, 
        data={"title": "Review Me"}, files={"file": ("t.txt", b"1", "text/plain")}
    )
    doc_id = res.json()["id"]
    client.post(f"/documents/{doc_id}/submit", headers={"Authorization": f"Bearer {tokenOwner}"})

    res = client.post(f"/documents/{doc_id}/review", 
        headers={"Authorization": f"Bearer {tokenEmp}"}, 
        json={"action": "approve", "comment": "yes"}
    )
    assert res.status_code == 403

    res = client.post(f"/documents/{doc_id}/review", 
        headers={"Authorization": f"Bearer {tokenOwner}"}, 
        json={"action": "approve", "comment": "yes"}
    )
    assert res.status_code == 200
    assert res.json()["status"] == "approved"
