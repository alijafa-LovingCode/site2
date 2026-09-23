import os


def test_health(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_admin_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "ali", "password": os.environ["ADMIN_PASSWORD"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "ADMIN"
    assert data["display_name"] == "علی"


def test_student_login_success(client):
    resp = client.post("/api/auth/login", json={"username": "mehrsa", "password": os.environ["STUDENT_PASSWORD"]})
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "STUDENT"
    assert data["display_name"] == "مهرسا"


def test_login_wrong_password(client):
    resp = client.post("/api/auth/login", json={"username": "ali", "password": "wrong-password"})
    assert resp.status_code == 401


def test_login_unknown_user(client):
    resp = client.post("/api/auth/login", json={"username": "someone-else", "password": "x"})
    assert resp.status_code == 401


def test_me_requires_auth(client):
    resp = client.get("/api/auth/me")
    assert resp.status_code == 401


def test_me_after_login(admin_client):
    resp = admin_client.get("/api/auth/me")
    assert resp.status_code == 200
    assert resp.json()["role"] == "ADMIN"


def test_student_cannot_access_admin_endpoints(student_client):
    resp = student_client.get("/api/admin/dashboard")
    assert resp.status_code == 403


def test_student_cannot_create_subject(student_client):
    resp = student_client.post("/api/subjects", json={"name": "زبان انگلیسی"})
    assert resp.status_code == 403


def test_admin_can_access_dashboard(admin_client):
    resp = admin_client.get("/api/admin/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "today_tasks_total" in data


def test_logout_clears_session(admin_client):
    resp = admin_client.post("/api/auth/logout")
    assert resp.status_code == 200
    resp2 = admin_client.get("/api/auth/me")
    assert resp2.status_code == 401
