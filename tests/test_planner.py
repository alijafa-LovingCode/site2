from datetime import date, timedelta


def test_list_subjects_seeded(student_client):
    resp = student_client.get("/api/subjects")
    assert resp.status_code == 200
    subjects = resp.json()
    assert len(subjects) >= 8
    names = [s["name"] for s in subjects]
    assert "ریاضی" in names
    assert "فیزیک" in names


def test_admin_create_update_delete_subject(admin_client):
    resp = admin_client.post("/api/subjects", json={"name": "هنر", "priority": 4, "difficulty": 1, "color": "#123456"})
    assert resp.status_code == 200
    subject = resp.json()
    assert subject["name"] == "هنر"

    resp2 = admin_client.put(f"/api/subjects/{subject['id']}", json={"priority": 2})
    assert resp2.status_code == 200
    assert resp2.json()["priority"] == 2

    resp3 = admin_client.delete(f"/api/subjects/{subject['id']}")
    assert resp3.status_code == 200


def test_duplicate_subject_rejected(admin_client):
    admin_client.post("/api/subjects", json={"name": "تکراری"})
    resp = admin_client.post("/api/subjects", json={"name": "تکراری"})
    assert resp.status_code == 400


def test_create_and_complete_task(admin_client):
    subjects = admin_client.get("/api/subjects").json()
    subject_id = subjects[0]["id"]
    today = date.today().isoformat()

    resp = admin_client.post(
        "/api/tasks",
        json={"subject_id": subject_id, "date": today, "task": "حل تمرین", "duration_minutes": 45},
    )
    assert resp.status_code == 200
    task = resp.json()
    assert task["duration_minutes"] == 45
    assert task["is_completed"] is False

    resp2 = admin_client.put(f"/api/tasks/{task['id']}", json={"is_completed": True})
    assert resp2.status_code == 200
    assert resp2.json()["is_completed"] is True

    resp3 = admin_client.delete(f"/api/tasks/{task['id']}")
    assert resp3.status_code == 200


def test_today_tasks_endpoint(student_client):
    resp = student_client.get("/api/tasks/today")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_week_tasks_endpoint_returns_seven_days(student_client):
    today = date.today()
    resp = student_client.get(f"/api/tasks/week?week_start={today.isoformat()}")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data["days"]) == 7
    weekday_names = [d["weekday_fa"] for d in data["days"]]
    for name in ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه"]:
        assert name in weekday_names


def test_next_day_selection_and_plan_generation(student_client):
    subjects = student_client.get("/api/subjects").json()
    subject_ids = [s["id"] for s in subjects[:3]]
    tomorrow = (date.today() + timedelta(days=1)).isoformat()

    resp = student_client.post("/api/next-day-selection", json={"date": tomorrow, "subject_ids": subject_ids})
    assert resp.status_code == 200

    resp2 = student_client.get(f"/api/next-day-selection?target_date={tomorrow}")
    assert resp2.status_code == 200
    assert set(resp2.json()["subject_ids"]) == set(subject_ids)

    resp3 = student_client.post(f"/api/planner/generate?target_date={tomorrow}")
    assert resp3.status_code == 200
    data = resp3.json()
    assert len(data["tasks"]) > 0
    # Engine should not overload a single day: sum of durations should be
    # close to (not wildly exceeding) the default daily budget.
    total_minutes = sum(t["duration_minutes"] for t in data["tasks"])
    assert total_minutes <= 240 + 30  # small tolerance for the review block


def test_plan_generation_without_selection_fails(student_client):
    far_future = (date.today() + timedelta(days=200)).isoformat()
    resp = student_client.post(f"/api/planner/generate?target_date={far_future}")
    assert resp.status_code == 400
