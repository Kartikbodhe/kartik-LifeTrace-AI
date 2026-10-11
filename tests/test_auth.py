import pytest
from models import User
from extensions import db

def test_register_success(client, app):
    response = client.post("/register", data={
        "username": "alice",
        "email": "alice@example.com",
        "full_name": "Alice Wonderland",
        "password": "securepassword123",
        "confirm_password": "securepassword123"
    }, follow_redirects=True)

    assert response.status_code == 200
    assert b"Welcome to LifeTrace AI" in response.data

    with app.app_context():
        user = User.query.filter_by(username="alice").first()
        assert user is not None
        assert user.check_password("securepassword123")
        assert not user.check_password("wrongpass")
        assert user.password_hash != "securepassword123"  # Never plaintext

def test_register_validation(client, app):
    # Short username
    resp = client.post("/register", data={
        "username": "ab",
        "email": "ab@example.com",
        "password": "password123",
        "confirm_password": "password123"
    }, follow_redirects=True)
    assert b"Username must be between 3 and 30 characters" in resp.data

    # Password mismatch
    resp2 = client.post("/register", data={
        "username": "bobsmith",
        "email": "bob@example.com",
        "password": "password123",
        "confirm_password": "password999"
    }, follow_redirects=True)
    assert b"Passwords do not match" in resp2.data

def test_login_success_and_logout(client, user1, auth):
    response = auth.login("user_one", "password123")
    assert response.status_code == 200
    assert b"Welcome back" in response.data

    # Logout
    logout_resp = auth.logout()
    assert logout_resp.status_code == 200
    assert b"signed out successfully" in logout_resp.data

def test_login_invalid_credentials(client, user1, auth):
    response = auth.login("user_one", "incorrect_password")
    assert response.status_code == 200
    assert b"Invalid username/email or password" in response.data

def test_unauthorized_access(client):
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]
