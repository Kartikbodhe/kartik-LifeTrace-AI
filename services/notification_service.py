from datetime import datetime
from extensions import db
from models import Notification

class NotificationService:
    @staticmethod
    def create_notification(user_id, title, message, notification_type="reminder", reminder_id=None):
        """Create a persistent notification for a user."""
        notification = Notification(
            user_id=user_id,
            reminder_id=reminder_id,
            title=title,
            message=message,
            notification_type=notification_type,
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notification)
        db.session.commit()
        return notification

    @staticmethod
    def get_unread_count(user_id):
        """Count unread notifications for navigation badge."""
        return Notification.query.filter_by(user_id=user_id, is_read=False).count()

    @staticmethod
    def get_user_notifications(user_id, limit=30):
        """Retrieve recent notifications ordered by newest first."""
        return Notification.query.filter_by(user_id=user_id)\
            .order_by(Notification.created_at.desc())\
            .limit(limit)\
            .all()

    @staticmethod
    def mark_as_read(notification_id, user_id):
        """Mark single notification as read if owned by user."""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            notification.is_read = True
            db.session.commit()
            return True
        return False

    @staticmethod
    def mark_all_as_read(user_id):
        """Mark all unread notifications as read for a user."""
        Notification.query.filter_by(user_id=user_id, is_read=False)\
            .update({Notification.is_read: True})
        db.session.commit()
        return True

    @staticmethod
    def delete_notification(notification_id, user_id):
        """Delete notification if owned by user."""
        notification = Notification.query.filter_by(id=notification_id, user_id=user_id).first()
        if notification:
            db.session.delete(notification)
            db.session.commit()
            return True
        return False
