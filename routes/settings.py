from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, Response
from flask_login import login_required, current_user, logout_user
from extensions import db
from models import User, Task, Memory, PaymentTransaction, Promise, Reminder, Notification
import json

settings_bp = Blueprint("settings", __name__)

@settings_bp.route("/", methods=["GET", "POST"])
@login_required
def index():
    if request.method == "POST":
        action = request.form.get("action")

        if action == "update_profile":
            full_name = request.form.get("full_name", "").strip()
            timezone = request.form.get("timezone", "Asia/Kolkata").strip()
            currency = request.form.get("currency", "₹").strip()

            current_user.full_name = full_name
            current_user.timezone = timezone
            current_user.currency = currency
            db.session.commit()
            flash("Profile preferences updated successfully!", "success")
            return redirect(url_for("settings.index"))

        elif action == "change_password":
            current_password = request.form.get("current_password", "")
            new_password = request.form.get("new_password", "")
            confirm_password = request.form.get("confirm_password", "")

            if not current_user.check_password(current_password):
                flash("Incorrect current password.", "danger")
                return redirect(url_for("settings.index"))

            if len(new_password) < 6:
                flash("New password must be at least 6 characters.", "danger")
                return redirect(url_for("settings.index"))

            if new_password != confirm_password:
                flash("New passwords do not match.", "danger")
                return redirect(url_for("settings.index"))

            current_user.set_password(new_password)
            db.session.commit()
            flash("Password updated successfully!", "success")
            return redirect(url_for("settings.index"))

    return render_template("settings/index.html")

@settings_bp.route("/export-data")
@login_required
def export_data():
    """Export complete user data snapshot in portable JSON format."""
    tasks = [
        {
            "id": t.id,
            "title": t.title,
            "description": t.description,
            "priority": t.priority,
            "category": t.category,
            "status": t.status,
            "due_date": t.due_date.isoformat() if t.due_date else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
            "created_at": t.created_at.isoformat()
        }
        for t in Task.query.filter_by(user_id=current_user.id).all()
    ]

    memories = [
        {
            "id": m.id,
            "title": m.title,
            "description": m.description,
            "category": m.category,
            "tags": m.tags,
            "event_date": m.event_date.isoformat() if m.event_date else None,
            "status": m.status,
            "created_at": m.created_at.isoformat()
        }
        for m in Memory.query.filter_by(user_id=current_user.id).all()
    ]

    payments = [
        {
            "id": p.id,
            "person_name": p.person_name,
            "amount": float(p.amount),
            "remaining_balance": float(p.remaining_balance),
            "transaction_type": p.transaction_type,
            "transaction_date": p.transaction_date.isoformat(),
            "expected_repayment_date": p.expected_repayment_date.isoformat() if p.expected_repayment_date else None,
            "status": p.status,
            "repayments": [
                {
                    "amount": float(r.amount),
                    "repayment_date": r.repayment_date.isoformat(),
                    "notes": r.notes
                }
                for r in p.repayments
            ]
        }
        for p in PaymentTransaction.query.filter_by(user_id=current_user.id).all()
    ]

    promises = [
        {
            "id": pr.id,
            "title": pr.title,
            "person_or_org": pr.person_or_org,
            "description": pr.description,
            "commitment_date": pr.commitment_date.isoformat(),
            "follow_up_date": pr.follow_up_date.isoformat() if pr.follow_up_date else None,
            "priority": pr.priority,
            "status": pr.status
        }
        for pr in Promise.query.filter_by(user_id=current_user.id).all()
    ]

    export_payload = {
        "user": {
            "username": current_user.username,
            "email": current_user.email,
            "full_name": current_user.full_name
        },
        "tasks": tasks,
        "memories": memories,
        "payments": payments,
        "promises": promises,
        "exported_at": str(db.func.current_timestamp())
    }

    return Response(
        json.dumps(export_payload, indent=2),
        mimetype="application/json",
        headers={"Content-Disposition": f"attachment;filename=lifetrace_backup_{current_user.username}.json"}
    )

@settings_bp.route("/delete-account", methods=["POST"])
@login_required
def delete_account():
    confirmation = request.form.get("confirmation", "").strip()
    if confirmation != current_user.username:
        flash("Account deletion canceled: Username confirmation mismatch.", "danger")
        return redirect(url_for("settings.index"))

    user = current_user._get_current_object()
    logout_user()
    db.session.delete(user)
    db.session.commit()
    flash("Your account and all associated records have been permanently deleted.", "info")
    return redirect(url_for("auth.login"))
