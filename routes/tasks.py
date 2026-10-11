from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from extensions import db
from models import Task, Reminder

tasks_bp = Blueprint("tasks", __name__)

PRIORITIES = ["Low", "Medium", "High"]
STATUSES = ["Pending", "In Progress", "Completed"]
CATEGORIES = ["General", "Work", "College", "Personal", "Urgent", "Project"]

@tasks_bp.route("/")
@login_required
def index():
    now = datetime.utcnow()
    query = Task.query.filter_by(user_id=current_user.id)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            (Task.title.ilike(f"%{search}%")) | (Task.description.ilike(f"%{search}%"))
        )

    # Status filter
    status = request.args.get("status", "").strip()
    if status == "overdue":
        query = query.filter(
            Task.status.in_(["Pending", "In Progress"]),
            Task.due_date.isnot(None),
            Task.due_date < now
        )
    elif status in STATUSES:
        query = query.filter_by(status=status)

    # Priority filter
    priority = request.args.get("priority", "").strip()
    if priority in PRIORITIES:
        query = query.filter_by(priority=priority)

    # Category filter
    category = request.args.get("category", "").strip()
    if category and category in CATEGORIES:
        query = query.filter_by(category=category)

    # Sort
    sort_by = request.args.get("sort", "due_date")
    if sort_by == "priority":
        # Order High, Medium, Low
        query = query.order_by(
            db.case(
                (Task.priority == "High", 1),
                (Task.priority == "Medium", 2),
                (Task.priority == "Low", 3),
                else_=4
            )
        )
    elif sort_by == "newest":
        query = query.order_by(Task.created_at.desc())
    elif sort_by == "oldest":
        query = query.order_by(Task.created_at.asc())
    else:  # due_date
        query = query.order_by(Task.due_date.asc().nullslast(), Task.created_at.desc())

    tasks = query.all()

    # Overall stats for banner
    all_user_tasks = Task.query.filter_by(user_id=current_user.id).all()
    overdue_count = sum(1 for t in all_user_tasks if t.is_overdue)
    completed_count = sum(1 for t in all_user_tasks if t.status == "Completed")
    pending_count = sum(1 for t in all_user_tasks if t.status != "Completed")

    return render_template(
        "tasks/index.html",
        tasks=tasks,
        priorities=PRIORITIES,
        statuses=STATUSES,
        categories=CATEGORIES,
        current_status=status,
        current_priority=priority,
        current_category=category,
        current_sort=sort_by,
        search_query=search,
        stats={
            "overdue": overdue_count,
            "completed": completed_count,
            "pending": pending_count,
            "total": len(all_user_tasks)
        }
    )

@tasks_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        category = request.form.get("category", "General").strip()
        due_date_str = request.form.get("due_date", "").strip()
        create_reminder = bool(request.form.get("create_reminder"))

        if not title:
            flash("Task title is required.", "danger")
            return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, action="new")

        due_date = None
        if due_date_str:
            try:
                # Expecting HTML datetime-local format 'YYYY-MM-DDTHH:MM'
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid due date or time format.", "danger")
                    return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, action="new")

        task = Task(
            user_id=current_user.id,
            title=title,
            description=description,
            priority=priority if priority in PRIORITIES else "Medium",
            category=category if category in CATEGORIES else "General",
            due_date=due_date,
            status="Pending"
        )
        db.session.add(task)
        db.session.flush()

        # If user checked "Set reminder for this task"
        if create_reminder and due_date:
            reminder = Reminder(
                user_id=current_user.id,
                title=f"Task Due: {task.title}",
                description=task.description or f"Deadline reached for {task.title}",
                due_datetime=due_date,
                related_type="task",
                related_id=task.id,
                status="Scheduled",
                delivery_channel="in_app"
            )
            db.session.add(reminder)

        db.session.commit()
        flash("Task created successfully!", "success")
        return redirect(url_for("tasks.index"))

    return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, action="new", task=None)

@tasks_bp.route("/<int:task_id>/edit", methods=["GET", "POST"])
@login_required
def edit(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        priority = request.form.get("priority", "Medium").strip()
        category = request.form.get("category", "General").strip()
        status = request.form.get("status", "Pending").strip()
        due_date_str = request.form.get("due_date", "").strip()

        if not title:
            flash("Task title is required.", "danger")
            return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, statuses=STATUSES, action="edit", task=task)

        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%dT%H:%M")
            except ValueError:
                try:
                    due_date = datetime.strptime(due_date_str, "%Y-%m-%d")
                except ValueError:
                    flash("Invalid due date or time format.", "danger")
                    return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, statuses=STATUSES, action="edit", task=task)

        task.title = title
        task.description = description
        task.priority = priority if priority in PRIORITIES else "Medium"
        task.category = category if category in CATEGORIES else "General"
        task.due_date = due_date

        if status == "Completed" and task.status != "Completed":
            task.mark_complete()
        elif status != "Completed" and task.status == "Completed":
            task.mark_reopen()
            task.status = status
        else:
            task.status = status if status in STATUSES else task.status

        db.session.commit()
        flash("Task updated successfully!", "success")
        return redirect(url_for("tasks.index"))

    return render_template("tasks/form.html", priorities=PRIORITIES, categories=CATEGORIES, statuses=STATUSES, action="edit", task=task)

@tasks_bp.route("/<int:task_id>/toggle", methods=["POST"])
@login_required
def toggle(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    if task.status == "Completed":
        task.mark_reopen()
        flash(f"Reopened task: '{task.title}'", "info")
    else:
        task.mark_complete()
        flash(f"Completed task: '{task.title}'! Great job.", "success")
    db.session.commit()
    return redirect(request.referrer or url_for("tasks.index"))

@tasks_bp.route("/<int:task_id>/delete", methods=["POST"])
@login_required
def delete(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    flash("Task deleted.", "info")
    return redirect(url_for("tasks.index"))
