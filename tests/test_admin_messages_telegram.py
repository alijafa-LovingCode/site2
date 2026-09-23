def test_daily_messages_crud(admin_client):
    resp = admin_client.post("/api/messages", json={"text": "پیام تستی", "category": "آرامش"})
    assert resp.status_code == 200
    msg = resp.json()

    resp2 = admin_client.put(f"/api/messages/{msg['id']}", json={"is_enabled": False})
    assert resp2.status_code == 200
    assert resp2.json()["is_enabled"] is False

    resp3 = admin_client.delete(f"/api/messages/{msg['id']}")
    assert resp3.status_code == 200


def test_today_message_endpoint_available_to_student(student_client):
    resp = student_client.get("/api/messages/today")
    assert resp.status_code == 200
    assert "text" in resp.json()


def test_message_cycle_does_not_repeat_immediately():
    """Two consecutive days should not receive the same message while the
    enabled message pool still has unused entries."""
    from datetime import date

    from app.database import SessionLocal
    from app.services.messages_seed import get_message_for_date

    with SessionLocal() as db:
        day1 = date(2031, 1, 1)
        day2 = date(2031, 1, 2)
        msg1 = get_message_for_date(db, day1)
        msg2 = get_message_for_date(db, day2)
        assert msg1 is not None and msg2 is not None
        assert msg1.id != msg2.id


def test_telegram_settings_get_and_update(admin_client):
    resp = admin_client.get("/api/telegram/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert "bot_token_set" in data

    resp2 = admin_client.put(
        "/api/telegram/settings",
        json={"chat_id": "123456", "reminder_time": "09:30", "is_enabled": False},
    )
    assert resp2.status_code == 200
    assert resp2.json()["chat_id"] == "123456"
    assert resp2.json()["reminder_time"] == "09:30"


def test_telegram_settings_forbidden_for_student(student_client):
    resp = student_client.get("/api/telegram/settings")
    assert resp.status_code == 403


def test_backup_export(admin_client):
    resp = admin_client.get("/api/admin/backup/export")
    assert resp.status_code == 200
    data = resp.json()
    assert "tables" in data
    assert "subjects" in data["tables"]
    # Cycle data must be excluded by default
    assert "cycle_entries" not in data["tables"]


def test_backup_export_with_cycle_data(admin_client):
    resp = admin_client.get("/api/admin/backup/export?include_cycle_data=true")
    assert resp.status_code == 200
    assert "cycle_entries" in resp.json()["tables"]


def test_system_settings_roundtrip(admin_client):
    resp = admin_client.put("/api/admin/settings", json={"daily_budget_minutes": "180"})
    assert resp.status_code == 200
    resp2 = admin_client.get("/api/admin/settings")
    assert resp2.json()["daily_budget_minutes"] == "180"


def test_activity_logs_recorded(admin_client):
    resp = admin_client.get("/api/admin/logs")
    assert resp.status_code == 200
    logs = resp.json()
    assert len(logs) > 0
    assert any(l["action"] == "login_success" for l in logs)


def test_change_password_flow(client):
    import os

    login = client.post("/api/auth/login", json={"username": "ali", "password": os.environ["ADMIN_PASSWORD"]})
    assert login.status_code == 200

    resp = client.post(
        "/api/auth/change-password",
        json={"current_password": os.environ["ADMIN_PASSWORD"], "new_password": "new-secure-pass-456"},
    )
    assert resp.status_code == 200

    # Old password should no longer work
    client.post("/api/auth/logout")
    relogin_old = client.post("/api/auth/login", json={"username": "ali", "password": os.environ["ADMIN_PASSWORD"]})
    assert relogin_old.status_code == 401

    relogin_new = client.post("/api/auth/login", json={"username": "ali", "password": "new-secure-pass-456"})
    assert relogin_new.status_code == 200

    # restore original password so other tests relying on it still work
    client.post(
        "/api/auth/change-password",
        json={"current_password": "new-secure-pass-456", "new_password": os.environ["ADMIN_PASSWORD"]},
    )
