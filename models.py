from datetime import datetime, date
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    timezone = db.Column(db.String(64), default="Asia/Kolkata")
    currency = db.Column(db.String(8), default="₹")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    memories = db.relationship("Memory", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    tasks = db.relationship("Task", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    payments = db.relationship("PaymentTransaction", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    repayments = db.relationship("Repayment", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    promises = db.relationship("Promise", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    reminders = db.relationship("Reminder", backref="user", cascade="all, delete-orphan", lazy="dynamic")
    notifications = db.relationship("Notification", backref="user", cascade="all, delete-orphan", lazy="dynamic")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.username}>"

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


class Memory(db.Model):
    __tablename__ = "memories"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), default="Personal", nullable=False)  # Personal, College, Work, Finance, Project, Documents, Other
    tags = db.Column(db.String(255), default="")  # comma-separated tags
    event_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.String(20), default="Active")  # Active, Archived
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def tag_list(self):
        if not self.tags:
            return []
        return [t.strip() for t in self.tags.split(",") if t.strip()]

    def __repr__(self):
        return f"<Memory {self.title}>"


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="", nullable=True)
    priority = db.Column(db.String(20), default="Medium", nullable=False)  # Low, Medium, High
    category = db.Column(db.String(50), default="General", nullable=False)
    due_date = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="Pending", nullable=False)  # Pending, In Progress, Completed
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_overdue(self):
        if self.status == "Completed" or not self.due_date:
            return False
        return self.due_date < datetime.utcnow()

    @property
    def is_due_today(self):
        if not self.due_date:
            return False
        return self.due_date.date() == date.today()

    def mark_complete(self):
        self.status = "Completed"
        self.completed_at = datetime.utcnow()

    def mark_reopen(self):
        self.status = "Pending"
        self.completed_at = None

    def __repr__(self):
        return f"<Task {self.title} [{self.status}]>"


class PaymentTransaction(db.Model):
    __tablename__ = "payment_transactions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    person_name = db.Column(db.String(120), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    transaction_type = db.Column(db.String(20), nullable=False)  # LENT, BORROWED
    transaction_date = db.Column(db.Date, default=date.today, nullable=False)
    expected_repayment_date = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, default="", nullable=True)
    status = db.Column(db.String(20), default="Pending", nullable=False)  # Pending, Partially Paid, Settled
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Repayment history
    repayments = db.relationship("Repayment", backref="transaction", cascade="all, delete-orphan", lazy="select", order_by="desc(Repayment.repayment_date)")

    @property
    def total_repaid(self):
        # Query directly from DB/session so it is always completely synchronized
        records = Repayment.query.filter_by(payment_id=self.id).all()
        total = sum((r.amount for r in records), Decimal("0.00"))
        return Decimal(total).quantize(Decimal("0.01"))

    @property
    def remaining_balance(self):
        balance = Decimal(self.amount) - self.total_repaid
        return max(Decimal("0.00"), balance).quantize(Decimal("0.01"))

    @property
    def is_overdue(self):
        if self.status == "Settled" or not self.expected_repayment_date:
            return False
        return self.expected_repayment_date < date.today()

    def update_settlement_status(self):
        balance = self.remaining_balance
        if balance <= Decimal("0.00"):
            self.status = "Settled"
        elif self.total_repaid > Decimal("0.00"):
            self.status = "Partially Paid"
        else:
            self.status = "Pending"

    def __repr__(self):
        return f"<Payment {self.transaction_type} {self.amount} - {self.person_name}>"


class Repayment(db.Model):
    __tablename__ = "repayments"

    id = db.Column(db.Integer, primary_key=True)
    payment_id = db.Column(db.Integer, db.ForeignKey("payment_transactions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    repayment_date = db.Column(db.Date, default=date.today, nullable=False)
    notes = db.Column(db.Text, default="", nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Repayment {self.amount} on {self.repayment_date}>"


class Promise(db.Model):
    __tablename__ = "promises"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    person_or_org = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text, default="", nullable=True)
    commitment_date = db.Column(db.Date, default=date.today, nullable=False)
    follow_up_date = db.Column(db.Date, nullable=True)
    priority = db.Column(db.String(20), default="Medium", nullable=False)  # Low, Medium, High
    status = db.Column(db.String(20), default="Pending", nullable=False)  # Pending, Completed, Cancelled
    completed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @property
    def is_overdue(self):
        if self.status != "Pending" or not self.follow_up_date:
            return False
        return self.follow_up_date < date.today()

    def mark_complete(self):
        self.status = "Completed"
        self.completed_at = datetime.utcnow()

    def mark_reopen(self):
        self.status = "Pending"
        self.completed_at = None

    def __repr__(self):
        return f"<Promise {self.title} to {self.person_or_org}>"


class Reminder(db.Model):
    __tablename__ = "reminders"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="", nullable=True)
    due_datetime = db.Column(db.DateTime, nullable=False)
    related_type = db.Column(db.String(50), default="general")  # task, payment, promise, memory, general
    related_id = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default="Scheduled", nullable=False)  # Scheduled, Sent, Failed, Cancelled
    delivery_channel = db.Column(db.String(50), default="in_app")  # in_app, browser, email
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notifications = db.relationship("Notification", backref="reminder", cascade="all, delete-orphan", lazy="dynamic")

    @property
    def is_overdue(self):
        return self.status == "Scheduled" and self.due_datetime < datetime.utcnow()

    def __repr__(self):
        return f"<Reminder {self.title} at {self.due_datetime}>"


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    reminder_id = db.Column(db.Integer, db.ForeignKey("reminders.id", ondelete="SET NULL"), nullable=True)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), default="reminder")  # task_due, payment_due, promise_due, reminder, system
    is_read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Notification {self.title} read={self.is_read}>"
