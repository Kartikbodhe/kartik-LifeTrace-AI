from datetime import datetime, date, timedelta
from decimal import Decimal
from flask import Blueprint, render_template, jsonify
from flask_login import login_required, current_user
from models import Task, PaymentTransaction, Promise, Memory

analytics_bp = Blueprint("analytics", __name__)

@analytics_bp.route("/")
@login_required
def index():
    now = datetime.utcnow()
    today = date.today()

    # 1. Tasks Analytics
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    total_tasks = len(tasks)
    completed_tasks = [t for t in tasks if t.status == "Completed"]
    in_progress_tasks = [t for t in tasks if t.status == "In Progress"]
    pending_tasks = [t for t in tasks if t.status == "Pending"]
    overdue_tasks = [t for t in tasks if t.is_overdue]

    # Task completion rate
    completion_rate = round((len(completed_tasks) / total_tasks * 100), 1) if total_tasks > 0 else 0

    # Tasks completed over the last 7 days
    last_7_days = [(today - timedelta(days=i)) for i in range(6, -1, -1)]
    days_labels = [d.strftime("%a (%b %d)") for d in last_7_days]
    completed_by_day = []
    created_by_day = []

    for d in last_7_days:
        day_completed = sum(1 for t in tasks if t.completed_at and t.completed_at.date() == d)
        day_created = sum(1 for t in tasks if t.created_at and t.created_at.date() == d)
        completed_by_day.append(day_completed)
        created_by_day.append(day_created)

    # Categories breakdown
    categories_count = {}
    for t in tasks:
        cat = t.category or "General"
        categories_count[cat] = categories_count.get(cat, 0) + 1

    # 2. Payments Analytics
    payments = PaymentTransaction.query.filter_by(user_id=current_user.id).all()
    lent_payments = [p for p in payments if p.transaction_type == "LENT"]
    borrowed_payments = [p for p in payments if p.transaction_type == "BORROWED"]

    total_lent = sum((p.amount for p in lent_payments), Decimal("0.00"))
    lent_recovered = sum((p.total_repaid for p in lent_payments), Decimal("0.00"))
    lent_outstanding = sum((p.remaining_balance for p in lent_payments if p.status != "Settled"), Decimal("0.00"))

    total_borrowed = sum((p.amount for p in borrowed_payments), Decimal("0.00"))
    borrowed_repaid = sum((p.total_repaid for p in borrowed_payments), Decimal("0.00"))
    borrowed_outstanding = sum((p.remaining_balance for p in borrowed_payments if p.status != "Settled"), Decimal("0.00"))

    # 3. Promises Analytics
    promises = Promise.query.filter_by(user_id=current_user.id).all()
    promises_completed = sum(1 for p in promises if p.status == "Completed")
    promises_pending = sum(1 for p in promises if p.status == "Pending")
    promises_cancelled = sum(1 for p in promises if p.status == "Cancelled")
    promises_overdue = sum(1 for p in promises if p.is_overdue)

    # 4. Memories count
    memories_count = Memory.query.filter_by(user_id=current_user.id).count()

    return render_template(
        "analytics/index.html",
        has_data=(total_tasks > 0 or len(payments) > 0 or len(promises) > 0 or memories_count > 0),
        task_metrics={
            "total": total_tasks,
            "completed": len(completed_tasks),
            "in_progress": len(in_progress_tasks),
            "pending": len(pending_tasks),
            "overdue": len(overdue_tasks),
            "completion_rate": completion_rate,
            "days_labels": days_labels,
            "completed_by_day": completed_by_day,
            "created_by_day": created_by_day,
            "categories_labels": list(categories_count.keys()),
            "categories_values": list(categories_count.values())
        },
        payment_metrics={
            "total_lent": float(total_lent),
            "lent_recovered": float(lent_recovered),
            "lent_outstanding": float(lent_outstanding),
            "total_borrowed": float(total_borrowed),
            "borrowed_repaid": float(borrowed_repaid),
            "borrowed_outstanding": float(borrowed_outstanding),
            "records_count": len(payments)
        },
        promise_metrics={
            "total": len(promises),
            "completed": promises_completed,
            "pending": promises_pending,
            "cancelled": promises_cancelled,
            "overdue": promises_overdue
        },
        memories_count=memories_count
    )
