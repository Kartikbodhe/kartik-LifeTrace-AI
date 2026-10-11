from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, jsonify, request
from flask_login import login_required, current_user
from models import Task, PaymentTransaction, Promise, Memory, Reminder

calendar_bp = Blueprint("calendar", __name__)

@calendar_bp.route("/")
@login_required
def index():
    # Pass initial current year and month for template rendering
    today = date.today()
    return render_template("calendar/index.html", today=today)

@calendar_bp.route("/api/events")
@login_required
def api_events():
    """
    Returns aggregated timeline events for the user formatted for month & agenda calendar.
    """
    events = []

    # 1. Task Deadlines
    tasks = Task.query.filter(
        Task.user_id == current_user.id,
        Task.due_date.isnot(None)
    ).all()

    for task in tasks:
        events.append({
            "id": f"task-{task.id}",
            "title": f"📋 {task.title}",
            "start": task.due_date.strftime("%Y-%m-%dT%H:%M:00"),
            "category": "Task",
            "status": task.status,
            "priority": task.priority,
            "url": f"/tasks/{task.id}/edit",
            "color": "#6366f1",  # Indigo
            "is_all_day": False,
            "description": task.description or f"Priority: {task.priority} | Status: {task.status}"
        })

    # 2. Payment Due Dates
    payments = PaymentTransaction.query.filter(
        PaymentTransaction.user_id == current_user.id,
        PaymentTransaction.expected_repayment_date.isnot(None)
    ).all()

    for p in payments:
        is_lent = p.transaction_type == "LENT"
        color = "#10b981" if is_lent else "#f59e0b"  # Emerald for Lent, Amber for Borrowed
        events.append({
            "id": f"payment-{p.id}",
            "title": f"{'💰' if is_lent else '💳'} ₹{p.remaining_balance} ({p.person_name})",
            "start": p.expected_repayment_date.strftime("%Y-%m-%d"),
            "category": f"Payment ({'Lent' if is_lent else 'Borrowed'})",
            "status": p.status,
            "url": f"/payments/{p.id}",
            "color": color,
            "is_all_day": True,
            "description": f"Balance: ₹{p.remaining_balance} | Status: {p.status}"
        })

    # 3. Promise Follow-ups
    promises = Promise.query.filter(
        Promise.user_id == current_user.id,
        Promise.follow_up_date.isnot(None)
    ).all()

    for pr in promises:
        events.append({
            "id": f"promise-{pr.id}",
            "title": f"🤝 {pr.title} ({pr.person_or_org})",
            "start": pr.follow_up_date.strftime("%Y-%m-%d"),
            "category": "Promise",
            "status": pr.status,
            "priority": pr.priority,
            "url": f"/promises/{pr.id}/edit",
            "color": "#a855f7",  # Purple
            "is_all_day": True,
            "description": pr.description or f"Commitment with {pr.person_or_org}"
        })

    # 4. Memory Events
    memories = Memory.query.filter(
        Memory.user_id == current_user.id,
        Memory.event_date.isnot(None)
    ).all()

    for m in memories:
        events.append({
            "id": f"memory-{m.id}",
            "title": f"🧠 {m.title}",
            "start": m.event_date.strftime("%Y-%m-%d"),
            "category": f"Memory ({m.category})",
            "status": m.status,
            "url": f"/memories/{m.id}",
            "color": "#06b6d4",  # Cyan
            "is_all_day": True,
            "description": m.description[:100] if m.description else ""
        })

    # 5. Scheduled Reminders
    reminders = Reminder.query.filter(
        Reminder.user_id == current_user.id,
        Reminder.status.in_(["Scheduled", "Sent"])
    ).all()

    for r in reminders:
        events.append({
            "id": f"reminder-{r.id}",
            "title": f"⏰ {r.title}",
            "start": r.due_datetime.strftime("%Y-%m-%dT%H:%M:00"),
            "category": "Reminder",
            "status": r.status,
            "url": "/reminders",
            "color": "#f43f5e",  # Rose
            "is_all_day": False,
            "description": r.description or "Scheduled Reminder"
        })

    return jsonify({"events": events})
