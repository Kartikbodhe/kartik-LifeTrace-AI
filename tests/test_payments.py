import pytest
from decimal import Decimal
from datetime import date
from models import PaymentTransaction, Repayment
from extensions import db

def test_create_payment(client, auth, user1, app):
    auth.login("user_one", "password123")

    resp = client.post("/payments/new", data={
        "person_name": "Rohan Sharma",
        "amount": "2500.50",
        "transaction_type": "LENT",
        "transaction_date": str(date.today()),
        "description": "Shared festival flight ticket"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"saved successfully" in resp.data

    with app.app_context():
        p = PaymentTransaction.query.filter_by(person_name="Rohan Sharma").first()
        assert p is not None
        assert p.amount == Decimal("2500.50")
        assert p.remaining_balance == Decimal("2500.50")
        assert p.status == "Pending"

def test_partial_repayment_and_settlement(client, auth, user1, app):
    auth.login("user_one", "password123")

    with app.app_context():
        p = PaymentTransaction(
            user_id=user1,
            person_name="Amit Patel",
            amount=Decimal("1000.00"),
            transaction_type="LENT",
            status="Pending"
        )
        db.session.add(p)
        db.session.commit()
        payment_id = p.id

    # 1. Partial Repayment of 400.00
    resp1 = client.post(f"/payments/{payment_id}/repay", data={
        "amount": "400.00",
        "notes": "First UPI transfer"
    }, follow_redirects=True)
    assert resp1.status_code == 200

    with app.app_context():
        p = db.session.get(PaymentTransaction, payment_id)
        assert p.total_repaid == Decimal("400.00")
        assert p.remaining_balance == Decimal("600.00")
        assert p.status == "Partially Paid"
        assert len(p.repayments) == 1

    # 2. Final Repayment of remaining 600.00
    resp2 = client.post(f"/payments/{payment_id}/repay", data={
        "amount": "600.00",
        "notes": "Final settlement"
    }, follow_redirects=True)
    assert resp2.status_code == 200

    with app.app_context():
        p = db.session.get(PaymentTransaction, payment_id)
        assert p.total_repaid == Decimal("1000.00")
        assert p.remaining_balance == Decimal("0.00")
        assert p.status == "Settled"

def test_repayment_validation_overflow(client, auth, user1, app):
    auth.login("user_one", "password123")

    with app.app_context():
        p = PaymentTransaction(
            user_id=user1,
            person_name="Deepak",
            amount=Decimal("500.00"),
            transaction_type="BORROWED",
            status="Pending"
        )
        db.session.add(p)
        db.session.commit()
        payment_id = p.id

    # Try repaying 600 on a 500 balance
    resp = client.post(f"/payments/{payment_id}/repay", data={
        "amount": "600.00"
    }, follow_redirects=True)

    assert b"cannot exceed remaining balance" in resp.data

    with app.app_context():
        p = db.session.get(PaymentTransaction, payment_id)
        assert p.remaining_balance == Decimal("500.00")
        assert p.status == "Pending"

def test_cross_user_payment_protection(client, auth, user1, user2, app):
    with app.app_context():
        p = PaymentTransaction(
            user_id=user1,
            person_name="Secret Borrower",
            amount=Decimal("10000.00"),
            transaction_type="LENT",
            status="Pending"
        )
        db.session.add(p)
        db.session.commit()
        payment_id = p.id

    # Log in as User 2
    auth.login("user_two", "password123")

    # Try accessing User 1's payment
    resp = client.get(f"/payments/{payment_id}")
    assert resp.status_code == 404

    # Try deleting User 1's payment
    resp_del = client.post(f"/payments/{payment_id}/delete")
    assert resp_del.status_code == 404
