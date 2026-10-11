from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from extensions import db, csrf
from models import Task, PaymentTransaction, Promise, Memory, Reminder
from services.smart_capture_service import SmartCaptureService

smart_capture_bp = Blueprint("smart_capture", __name__)

@smart_capture_bp.route("/")
@login_required
def index():
    return render_template("smart_capture/index.html")

@smart_capture_bp.route("/parse", methods=["POST"])
@csrf.exempt
@login_required
def parse_text():
    data = request.get_json(silent=True) or request.form
    text = data.get("text", "").strip()

    if not text:
        return jsonify({"error": "Please provide input text to analyze."}), 400

    parsed = SmartCaptureService.parse(text)
    return jsonify({"success": True, "data": parsed})

@smart_capture_bp.route("/confirm", methods=["POST"])
@login_required
def confirm_creation():
    target_type = request.form.get("type", "task").strip().lower()
    title = request.form.get("title", "").strip()
    description = request.form.get("description", "").strip()
    category = request.form.get("category", "General").strip()
    date_str = request.form.get("date", "").strip()

    if not title:
        flash("Title is required to create a record.", "danger")
        return redirect(url_for("smart_capture.index"))

    parsed_dt = None
    if date_str:
        for fmt in ["%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M", "%Y-%m-%d"]:
            try:
                parsed_dt = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                pass

    if target_type == "payment":
        person_name = request.form.get("person_name", "Someone").strip()
        amount_str = request.form.get("amount", "0").strip()
        transaction_type = request.form.get("transaction_type", "LENT").strip().upper()

        try:
            amount = Decimal(amount_str).quantize(Decimal("0.01"))
        except (InvalidOperation, ValueError):
            amount = Decimal("100.00")

        exp_date = parsed_dt.date() if parsed_dt else None

        payment = PaymentTransaction(
            user_id=current_user.id,
            person_name=person_name,
            amount=amount,
            transaction_type=transaction_type if transaction_type in ["LENT", "BORROWED"] else "LENT",
            transaction_date=date.today(),
            expected_repayment_date=exp_date,
            description=description or f"Captured via Smart Capture: {title}",
            status="Pending"
        )
        db.session.add(payment)
        db.session.commit()
        flash(f"Payment entry for ₹{amount} with {person_name} created successfully!", "success")
        return redirect(url_for("payments.detail", payment_id=payment.id))

    elif target_type == "promise":
        person_or_org = request.form.get("person_or_org", "Collaborator").strip()
        follow_up_date = parsed_dt.date() if parsed_dt else None

        promise = Promise(
            user_id=current_user.id,
            title=title,
            person_or_org=person_or_org,
            description=description or f"Captured via Smart Capture",
            commitment_date=date.today(),
            follow_up_date=follow_up_date,
            priority="Medium",
            status="Pending"
        )
        db.session.add(promise)
        db.session.commit()
        flash(f"Commitment with {person_or_org} recorded successfully!", "success")
        return redirect(url_for("promises.index"))

    elif target_type == "memory":
        event_date = parsed_dt.date() if parsed_dt else None
        memory = Memory(
            user_id=current_user.id,
            title=title,
            description=description or title,
            category=category if category in ["Personal", "College", "Work", "Finance", "Project", "Documents", "Other"] else "Personal",
            tags="smart-capture",
            event_date=event_date,
            status="Active"
        )
        db.session.add(memory)
        db.session.commit()
        flash("Personal memory note preserved successfully!", "success")
        return redirect(url_for("memories.index"))

    else:  # Task (default)
        priority = request.form.get("priority", "Medium").strip()
        task = Task(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority if priority in ["Low", "Medium", "High"] else "Medium",
            category=category,
            due_date=parsed_dt,
            status="Pending"
        )
        db.session.add(task)
        db.session.flush()

        # If user checked reminder
        if request.form.get("create_reminder") and parsed_dt:
            rem = Reminder(
                user_id=current_user.id,
                title=f"Task Due: {task.title}",
                description=description or f"Smart capture reminder for {task.title}",
                due_datetime=parsed_dt,
                related_type="task",
                related_id=task.id,
                status="Scheduled",
                delivery_channel="in_app"
            )
            db.session.add(rem)

        db.session.commit()
        flash(f"Task '{task.title}' confirmed and created!", "success")
        return redirect(url_for("tasks.index"))
