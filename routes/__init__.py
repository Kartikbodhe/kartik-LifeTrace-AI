def register_blueprints(app):
    from routes.auth import auth_bp
    from routes.dashboard import dashboard_bp
    from routes.memories import memories_bp
    from routes.tasks import tasks_bp
    from routes.payments import payments_bp
    from routes.promises import promises_bp
    from routes.reminders import reminders_bp
    from routes.calendar import calendar_bp
    from routes.analytics import analytics_bp
    from routes.smart_capture import smart_capture_bp
    from routes.settings import settings_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(memories_bp, url_prefix="/memories")
    app.register_blueprint(tasks_bp, url_prefix="/tasks")
    app.register_blueprint(payments_bp, url_prefix="/payments")
    app.register_blueprint(promises_bp, url_prefix="/promises")
    app.register_blueprint(reminders_bp, url_prefix="/reminders")
    app.register_blueprint(calendar_bp, url_prefix="/calendar")
    app.register_blueprint(analytics_bp, url_prefix="/analytics")
    app.register_blueprint(smart_capture_bp, url_prefix="/smart-capture")
    app.register_blueprint(settings_bp, url_prefix="/settings")
