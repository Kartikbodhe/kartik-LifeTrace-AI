from datetime import datetime, date
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import Memory

memories_bp = Blueprint("memories", __name__)

CATEGORIES = ["Personal", "College", "Work", "Finance", "Project", "Documents", "Other"]

@memories_bp.route("/")
@login_required
def index():
    query = Memory.query.filter_by(user_id=current_user.id)

    # Search
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            (Memory.title.ilike(f"%{search}%")) | (Memory.description.ilike(f"%{search}%"))
        )

    # Filter by category
    category = request.args.get("category", "").strip()
    if category and category in CATEGORIES:
        query = query.filter_by(category=category)

    # Filter by tag
    tag = request.args.get("tag", "").strip()
    if tag:
        query = query.filter(Memory.tags.ilike(f"%{tag}%"))

    # Sort
    sort_by = request.args.get("sort", "newest")
    if sort_by == "oldest":
        query = query.order_by(Memory.created_at.asc())
    elif sort_by == "event_date":
        # Event date sorting with nulls last
        query = query.order_by(Memory.event_date.asc().nullslast(), Memory.created_at.desc())
    else:
        query = query.order_by(Memory.created_at.desc())

    memories = query.all()
    return render_template(
        "memories/index.html",
        memories=memories,
        categories=CATEGORIES,
        current_category=category,
        current_sort=sort_by,
        search_query=search,
        current_tag=tag
    )

@memories_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "Personal").strip()
        tags = request.form.get("tags", "").strip()
        event_date_str = request.form.get("event_date", "").strip()

        if not title:
            flash("Memory title is required.", "danger")
            return render_template("memories/form.html", categories=CATEGORIES, action="new")

        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid event date format.", "danger")
                return render_template("memories/form.html", categories=CATEGORIES, action="new")

        memory = Memory(
            user_id=current_user.id,
            title=title,
            description=description,
            category=category if category in CATEGORIES else "Other",
            tags=tags,
            event_date=event_date,
            status="Active"
        )
        db.session.add(memory)
        db.session.commit()

        flash("Memory saved successfully!", "success")
        return redirect(url_for("memories.index"))

    return render_template("memories/form.html", categories=CATEGORIES, action="new", memory=None)

@memories_bp.route("/<int:memory_id>")
@login_required
def detail(memory_id):
    memory = Memory.query.filter_by(id=memory_id, user_id=current_user.id).first_or_404()
    return render_template("memories/detail.html", memory=memory)

@memories_bp.route("/<int:memory_id>/edit", methods=["GET", "POST"])
@login_required
def edit(memory_id):
    memory = Memory.query.filter_by(id=memory_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        description = request.form.get("description", "").strip()
        category = request.form.get("category", "Personal").strip()
        tags = request.form.get("tags", "").strip()
        event_date_str = request.form.get("event_date", "").strip()

        if not title:
            flash("Memory title is required.", "danger")
            return render_template("memories/form.html", categories=CATEGORIES, action="edit", memory=memory)

        event_date = None
        if event_date_str:
            try:
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
            except ValueError:
                flash("Invalid event date format.", "danger")
                return render_template("memories/form.html", categories=CATEGORIES, action="edit", memory=memory)

        memory.title = title
        memory.description = description
        memory.category = category if category in CATEGORIES else "Other"
        memory.tags = tags
        memory.event_date = event_date
        db.session.commit()

        flash("Memory updated successfully!", "success")
        return redirect(url_for("memories.index"))

    return render_template("memories/form.html", categories=CATEGORIES, action="edit", memory=memory)

@memories_bp.route("/<int:memory_id>/delete", methods=["POST"])
@login_required
def delete(memory_id):
    memory = Memory.query.filter_by(id=memory_id, user_id=current_user.id).first_or_404()
    db.session.delete(memory)
    db.session.commit()
    flash("Memory removed.", "info")
    return redirect(url_for("memories.index"))
