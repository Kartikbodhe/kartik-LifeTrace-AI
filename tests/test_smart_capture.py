import pytest
from services.smart_capture_service import SmartCaptureService

def test_smart_capture_task_parsing():
    res = SmartCaptureService.parse("Remind me on Friday to submit my college project report")
    assert res["type"] == "task"
    assert "submit my college project report" in res["title"].lower()
    assert res["category"] == "College"
    assert res["suggested_datetime"] is not None
    assert res["confidence"] >= 0.8

def test_smart_capture_payment_lent():
    res = SmartCaptureService.parse("Lent ₹500 to Rahul until tomorrow")
    assert res["type"] == "payment"
    assert res["transaction_type"] == "LENT"
    assert res["person_name"] == "Rahul"
    assert res["amount"] == "500"
    assert res["suggested_date"] is not None

def test_smart_capture_payment_borrowed():
    res = SmartCaptureService.parse("Borrowed ₹2000 from Priya due next month")
    assert res["type"] == "payment"
    assert res["transaction_type"] == "BORROWED"
    assert res["person_name"] == "Priya"
    assert res["amount"] == "2000"

def test_smart_capture_promise():
    res = SmartCaptureService.parse("Promised Dr. Sharma to send thesis draft by Monday")
    assert res["type"] == "promise"
    assert "Dr. Sharma" in res["person_or_org"]
    assert res["suggested_date"] is not None

def test_smart_capture_confirm_flow(client, auth, user1):
    auth.login("user_one", "password123")

    # Confirm and save parsed task
    resp = client.post("/smart-capture/confirm", data={
        "type": "task",
        "title": "Submit assignment",
        "category": "College",
        "date": "2026-11-20 17:00",
        "priority": "High",
        "create_reminder": "1",
        "description": "Original expression captured"
    }, follow_redirects=True)

    assert resp.status_code == 200
    assert b"confirmed and created" in resp.data
