from datetime import datetime, date
from decimal import Decimal
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from models import Task, Memory, PaymentTransaction, Promise, Reminder, Notification

dashboard_bp = Blueprint("dashboard", __name__)

@dashboard_bp.route("/dashboard")
@login_required
def index():
    now = datetime.utcnow()
    today = date.today()

    # 1. Tasks Stats
    user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    total_tasks = len(user_tasks)
    active_tasks = [t for t in user_tasks if t.status != "Completed"]
    completed_tasks = [t for t in user_tasks if t.status == "Completed"]
    tasks_due_today = [t for t in active_tasks if t.is_due_today]
    overdue_tasks = [t for t in active_tasks if t.is_overdue]

    # 2. Payments Stats
    payments = PaymentTransaction.query.filter_by(user_id=current_user.id).all()
    lent_payments = [p for p in payments if p.transaction_type == "LENT" and p.status != "Settled"]
    borrowed_payments = [p for p in payments if p.transaction_type == "BORROWED" and p.status != "Settled"]
    
    total_lent_outstanding = sum((p.remaining_balance for p in lent_payments), Decimal("0.00"))
    total_borrowed_outstanding = sum((p.remaining_balance for p in borrowed_payments), Decimal("0.00"))
    overdue_payments = [p for p in payments if p.is_overdue]

    # 3. Promises Stats
    promises = Promise.query.filter_by(user_id=current_user.id).all()
    pending_promises = [p for p in promises if p.status == "Pending"]
    overdue_promises = [p for p in pending_promises if p.is_overdue]

    # 4. Reminders & Notifications
    upcoming_reminders = Reminder.query.filter(
        Reminder.user_id == current_user.id,
        Reminder.status == "Scheduled",
        Reminder.due_datetime >= now
    ).order_by(Reminder.due_datetime.asc()).limit(5).all()

    recent_notifications = Notification.query.filter_by(
        user_id=current_user.id
    ).order_by(Notification.created_at.desc()).limit(5).all()

    # 5. Recent Memories
    recent_memories = Memory.query.filter_by(
        user_id=current_user.id
    ).order_by(Memory.created_at.desc()).limit(5).all()

    # 6. Recent Tasks
    recent_active_tasks = sorted(active_tasks, key=lambda x: (x.due_date is None, x.due_date or datetime.max))[:5]

    return render_template(
        "dashboard.html",
        stats={
            "total_tasks": total_tasks,
            "active_tasks_count": len(active_tasks),
            "completed_tasks_count": len(completed_tasks),
            "due_today_count": len(tasks_due_today),
            "overdue_tasks_count": len(overdue_tasks),
            "total_lent_outstanding": total_lent_outstanding,
            "total_borrowed_outstanding": total_borrowed_outstanding,
            "pending_promises_count": len(pending_promises),
            "overdue_promises_count": len(overdue_promises),
            "upcoming_reminders_count": len(upcoming_reminders),
            "overdue_payments_count": len(overdue_payments)
        },
        recent_tasks=recent_active_tasks,
        recent_memories=recent_memories,
        upcoming_reminders=upcoming_reminders,
        recent_notifications=recent_notifications,
        pending_promises=pending_promises[:5],
        active_payments=payments[:5]
    )
