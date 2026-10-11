from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from flask import Blueprint, render_template, request, redirect, url_for, flash, abort
from flask_login import login_required, current_user
from extensions import db
from models import PaymentTransaction, Repayment, Reminder

payments_bp = Blueprint("payments", __name__)

TRANSACTION_TYPES = ["LENT", "BORROWED"]
STATUSES = ["Pending", "Partially Paid", "Settled"]

@payments_bp.route("/")
@login_required
def index():
    today = date.today()
    query = PaymentTransaction.query.filter_by(user_id=current_user.id)

    # Search by person name or description
    search = request.args.get("search", "").strip()
    if search:
        query = query.filter(
            (PaymentTransaction.person_name.ilike(f"%{search}%")) |
            (PaymentTransaction.description.ilike(f"%{search}%"))
        )

    # Type filter (LENT or BORROWED)
    t_type = request.args.get("type", "").strip().upper()
    if t_type in TRANSACTION_TYPES:
        query = query.filter_by(transaction_type=t_type)

    # Status filter
    status = request.args.get("status", "").strip()
    if status == "overdue":
        query = query.filter(
            PaymentTransaction.status.in_(["Pending", "Partially Paid"]),
            PaymentTransaction.expected_repayment_date.isnot(None),
            PaymentTransaction.expected_repayment_date < today
        )
    elif status in STATUSES:
        query = query.filter_by(status=status)

    # Sorting
    sort_by = request.args.get("sort", "newest")
    if sort_by == "expected_date":
        query = query.order_by(PaymentTransaction.expected_repayment_date.asc().nullslast())
    elif sort_by == "amount_high":
        query = query.order_by(PaymentTransaction.amount.desc())
    elif sort_by == "oldest":
        query = query.order_by(PaymentTransaction.transaction_date.asc())
    else:
        query = query.order_by(PaymentTransaction.transaction_date.desc(), PaymentTransaction.created_at.desc())

    transactions = query.all()

    # Aggregate summaries across all user's transactions
    all_transactions = PaymentTransaction.query.filter_by(user_id=current_user.id).all()
    lent_list = [p for p in all_transactions if p.transaction_type == "LENT"]
    borrowed_list = [p for p in all_transactions if p.transaction_type == "BORROWED"]

    total_lent_original = sum((p.amount for p in lent_list), Decimal("0.00"))
    total_lent_outstanding = sum((p.remaining_balance for p in lent_list if p.status != "Settled"), Decimal("0.00"))
    total_lent_recovered = sum((p.total_repaid for p in lent_list), Decimal("0.00"))

    total_borrowed_original = sum((p.amount for p in borrowed_list), Decimal("0.00"))
    total_borrowed_outstanding = sum((p.remaining_balance for p in borrowed_list if p.status != "Settled"), Decimal("0.00"))
    total_borrowed_repaid = sum((p.total_repaid for p in borrowed_list), Decimal("0.00"))

    return render_template(
        "payments/index.html",
        transactions=transactions,
        transaction_types=TRANSACTION_TYPES,
        statuses=STATUSES,
        current_type=t_type,
        current_status=status,
        current_sort=sort_by,
        search_query=search,
        summary={
            "lent_outstanding": total_lent_outstanding,
            "lent_recovered": total_lent_recovered,
            "lent_original": total_lent_original,
            "borrowed_outstanding": total_borrowed_outstanding,
            "borrowed_repaid": total_borrowed_repaid,
            "borrowed_original": total_borrowed_original,
            "total_records": len(all_transactions)
        }
    )

@payments_bp.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        person_name = request.form.get("person_name", "").strip()
        amount_str = request.form.get("amount", "").strip()
        transaction_type = request.form.get("transaction_type", "LENT").strip().upper()
        transaction_date_str = request.form.get("transaction_date", "").strip()
        expected_date_str = request.form.get("expected_repayment_date", "").strip()
        description = request.form.get("description", "").strip()
        schedule_reminder = bool(request.form.get("schedule_reminder"))

        errors = []
        if not person_name:
            errors.append("Person's name or nickname is required.")

        try:
            amount = Decimal(amount_str).quantize(Decimal("0.01"))
            if amount <= Decimal("0.00"):
                errors.append("Amount must be greater than zero.")
        except (InvalidOperation, ValueError, TypeError):
            errors.append("Please enter a valid monetary amount.")

        if transaction_type not in TRANSACTION_TYPES:
            errors.append("Invalid transaction type.")

        transaction_date = date.today()
        if transaction_date_str:
            try:
                transaction_date = datetime.strptime(transaction_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Invalid transaction date format.")

        expected_date = None
        if expected_date_str:
            try:
                expected_date = datetime.strptime(expected_date_str, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Invalid expected repayment date format.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("payments/form.html", action="new", transaction_types=TRANSACTION_TYPES)

        payment = PaymentTransaction(
            user_id=current_user.id,
            person_name=person_name,
            amount=amount,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            expected_repayment_date=expected_date,
            description=description,
            status="Pending"
        )
        db.session.add(payment)
        db.session.flush()

        if schedule_reminder and expected_date:
            due_dt = datetime.combine(expected_date, datetime.min.time().replace(hour=10))
            direction = "collecting from" if transaction_type == "LENT" else "repaying to"
            reminder = Reminder(
                user_id=current_user.id,
                title=f"Payment Due: ₹{amount} ({direction} {person_name})",
                description=f"Expected repayment date for ₹{amount} is today.",
                due_datetime=due_dt,
                related_type="payment",
                related_id=payment.id,
                status="Scheduled",
                delivery_channel="in_app"
            )
            db.session.add(reminder)

        db.session.commit()
        flash(f"Payment record for ₹{amount} ({'Lent' if transaction_type == 'LENT' else 'Borrowed'}) saved successfully!", "success")
        return redirect(url_for("payments.index"))

    return render_template("payments/form.html", action="new", transaction_types=TRANSACTION_TYPES, payment=None)

@payments_bp.route("/<int:payment_id>")
@login_required
def detail(payment_id):
    payment = PaymentTransaction.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    return render_template("payments/detail.html", payment=payment)

@payments_bp.route("/<int:payment_id>/edit", methods=["GET", "POST"])
@login_required
def edit(payment_id):
    payment = PaymentTransaction.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()

    if request.method == "POST":
        person_name = request.form.get("person_name", "").strip()
        amount_str = request.form.get("amount", "").strip()
        transaction_type = request.form.get("transaction_type", "LENT").strip().upper()
        transaction_date_str = request.form.get("transaction_date", "").strip()
        expected_date_str = request.form.get("expected_repayment_date", "").strip()
        description = request.form.get("description", "").strip()

        errors = []
        if not person_name:
            errors.append("Person's name is required.")

        try:
            amount = Decimal(amount_str).quantize(Decimal("0.01"))
            if amount < payment.total_repaid:
                errors.append(f"Total amount cannot be less than the already repaid amount (₹{payment.total_repaid}).")
        except (InvalidOperation, ValueError, TypeError):
            errors.append("Invalid amount.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("payments/form.html", action="edit", transaction_types=TRANSACTION_TYPES, payment=payment)

        payment.person_name = person_name
        payment.amount = amount
        payment.transaction_type = transaction_type if transaction_type in TRANSACTION_TYPES else payment.transaction_type
        if transaction_date_str:
            payment.transaction_date = datetime.strptime(transaction_date_str, "%Y-%m-%d").date()
        if expected_date_str:
            payment.expected_repayment_date = datetime.strptime(expected_date_str, "%Y-%m-%d").date()
        else:
            payment.expected_repayment_date = None
        payment.description = description

        payment.update_settlement_status()
        db.session.commit()

        flash("Payment record updated successfully!", "success")
        return redirect(url_for("payments.detail", payment_id=payment.id))

    return render_template("payments/form.html", action="edit", transaction_types=TRANSACTION_TYPES, payment=payment)

@payments_bp.route("/<int:payment_id>/repay", methods=["POST"])
@login_required
def add_repayment(payment_id):
    payment = PaymentTransaction.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    amount_str = request.form.get("amount", "").strip()
    repayment_date_str = request.form.get("repayment_date", "").strip()
    notes = request.form.get("notes", "").strip()

    try:
        amount = Decimal(amount_str).quantize(Decimal("0.01"))
        if amount <= Decimal("0.00"):
            flash("Repayment amount must be greater than zero.", "danger")
            return redirect(url_for("payments.detail", payment_id=payment.id))
        if amount > payment.remaining_balance:
            flash(f"Repayment amount cannot exceed remaining balance of ₹{payment.remaining_balance}.", "danger")
            return redirect(url_for("payments.detail", payment_id=payment.id))
    except (InvalidOperation, ValueError, TypeError):
        flash("Invalid repayment amount.", "danger")
        return redirect(url_for("payments.detail", payment_id=payment.id))

    repay_date = date.today()
    if repayment_date_str:
        try:
            repay_date = datetime.strptime(repayment_date_str, "%Y-%m-%d").date()
        except ValueError:
            pass

    repayment = Repayment(
        payment_id=payment.id,
        user_id=current_user.id,
        amount=amount,
        repayment_date=repay_date,
        notes=notes
    )
    db.session.add(repayment)
    db.session.flush()

    payment.update_settlement_status()
    db.session.commit()

    if payment.status == "Settled":
        flash(f"Recorded repayment of ₹{amount}. The transaction is now fully SETTLED! 🎉", "success")
    else:
        flash(f"Recorded partial repayment of ₹{amount}. Remaining balance: ₹{payment.remaining_balance}.", "info")

    return redirect(url_for("payments.detail", payment_id=payment.id))

@payments_bp.route("/repayments/<int:repayment_id>/delete", methods=["POST"])
@login_required
def delete_repayment(repayment_id):
    repayment = Repayment.query.filter_by(id=repayment_id, user_id=current_user.id).first_or_404()
    payment = repayment.transaction
    db.session.delete(repayment)
    db.session.flush()

    payment.update_settlement_status()
    db.session.commit()

    flash("Repayment entry deleted and balance recalculated.", "info")
    return redirect(url_for("payments.detail", payment_id=payment.id))

@payments_bp.route("/<int:payment_id>/delete", methods=["POST"])
@login_required
def delete(payment_id):
    payment = PaymentTransaction.query.filter_by(id=payment_id, user_id=current_user.id).first_or_404()
    db.session.delete(payment)
    db.session.commit()
    flash("Payment record deleted.", "info")
    return redirect(url_for("payments.index"))
