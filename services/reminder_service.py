import os
import atexit
from datetime import datetime, date, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
from extensions import db
from models import Reminder, Notification, Task, PaymentTransaction, Promise

scheduler = BackgroundScheduler(daemon=True)

def process_due_reminders(app):
    """
    Background job triggered periodically to:
    1. Deliver scheduled reminders that are due.
    2. Check for newly overdue tasks, payments, or promises.
    """
    with app.app_context():
        try:
            now = datetime.utcnow()
            today = date.today()

            # 1. Process explicit reminders
            due_reminders = Reminder.query.filter(
                Reminder.status == "Scheduled",
                Reminder.due_datetime <= now
            ).all()

            for rem in due_reminders:
                rem.status = "Sent"
                rem.updated_at = now
                
                # Create corresponding notification
                notif = Notification(
                    user_id=rem.user_id,
                    reminder_id=rem.id,
                    title=f"Reminder: {rem.title}",
                    message=rem.description or f"Your scheduled reminder for '{rem.title}' is now due.",
                    notification_type=f"{rem.related_type}_reminder" if rem.related_type else "reminder",
                    is_read=False,
                    created_at=now
                )
                db.session.add(notif)

            # 2. Check overdue tasks (only notify once per overdue task)
            overdue_tasks = Task.query.filter(
                Task.status.in_(["Pending", "In Progress"]),
                Task.due_date.isnot(None),
                Task.due_date < now
            ).all()

            for task in overdue_tasks:
                # Check if notification was already generated in the last 24 hours
                recent_notif = Notification.query.filter(
                    Notification.user_id == task.user_id,
                    Notification.title == f"Overdue Task: {task.title}",
                    Notification.created_at >= (now - timedelta(hours=24))
                ).first()

                if not recent_notif:
                    db.session.add(Notification(
                        user_id=task.user_id,
                        title=f"Overdue Task: {task.title}",
                        message=f"Task '{task.title}' was due on {task.due_date.strftime('%Y-%m-%d %H:%M')}.",
                        notification_type="task_due",
                        is_read=False,
                        created_at=now
                    ))

            # 3. Check overdue payments
            overdue_payments = PaymentTransaction.query.filter(
                PaymentTransaction.status.in_(["Pending", "Partially Paid"]),
                PaymentTransaction.expected_repayment_date.isnot(None),
                PaymentTransaction.expected_repayment_date < today
            ).all()

            for payment in overdue_payments:
                direction = "repaying" if payment.transaction_type == "BORROWED" else "collecting from"
                p_title = f"Overdue Payment: ₹{payment.remaining_balance} with {payment.person_name}"
                recent_notif = Notification.query.filter(
                    Notification.user_id == payment.user_id,
                    Notification.title == p_title,
                    Notification.created_at >= (now - timedelta(hours=24))
                ).first()

                if not recent_notif:
                    db.session.add(Notification(
                        user_id=payment.user_id,
                        title=p_title,
                        message=f"Outstanding balance of ₹{payment.remaining_balance} ({direction} {payment.person_name}) was expected by {payment.expected_repayment_date}.",
                        notification_type="payment_due",
                        is_read=False,
                        created_at=now
                    ))

            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Silent fallback during background execution, log to stdout
            print(f"[LifeTrace Scheduler Error]: {e}")


def init_scheduler(app):
    """
    Initializes and starts APScheduler for background reminders.
    Avoids running multiple schedulers during Flask debug reloader.
    """
    if not app.config.get("SCHEDULER_API_ENABLED", True):
        return

    # In Werkzeug reloader, only run in the main child process
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true" or not app.debug:
        if not scheduler.running:
            # Check reminders every 30 seconds
            scheduler.add_job(
                func=process_due_reminders,
                args=[app],
                trigger="interval",
                seconds=30,
                id="lifetrace_reminder_job",
                replace_existing=True
            )
            scheduler.start()
            atexit.register(lambda: scheduler.shutdown(wait=False))
