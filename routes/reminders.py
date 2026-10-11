from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db
from models import Reminder, Notification
from services.notification_service import NotificationService

reminders_bp = Blueprint("reminders", __name__)

@reminders_bp.route("/")
@login_required
def index():
    now = datetime.utcnow()
    status_filter = request.args.get("status", "all").strip()

    query = Reminder.query.filter_by(user_id=current_user.id)
    if status_filter == "upcoming":
        query = query.filter(Reminder.status == "Scheduled", Reminder.due_datetime >= now)
    elif status_filter == "overdue":
        query = query.filter(Reminder.status == "Scheduled", Reminder.due_datetime < now)
    elif status_filter == "sent":
        query = query.filter(Reminder.status == "Sent")
    elif status_filter != "all":
        query = query.filter_by(status=status_filter)

    reminders = query.order_by(Reminder.due_datetime.asc()).all()

    # Counts
    all_rems = Reminder.query.filter_by(user_id=current_user.id).all()
    upcoming_count = sum(1 for r in all_rems if r.status == "Scheduled" and r.due_datetime >= now)
    overdue_count = sum(1 for r in all_rems if r.status == "Scheduled" and r.due_datetime < now)
    sent_count = sum(1 for r in all_rems if r.status == "Sent")

    return render_template(
        "reminders/index.html",
        reminders=reminders,
        current_status=status_filter,
        stats={
            "upcoming": upcoming_count,
            "overdue": overdue_count,
            "sent": sent_count,
            "total": len(all_rems)
        }
    )

@reminders_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        due_datetime_str = request.form.get("due_datetime", "").strip()
        related_type = request.form.get("related_type", "general").strip()

        if not title:
            flash("Reminder title is required.", "danger")
            return render_template("reminders/form.html", action="new")

        if not due_datetime_str:
            flash("Due date and time are required.", "danger")
            return render_template("reminders/form.html", action="new")

        try:
            due_datetime = datetime.strptime(due_datetime_str, "%Y-%m-%dT%H:%M")
        except ValueError:
            flash("Invalid date and time format.", "danger")
            return render_template("reminders/form.html", action="new")

        reminder = Reminder(
            user_id=current_user.id,
            title=title,
            description=description,
            due_datetime=due_datetime,
            related_type=related_type,
            status="Scheduled",
            delivery_channel="in_app"
        )
        db.session.add(reminder)
        db.session.commit()

        flash("Reminder scheduled successfully!", "success")
        return redirect(url_for("reminders.index"))

    return render_template("reminders/form.html", action="new")

@reminders_bp.route("/<int:reminder_id>/dismiss", methods=["POST"])
@login_required
def dismiss(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    reminder.status = "Cancelled"
    db.session.commit()
    flash("Reminder dismissed.", "info")
    return redirect(request.referrer or url_for("reminders.index"))

@reminders_bp.route("/<int:reminder_id>/delete", methods=["POST"])
@login_required
def delete(reminder_id):
    reminder = Reminder.query.filter_by(id=reminder_id, user_id=current_user.id).first_or_404()
    db.session.delete(reminder)
    db.session.commit()
    flash("Reminder deleted.", "info")
    return redirect(url_for("reminders.index"))

@reminders_bp.route("/notifications")
@login_required
def notifications():
    notifications_list = NotificationService.get_user_notifications(current_user.id, limit=50)
    unread_count = NotificationService.get_unread_count(current_user.id)
    return render_template("reminders/notifications.html", notifications=notifications_list, unread_count=unread_count)

@reminders_bp.route("/notifications/<int:notification_id>/read", methods=["POST"])
@login_required
def mark_notification_read(notification_id):
    NotificationService.mark_as_read(notification_id, current_user.id)
    return redirect(request.referrer or url_for("reminders.notifications"))

@reminders_bp.route("/notifications/read-all", methods=["POST"])
@login_required
def mark_all_notifications_read():
    NotificationService.mark_all_as_read(current_user.id)
    flash("All notifications marked as read.", "success")
    return redirect(url_for("reminders.notifications"))

@reminders_bp.route("/notifications/<int:notification_id>/delete", methods=["POST"])
@login_required
def delete_notification(notification_id):
    NotificationService.delete_notification(notification_id, current_user.id)
    return redirect(request.referrer or url_for("reminders.notifications"))

@reminders_bp.route("/api/unread-count")
@login_required
def api_unread_count():
    count = NotificationService.get_unread_count(current_user.id)
    return jsonify({"unread_count": count})
