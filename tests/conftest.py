# tests/conftest.py
from werkzeug.security import generate_password_hash
from models import User
from app import app, db
import os
import sys
import pytest

# ensure project root is on sys.path so imports work
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ✅ Import the full initialized app, not just create_app()


@pytest.fixture(scope='module')
def test_app():
    """Provides the full initialized Flask app with all routes registered."""
    app.config.update({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False
    })
    with app.app_context():
        db.create_all()

        # Seed a user for authenticated endpoints
        if not User.query.filter_by(email='test@example.com').first():
            user = User(
                email='test@example.com',
                password_hash=generate_password_hash('Test123'),
                first_name='QA',
                last_name='Tester',
                base_currency='USD'
            )
            db.session.add(user)
            db.session.commit()

        yield app

        db.session.remove()
        db.drop_all()


@pytest.fixture()
def client(test_app):
    """Provides Flask test client."""
    return test_app.test_client()
