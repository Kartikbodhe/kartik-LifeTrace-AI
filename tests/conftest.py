import pytest
from app import create_app
from extensions import db
from models import User

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def runner(app):
    return app.test_cli_runner()

class AuthActions:
    def __init__(self, client):
        self._client = client

    def login(self, identifier="testuser", password="password123"):
        return self._client.post(
            "/login",
            data={"identifier": identifier, "password": password},
            follow_redirects=True
        )

    def logout(self):
        return self._client.get("/logout", follow_redirects=True)

@pytest.fixture
def auth(client):
    return AuthActions(client)

@pytest.fixture
def user1(app):
    with app.app_context():
        user = User(
            username="user_one",
            email="user1@example.com",
            full_name="User One"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id

@pytest.fixture
def user2(app):
    with app.app_context():
        user = User(
            username="user_two",
            email="user2@example.com",
            full_name="User Two"
        )
        user.set_password("password123")
        db.session.add(user)
        db.session.commit()
        return user.id
