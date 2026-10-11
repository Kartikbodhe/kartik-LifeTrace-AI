import pytest
from datetime import datetime, timedelta
from models import Reminder, Notification
from extensions import db
from services.reminder_service import process_due_reminders
from services.notification_service import NotificationService

def test_schedule_and_trigger_reminder(client, auth, user1, app):
    auth.login("user_one", "password123")

    # 1. Schedule a reminder in the past so it triggers immediately upon execution
    past_time = datetime.utcnow() - timedelta(minutes=5)
    with app.app_context():
        reminder = Reminder(
            user_id=user1,
            title="Meeting with Thesis Supervisor",
            description="Bring chapter 2 notes",
            due_datetime=past_time,
            status="Scheduled",
            related_type="general"
        )
        db.session.add(reminder)
        db.session.commit()
        reminder_id = reminder.id

    # 2. Run reminder processor
    process_due_reminders(app)

    # 3. Verify reminder became "Sent" and notification was generated
    with app.app_context():
        rem = db.session.get(Reminder, reminder_id)
        assert rem.status == "Sent"

        notif = Notification.query.filter_by(reminder_id=reminder_id).first()
        assert notif is not None
        assert notif.user_id == user1
        assert "Meeting with Thesis Supervisor" in notif.title
        assert notif.is_read is False

        # Verify unread count
        assert NotificationService.get_unread_count(user1) == 1

def test_mark_notification_as_read(client, auth, user1, app):
    auth.login("user_one", "password123")

    with app.app_context():
        notif = NotificationService.create_notification(
            user_id=user1,
            title="Important Alert",
            message="Your assignment deadline is approaching."
        )
        notif_id = notif.id

    assert NotificationService.get_unread_count(user1) == 1

    # Mark as read
    resp = client.post(f"/reminders/notifications/{notif_id}/read", follow_redirects=True)
    assert resp.status_code == 200

    assert NotificationService.get_unread_count(user1) == 0

def test_dismiss_reminder(client, auth, user1, app):
    auth.login("user_one", "password123")

    with app.app_context():
        rem = Reminder(
            user_id=user1,
            title="Grocery run",
            due_datetime=datetime.utcnow() + timedelta(days=1),
            status="Scheduled"
        )
        db.session.add(rem)
        db.session.commit()
        rem_id = rem.id

    # Dismiss
    client.post(f"/reminders/{rem_id}/dismiss", follow_redirects=True)

    with app.app_context():
        assert db.session.get(Reminder, rem_id).status == "Cancelled"
