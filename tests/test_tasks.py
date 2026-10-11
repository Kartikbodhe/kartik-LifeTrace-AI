import pytest
from datetime import datetime, timedelta
from models import Task
from extensions import db

def test_create_and_edit_task(client, auth, user1, app):
    auth.login("user_one", "password123")

    # Create task
    future_time = (datetime.utcnow() + timedelta(days=2)).strftime("%Y-%m-%dT%H:%M")
    resp = client.post("/tasks/new", data={
        "title": "Complete Thesis Presentation",
        "description": "Prepare 15 slides for committee review",
        "priority": "High",
        "category": "College",
        "due_date": future_time
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"Task created successfully" in resp.data

    with app.app_context():
        task = Task.query.filter_by(title="Complete Thesis Presentation").first()
        assert task is not None
        assert task.user_id == user1
        assert task.priority == "High"
        assert task.status == "Pending"
        assert not task.is_overdue

    # Edit task
    resp_edit = client.post(f"/tasks/{task.id}/edit", data={
        "title": "Complete Thesis Presentation (Updated)",
        "description": "Updated slides",
        "priority": "Medium",
        "category": "College",
        "status": "In Progress",
        "due_date": future_time
    }, follow_redirects=True)

    assert resp_edit.status_code == 200
    with app.app_context():
        updated_task = db.session.get(Task, task.id)
        assert updated_task.title == "Complete Thesis Presentation (Updated)"
        assert updated_task.status == "In Progress"

def test_task_toggle_completion(client, auth, user1, app):
    auth.login("user_one", "password123")

    with app.app_context():
        task = Task(user_id=user1, title="Read chapter 4", status="Pending")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    # Toggle to complete
    client.post(f"/tasks/{task_id}/toggle", follow_redirects=True)
    with app.app_context():
        t = db.session.get(Task, task_id)
        assert t.status == "Completed"
        assert t.completed_at is not None

    # Toggle reopen
    client.post(f"/tasks/{task_id}/toggle", follow_redirects=True)
    with app.app_context():
        t = db.session.get(Task, task_id)
        assert t.status == "Pending"
        assert t.completed_at is None

def test_overdue_dynamic_calculation(app, user1):
    with app.app_context():
        # Past due date task
        past_task = Task(
            user_id=user1,
            title="Overdue report",
            due_date=datetime.utcnow() - timedelta(hours=5),
            status="Pending"
        )
        db.session.add(past_task)
        db.session.commit()

        assert past_task.is_overdue is True

        # When completed, is_overdue should be False
        past_task.mark_complete()
        assert past_task.is_overdue is False

def test_cross_user_isolation(client, auth, user1, user2, app):
    with app.app_context():
        task = Task(user_id=user1, title="User1 Secret Task", status="Pending")
        db.session.add(task)
        db.session.commit()
        task_id = task.id

    # Log in as user2
    auth.login("user_two", "password123")

    # User 2 tries to edit User 1's task
    resp = client.get(f"/tasks/{task_id}/edit")
    assert resp.status_code == 404  # Scoped query returns 404

    # User 2 tries to delete User 1's task
    resp_del = client.post(f"/tasks/{task_id}/delete")
    assert resp_del.status_code == 404

    # Verify task still exists for User 1
    with app.app_context():
        assert db.session.get(Task, task_id) is not None
