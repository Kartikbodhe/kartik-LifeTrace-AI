import os
from datetime import datetime
from flask import Flask, render_template
from config import config_by_name
from extensions import db, login_manager, csrf
from routes import register_blueprints
from services.reminder_service import init_scheduler
from services.notification_service import NotificationService
from flask_login import current_user

def create_app(config_name=None):
    """Application factory for LifeTrace AI."""
    if config_name is None:
        config_name = os.environ.get("FLASK_ENV", "development").lower()

    app = Flask(__name__)
    app.config.from_object(config_by_name.get(config_name, config_by_name["default"]))

    # Ensure instance folder exists
    os.makedirs(app.instance_path, exist_ok=True)

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    # Register all application blueprints
    register_blueprints(app)

    # Health check endpoint for uptime monitors & Render
    @app.route("/health")
    def health_check():
        return {"status": "ok", "app": "LifeTrace-AI"}, 200

    # Global context processors for templates
    @app.context_processor
    def inject_global_template_data():
        unread_count = 0
        currency = app.config.get("DEFAULT_CURRENCY", "₹")
        if current_user.is_authenticated:
            unread_count = NotificationService.get_unread_count(current_user.id)
            if hasattr(current_user, "currency") and current_user.currency:
                currency = current_user.currency
        return {
            "unread_count": unread_count,
            "currency_symbol": currency,
            "current_year": datetime.utcnow().year,
            "now_utc": datetime.utcnow()
        }

    # Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("errors/400.html", error=error), 400

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("errors/500.html", error=error), 500

    # Auto-initialize database tables in dev/testing
    with app.app_context():
        db.create_all()

    # Initialize background scheduler for reminders
    init_scheduler(app)

    return app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
