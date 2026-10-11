from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Promise, Reminder

promises_bp = Blueprint("promises", __name__)

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "Completed", "Cancelled"]

@promises_bp.route("/")
@login_required
def index():
    today = date.today()
    query = Promise.query.filter_by(user_id=current_user.id)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            (Promise.title.ilike(f"%{search}%")) |
            (Promise.person_or_org.ilike(f"%{search}%")) |
            (Promise.description.ilike(f"%{search}%"))
        )

    # Status filter
    status = request.args.get("status", "").strip()
    if status == "overdue":
        query = query.filter(
            Promise.status == "Pending",
            Promise.follow_up_date.isnot(None),
            Promise.follow_up_date < today
        )
    elif status in STATUSES:
        query = query.filter_by(status=status)

    # Priority filter
    priority = request.args.get("priority", "").strip()
    if priority in PRIORITIES:
        query = query.filter_by(priority=priority)

    # Sort
    sort_by = request.args.get("sort", "follow_up")
    if sort_by == "newest":
        query = query.order_by(Promise.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Promise.created_at.asc())
    elif sort_by == "priority":
        query = query.order_by(
            db.case(
                (Promise.priority == "High", 1),
                (Promise.priority == "Medium", 2),
                (Promise.priority == "Low", 3),
                else_=4
            )
        )
    else:  # follow_up date
        query = query.order_by(Promise.follow_up_date.asc().nullslast(), Promise.created_at.desc())

    promises = query.all()

    # Aggregate counts for banner
    all_user_promises = Promise.query.filter_by(user_id=current_user.id).all()
    pending_count = sum(1 for p in all_user_promises if p.status == "Pending")
    overdue_count = sum(1 for p in all_user_promises if p.is_overdue)
    completed_count = sum(1 for p in all_user_promises if p.status == "Completed")

    return render_template(
        "promises/index.html",
        promises=promises,
        priorities=PRIORITIES,
        statuses=STATUSES,
        current_status=status,
        current_priority=priority,
        current_sort=sort_by,
        search_query=search,
        stats={
            "pending": pending_count,
            "overdue": overdue_count,
            "completed": completed_count,
            "total": len(all_user_promises)
        }
    )

@promises_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        person_or_org = request.form.get("person_or_org", "").strip()
        description = request.form.get("description", "").strip()
        commitment_date_str = request.form.get("commitment_date", "").strip()
        follow_up_date_str = request.form.get("follow_up_date", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        schedule_reminder = bool(request.form.get("schedule_reminder"))

        errors = []
        if not title:
            errors.append("Commitment title is required.")
        if not person_or_org:
            errors.append("Person or Organization name is required.")

        commit_date = date.today()
        if commitment_date_str:
            try:
                commit_date = datetime.strptime(commitment_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Invalid commitment date.")

        follow_up_date = None
        if follow_up_date_str:
            try:
                follow_up_date = datetime.strptime(follow_up_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Invalid follow-up date.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("promises/form.html", action="new", priorities=PRIORITIES)

        promise = Promise(
            user_id=current_user.id,
            title=title,
            person_or_org=person_or_org,
            description=description,
            commitment_date=commit_date,
            follow_up_date=follow_up_date,
            priority=priority if priority in PRIORITIES else "Medium",
            status="Pending"
        )
        db.session.add(promise)
        db.session.flush()

        if schedule_reminder and follow_up_date:
            due_dt = datetime.combine(follow_up_date, datetime.min.time().replace(hour=9))
            reminder = Reminder(
                user_id=current_user.id,
                title=f"Promise Follow-up: {promise.title} ({promise.person_or_org})",
                description=promise.description or f"Follow-up commitment with {promise.person_or_org}",
                due_datetime=due_dt,
                related_type="promise",
                related_id=promise.id,
                status="Scheduled",
                delivery_channel="in_app"
            )
            db.session.add(reminder)

        db.session.commit()
        flash("Commitment saved successfully!", "success")
        return redirect(url_for("promises.index"))

    return render_template("promises/form.html", action="new", priorities=PRIORITIES, promise=None)

@promises_bp.route("/<int:promise_id>/edit", methods=["GET", "POST"])
@login_required
def edit(promise_id):
    promise = Promise.query.filter_by(id=promise_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        person_or_org = request.form.get("person_or_org", "").strip()
        description = request.form.get("description", "").strip()
        commitment_date_str = request.form.get("commitment_date", "").strip()
        follow_up_date_str = request.form.get("follow_up_date", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        status = request.form.get("status", "Pending").strip()

        errors = []
        if not title:
            errors.append("Commitment title is required.")
        if not person_or_org:
            errors.append("Person or organization is required.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("promises/form.html", action="edit", priorities=PRIORITIES, statuses=STATUSES, promise=promise)

        promise.title = title
        promise.person_or_org = person_or_org
        promise.description = description
        if commitment_date_str:
            promise.commitment_date = datetime.strptime(commitment_date_str, "%Y-%m-%d").date()
        if follow_up_date_str:
            promise.follow_up_date = datetime.strptime(follow_up_date_str, "%Y-%m-%d").date()
        else:
            promise.follow_up_date = None
        promise.priority = priority if priority in PRIORITIES else "Medium"

        if status == "Completed" and promise.status != "Completed":
            promise.mark_complete()
        elif status != "Completed" and promise.status == "Completed":
            promise.mark_reopen()
            promise.status = status
        else:
            promise.status = status if status in STATUSES else promise.status

        db.session.commit()
        flash("Promise updated successfully!", "success")
        return redirect(url_for("promises.index"))

    return render_template("promises/form.html", action="edit", priorities=PRIORITIES, statuses=STATUSES, promise=promise)

@promises_bp.route("/<int:promise_id>/toggle", methods=["POST"])
@login_required
def toggle(promise_id):
    promise = Promise.query.filter_by(id=promise_id, user_id=current_user.id).first_or_404()
    if promise.status == "Completed":
        promise.mark_reopen()
        flash(f"Reopened promise: '{promise.title}'", "info")
    else:
        promise.mark_complete()
        flash(f"Fulfilled commitment: '{promise.title}'! Keep up the integrity.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("promises.index"))

@promises_bp.route("/<int:promise_id>/delete", methods=["POST"])
@login_required
def delete(promise_id):
    promise = Promise.query.filter_by(id=promise_id, user_id=current_user.id).first_or_404()
    db.session.delete(promise)
    db.session.commit()
    flash("Commitment removed.", "info")
    return redirect(url_for("promises.index"))
