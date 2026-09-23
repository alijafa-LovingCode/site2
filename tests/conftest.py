"""
Test configuration.

Tests use a local SQLite file database purely for speed and CI simplicity.
This does NOT change the production requirement of PostgreSQL -- see
app/database.py and README.md, where SQLite is explicitly documented as
unsupported for production/Railway deployments.
"""
from __future__ import annotations

import os

os.environ.setdefault("DATABASE_URL", "sqlite:///./test_mehrsa_planner.db")
os.environ.setdefault("SECRET_KEY", "test-secret-key-not-for-production")
os.environ.setdefault("ADMIN_PASSWORD", "test-admin-pass-123")
os.environ.setdefault("STUDENT_PASSWORD", "test-student-pass-123")
os.environ.setdefault("APP_ENV", "test")
os.environ.setdefault("TELEGRAM_ENABLED", "false")
os.environ.setdefault("AI_PROVIDER", "none")
os.environ.setdefault("LOGIN_RATE_LIMIT", "1000/minute")

import pytest
from fastapi.testclient import TestClient

from app.database import Base, SessionLocal, engine
from app.main import app
from app.services.startup_seed import run_startup_seed


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        run_startup_seed(db)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("test_mehrsa_planner.db")
    except OSError:
        pass


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture
def admin_client(client):
    resp = client.post("/api/auth/login", json={"username": "ali", "password": os.environ["ADMIN_PASSWORD"]})
    assert resp.status_code == 200
    return client


@pytest.fixture
def student_client(client):
    resp = client.post("/api/auth/login", json={"username": "mehrsa", "password": os.environ["STUDENT_PASSWORD"]})
    assert resp.status_code == 200
    return client
