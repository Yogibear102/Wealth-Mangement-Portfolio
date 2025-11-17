# tests/test_usability_charts.py
from models import db, Asset, User
from app import app


def login_test_user(client):
    """Simulate a logged-in session."""
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


def test_chart_data_accuracy(client):
    """Ensure chart data reflects accurate net worth total."""
    with app.app_context():
        # Clear and add assets
        db.session.query(Asset).delete()
        db.session.commit()

        asset1 = Asset(
            user_id=1,
            asset_type="Gold",
            name="Bar",
            quantity=2,
            current_value=2000,
            currency="USD")
        asset2 = Asset(
            user_id=1,
            asset_type="RealEstate",
            name="Home",
            quantity=1,
            current_value=8000,
            currency="USD")
        db.session.add_all([asset1, asset2])
        db.session.commit()

        total_calculated = asset1.current_value + asset2.current_value

    # ✅ simulate login before calling protected route
    login_test_user(client)

    response = client.get('/api/networth')
    assert response.status_code == 200, "API should be accessible to logged-in users"

    data = response.get_json()
    assert abs(data['networth'] -
               total_calculated) < 0.01, "Chart net worth must match total asset value"
    assert 'currency' in data, "Currency info should be included in API response"
