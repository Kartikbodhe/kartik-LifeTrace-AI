import re
from urllib.parse import urlparse
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from extensions import db, csrf
from models import User

auth_bp = Blueprint("auth", __name__)

def is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(target)
    return test_url.scheme in ("http", "https") and ref_url.netloc == test_url.netloc

@auth_bp.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))
    return render_template("landing.html")

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        full_name = request.form.get("full_name", "").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        errors = []
        if not username or len(username) < 3 or len(username) > 30:
            errors.append("Username must be between 3 and 30 characters.")
        if not re.match(r"^[a-zA-Z0-9_]+$", username):
            errors.append("Username can only contain letters, numbers, and underscores.")
        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            errors.append("Please enter a valid email address.")
        if not password or len(password) < 6:
            errors.append("Password must be at least 6 characters long.")
        if password != confirm_password:
            errors.append("Passwords do not match.")

        if User.query.filter_by(username=username).first():
            errors.append("Username is already taken.")
        if User.query.filter_by(email=email).first():
            errors.append("Email is already registered.")

        if errors:
            for error in errors:
                flash(error, "danger")
            return render_template("auth/register.html", username=username, email=email, full_name=full_name)

        user = User(
            username=username,
            email=email,
            full_name=full_name or username.title()
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash(f"Welcome to LifeTrace AI, {user.full_name or user.username}! Your personal memory assistant is ready.", "success")
        return redirect(url_for("dashboard.index"))

    return render_template("auth/register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        identifier = request.form.get("identifier", "").strip()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))

        if not identifier or not password:
            flash("Please enter both username/email and password.", "danger")
            return render_template("auth/login.html", identifier=identifier)

        user = User.query.filter(
            (User.username == identifier) | (User.email == identifier.lower())
        ).first()

        if user and user.check_password(password):
            login_user(user, remember=remember)
            flash(f"Welcome back, {user.full_name or user.username}!", "success")
            next_page = request.args.get("next")
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for("dashboard.index"))
        else:
            flash("Invalid username/email or password.", "danger")

    return render_template("auth/login.html")

@auth_bp.route("/dev-demo-login", methods=["POST", "GET"])
@csrf.exempt
def dev_demo_login():
    """Development helper: one-click login for testing/demoing."""
    if not current_app.config.get("DEBUG", False) and not current_app.config.get("TESTING", False):
        flash("Demo account login is only available in development mode.", "warning")
        return redirect(url_for("auth.login"))

    demo_user = User.query.filter_by(username="demouser").first()
    if not demo_user:
        demo_user = User(
            username="demouser",
            email="demo@lifetrace.local",
            full_name="Demo User"
        )
        demo_user.set_password("lifetrace123")
        db.session.add(demo_user)
        db.session.commit()

    login_user(demo_user)
    flash("Signed in as Demo User.", "info")
    return redirect(url_for("dashboard.index"))

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for("auth.login"))
