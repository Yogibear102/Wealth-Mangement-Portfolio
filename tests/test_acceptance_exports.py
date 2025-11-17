# tests/test_acceptance_exports.py
import io
import csv
from models import Asset, User, db


def login_test_user(client):
    """Helper: Simulate a logged-in session."""
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


def test_export_csv_data_integrity(client, test_app):
    # First, ensure a test user is logged in
    login_test_user(client)

    # Create asset for the logged-in user
    with test_app.app_context():
        user = User.query.filter_by(email="test@example.com").first()
        assert user is not None, "login_test_user should create a test user"

        asset = Asset(
            user_id=user.id,
            asset_type="Bond",
            name="Govt Bond",
            quantity=5,
            current_value=5000,
            currency="USD"
        )
        db.session.add(asset)
        db.session.commit()

    # Call the protected CSV export route
    response = client.get('/export/csv')
    assert response.status_code == 200

    data = response.data.decode('utf-8')
    reader = csv.reader(io.StringIO(data))
    rows = list(reader)

    # Ensure our created asset appears in the CSV output
    assert any("Govt Bond" in ",".join(row) for row in rows), "Export CSV missing created asset"


def test_export_pdf_generation(client, test_app):
    login_test_user(client)
    response = client.get('/export/pdf')
    assert response.status_code == 200
    assert response.mimetype == 'application/pdf'
    assert len(response.data) > 500  # ensure PDF has content
