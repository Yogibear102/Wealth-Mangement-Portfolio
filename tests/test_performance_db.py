# tests/test_performance_db.py
import time
from models import db, Asset, User
from app import app


def login_test_user(client):
    """Helper to simulate a logged-in user session."""
    with client.session_transaction() as sess:
        user = User.query.filter_by(email="test@example.com").first()
        if not user:
            user = User(
                email="test@example.com",
                password_hash=b"fakehash",
                first_name="QA",
                last_name="Tester",
                base_currency="USD"
            )
            db.session.add(user)
            db.session.commit()
        sess['user_id'] = user.id
        sess['user_email'] = user.email
        sess['user_name'] = f"{user.first_name} {user.last_name}"


def test_dashboard_query_performance(client):
    """Simulate 10k assets and ensure dashboard loads within 3 seconds."""
    with app.app_context():
        # ✅ Insert 10,000 fake assets for the test user
        assets = [
            Asset(user_id=1, asset_type="Stock", name=f"Test{i}",
                  quantity=1, current_value=100, currency="USD")
            for i in range(10000)
        ]
        db.session.bulk_save_objects(assets)
        db.session.commit()

    # ✅ simulate login
    login_test_user(client)

    start = time.perf_counter()
    response = client.get('/dashboard')
    end = time.perf_counter()

    assert response.status_code == 200, "Dashboard should load successfully"
    duration = end - start
    assert duration < 3, f"Dashboard took too long ({duration:.2f}s)"
