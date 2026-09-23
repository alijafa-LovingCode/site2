from datetime import date, timedelta


def test_create_exam_and_countdown(admin_client):
    subjects = admin_client.get("/api/subjects").json()
    subject_id = subjects[0]["id"]
    exam_date = (date.today() + timedelta(days=5)).isoformat()

    resp = admin_client.post(
        "/api/exams",
        json={"name": "آزمون میان‌ترم", "subject_id": subject_id, "exam_date": exam_date, "importance": 1},
    )
    assert resp.status_code == 200
    exam = resp.json()
    assert exam["days_remaining"] == 5

    resp2 = admin_client.get("/api/exams/next")
    assert resp2.status_code == 200
    assert resp2.json()["days_remaining"] <= 5


def test_exam_update_and_delete(admin_client):
    exam_date = (date.today() + timedelta(days=10)).isoformat()
    resp = admin_client.post("/api/exams", json={"name": "آزمون حذفی", "exam_date": exam_date})
    exam = resp.json()

    resp2 = admin_client.put(f"/api/exams/{exam['id']}", json={"importance": 1})
    assert resp2.status_code == 200
    assert resp2.json()["importance"] == 1

    resp3 = admin_client.delete(f"/api/exams/{exam['id']}")
    assert resp3.status_code == 200


def test_student_cannot_create_exam(student_client):
    resp = student_client.post("/api/exams", json={"name": "بدون دسترسی", "exam_date": date.today().isoformat()})
    assert resp.status_code == 403


def test_student_can_list_upcoming_exams(student_client):
    resp = student_client.get("/api/exams?upcoming_only=true")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
