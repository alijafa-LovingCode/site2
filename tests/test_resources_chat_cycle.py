def test_admin_add_resource_and_student_view(admin_client, student_client):
    resp = admin_client.post(
        "/api/resources",
        json={
            "title": "جزوه فصل ۱ ریاضی",
            "url": "https://paadars.com/class-12/some-resource",
            "resource_type": "جزوه",
            "grade": "دوازدهم",
        },
    )
    assert resp.status_code == 200
    resource = resp.json()
    assert resource["title"] == "جزوه فصل ۱ ریاضی"

    resp2 = student_client.get("/api/resources")
    assert resp2.status_code == 200
    titles = [r["title"] for r in resp2.json()]
    assert "جزوه فصل ۱ ریاضی" in titles


def test_invalid_resource_url_rejected(admin_client):
    resp = admin_client.post("/api/resources", json={"title": "بد", "url": "not-a-valid-url"})
    assert resp.status_code == 400


def test_student_cannot_add_resource(student_client):
    resp = student_client.post("/api/resources", json={"title": "x", "url": "https://example.com"})
    assert resp.status_code == 403


def test_chat_send_and_read(admin_client, student_client):
    resp = student_client.post("/api/chat/messages", json={"text": "سلام علی"})
    assert resp.status_code == 200
    assert resp.json()["sender"] == "MEHRSA"

    resp2 = admin_client.post("/api/chat/messages", json={"text": "سلام مهرسا جان"})
    assert resp2.status_code == 200
    assert resp2.json()["sender"] == "ALI"

    resp3 = student_client.get("/api/chat/messages")
    assert resp3.status_code == 200
    texts = [m["text"] for m in resp3.json()]
    assert "سلام علی" in texts
    assert "سلام مهرسا جان" in texts


def test_cycle_tracker_student_flow(student_client):
    resp = student_client.post(
        "/api/cycle/entries",
        json={"start_date": "2026-01-01", "cycle_length_days": 28, "period_length_days": 5},
    )
    assert resp.status_code == 200
    entry = resp.json()

    resp2 = student_client.get("/api/cycle/prediction")
    assert resp2.status_code == 200
    prediction = resp2.json()
    assert prediction["estimated_next_start"] == "2026-01-29"
    assert "پزشک" in prediction["disclaimer"]

    resp3 = student_client.delete(f"/api/cycle/entries/{entry['id']}")
    assert resp3.status_code == 200


def test_cycle_tracker_blocked_for_admin_by_default(admin_client):
    resp = admin_client.get("/api/cycle/entries")
    assert resp.status_code == 403
