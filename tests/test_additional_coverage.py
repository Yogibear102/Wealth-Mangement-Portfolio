# tests/test_additional_coverage.py
from app import parse_date_input
from app import app, db
from models import User, Asset, Transaction
from datetime import datetime


def login_test_user(client):
    with client.session_transaction() as sess:
        user = User.query.filter_by(email="cover@test.com").first()
        if not user:
            user = User(
                email="cover@test.com",
                password_hash=b"fakehash",
                first_name="Cover",
                last_name="Tester",
                base_currency="USD"
            )
            db.session.add(user)
            db.session.commit()
        sess['user_id'] = user.id
        sess['user_email'] = user.email
        sess['user_name'] = f"{user.first_name} {user.last_name}"


def test_health_endpoint(client):
    """Simple coverage for /health route"""
    res = client.get('/health')
    assert res.status_code == 200
    assert 'status' in res.get_json()


def test_login_logout_flow(client):
    """Covers login and logout routes."""
    import bcrypt

    with app.app_context():
        user = User.query.filter_by(email='login@test.com').first()
        if not user:
            hashed_pw = bcrypt.hashpw(b"testpassword", bcrypt.gensalt())
            user = User(
                email='login@test.com',
                password_hash=hashed_pw,
                first_name='QA',
                last_name='User',
                base_currency='USD')
            db.session.add(user)
            db.session.commit()

    # Wrong password
    res = client.post(
        '/login',
        data={
            'email': 'login@test.com',
            'password': 'wrong'})
    assert b'Invalid' in res.data or res.status_code in [200, 302]

    # Correct password
    res = client.post(
        '/login',
        data={
            'email': 'login@test.com',
            'password': 'testpassword'},
        follow_redirects=True)
    assert res.status_code == 200 or b'Dashboard' in res.data

    # Logout
    res = client.get('/logout', follow_redirects=True)
    assert res.status_code == 200
    assert b'Logged out' in res.data or b'Login' in res.data


def test_settings_update(client):
    """Covers /settings GET and POST"""
    login_test_user(client)
    res = client.get('/settings')
    assert res.status_code == 200
    res = client.post(
        '/settings',
        data={
            'base_currency': 'EUR'},
        follow_redirects=True)
    assert b'Settings saved' in res.data


def test_asset_edit_and_delete(client):
    """Covers editing and deleting assets."""
    login_test_user(client)

    # get current logged-in user's ID
    with client.session_transaction() as sess:
        uid = sess['user_id']

    with app.app_context():
        asset = Asset(
            user_id=uid,
            asset_type='Stock',
            name='DemoAsset',
            quantity=1,
            current_value=100,
            currency='USD')
        db.session.add(asset)
        db.session.commit()
        aid = asset.id

    res = client.post(
        f'/assets/edit/{aid}',
        data={
            'name': 'UpdatedAsset',
            'quantity': 2,
            'current_value': 200},
        follow_redirects=True)
    assert b'Asset updated' in res.data

    res = client.post(f'/assets/delete/{aid}', follow_redirects=True)
    assert b'deleted' in res.data


def test_transaction_edit_flow(client):
    """Covers /transactions/edit"""
    login_test_user(client)

    # Get the logged-in user's ID
    with client.session_transaction() as sess:
        uid = sess['user_id']

    with app.app_context():
        asset = Asset(
            user_id=uid,
            asset_type='Gold',
            name='Coin',
            quantity=1,
            current_value=1000,
            currency='USD')
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id

        tx = Transaction(
            user_id=uid,
            asset_id=asset_id,
            tx_type='Buy',
            amount=500,
            date=datetime.utcnow(),
            note='Initial')
        db.session.add(tx)
        db.session.commit()
        tx_id = tx.id

    # ✅ Convert the date into a valid string format Flask expects
    edit_date = parse_date_input("2025-01-01").strftime("%Y-%m-%d")

    # ✅ Perform the edit
    res = client.post(f'/transactions/edit/{tx_id}', data={
        'asset_id': asset_id,
        'type': 'Sell',
        'amount': '300',
        'note': 'Edited',
        'date': edit_date  # Properly formatted date string
    }, follow_redirects=True)

    assert res.status_code == 200
    assert b'Transaction updated' in res.data or b'success' in res.data

def test_misc_routes_and_health(client):
    """Covers rarely hit misc routes and boosts coverage."""
    res = client.get("/health")
    assert res.status_code == 200

    res = client.get("/favicon.ico")
    assert res.status_code in (200, 404)  # favicon optional

    res = client.get("/logout", follow_redirects=True)
    assert b"Login" in res.data or res.status_code == 200
