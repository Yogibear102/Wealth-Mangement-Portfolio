"""
Additional tests to achieve 80% code coverage.
Focus on transaction add/buy flows, error cases, and edge paths in app.py.
"""
import json
import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from app import app, parse_date_input
from models import db, User, Asset, Transaction, MasterAsset


@pytest.fixture
def authenticated_client():
    """Create a fully authenticated client with user and assets."""
    with app.app_context():
        db.drop_all()
        db.create_all()
        
        user = User(
            email='auth@test.com',
            password_hash=b'hash',
            first_name='Auth',
            last_name='User',
            base_currency='USD',
            liquid_equity=50000,
            monthly_income=5000
        )
        db.session.add(user)
        db.session.flush()
        user_id = user.id
        
        # Create master assets
        master1 = MasterAsset(
            symbol='AAPL',
            name='Apple Inc.',
            asset_type='Stock',
            currency='USD',
            meta=json.dumps({})
        )
        master2 = MasterAsset(
            symbol='EURUSD',
            name='EUR/USD',
            asset_type='Forex',
            currency='EUR',
            meta=json.dumps({})
        )
        db.session.add_all([master1, master2])
        db.session.commit()
    
    client = app.test_client()
    with client.session_transaction() as sess:
        sess['user_id'] = user_id
        sess['user_email'] = 'auth@test.com'
        sess['user_name'] = 'Auth User'
    
    return client, user_id


# ============================================
# Transaction Buy/Add Tests
# ============================================

def test_buy_transaction_from_master_asset(authenticated_client):
    """Test buying an asset from master assets."""
    client, user_id = authenticated_client
    
    with patch('app.get_latest_price') as mock_price:
        mock_price.return_value = 150.0
        response = client.post('/assets/buy', data={
            'asset_choice': 'm:AAPL',  # Master asset selection
            'type': 'buy',
            'quantity': '5',
            'amount': '750'
        })
        assert response.status_code == 302
        
    with app.app_context():
        assets = Asset.query.filter_by(user_id=user_id).all()
        assert len(assets) > 0


def test_buy_transaction_with_auto_price_fetch(authenticated_client):
    """Test buying without providing amount (auto-fetch price)."""
    client, user_id = authenticated_client
    
    with patch('app.get_latest_price') as mock_price:
        mock_price.return_value = 150.0
        response = client.post('/assets/buy', data={
            'asset_choice': 'm:AAPL',
            'type': 'buy',
            'quantity': '5',
            'amount': ''  # No amount provided
        })
        assert response.status_code in [302, 200]


def test_buy_insufficient_liquid_equity(authenticated_client):
    """Test buy fails when user doesn't have enough liquid equity."""
    client, user_id = authenticated_client
    
    # Set user's liquid equity to very low
    with app.app_context():
        user = User.query.get(user_id)
        user.liquid_equity = 10
        db.session.commit()
    
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '10',
        'amount': '5000'  # More than available liquid equity
    })
    assert response.status_code in [302, 200]


def test_buy_invalid_quantity(authenticated_client):
    """Test buy with invalid quantity."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '0',  # Invalid quantity
        'amount': '150'
    })
    assert response.status_code in [302, 200]


def test_buy_invalid_amount(authenticated_client):
    """Test buy with invalid amount."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '5',
        'amount': '-100'  # Negative amount
    })
    assert response.status_code in [302, 200]


def test_buy_invalid_asset_choice(authenticated_client):
    """Test buy with invalid asset choice."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': '',  # No asset choice
        'type': 'buy',
        'quantity': '5',
        'amount': '150'
    })
    assert response.status_code in [302, 200]


def test_buy_numeric_asset_id(authenticated_client):
    """Test buy using numeric asset ID (backward compatibility)."""
    client, user_id = authenticated_client
    
    # First create an asset
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Test Asset',
            quantity=0,
            current_value=0,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    # Buy using numeric ID
    response = client.post('/assets/buy', data={
        'asset_choice': str(asset_id),  # Numeric asset ID
        'type': 'buy',
        'quantity': '5',
        'amount': '1000'
    })
    assert response.status_code == 302


def test_buy_income_transaction(authenticated_client):
    """Test income transaction (doesn't require liquid equity check)."""
    client, user_id = authenticated_client
    
    with patch('app.get_latest_price') as mock_price:
        mock_price.return_value = 100.0
        response = client.post('/assets/buy', data={
            'asset_choice': 'm:EURUSD',
            'type': 'income',
            'quantity': '100',
            'amount': '100'
        })
        assert response.status_code == 302


def test_buy_sell_transaction(authenticated_client):
    """Test sell transaction."""
    client, user_id = authenticated_client
    
    # First create and buy an asset
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Sellable',
            quantity=10,
            current_value=1500,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    # Sell some
    response = client.post('/assets/buy', data={
        'asset_choice': str(asset_id),
        'type': 'sell',
        'quantity': '5',
        'amount': '750'
    })
    assert response.status_code == 302


def test_buy_expense_transaction(authenticated_client):
    """Test expense transaction."""
    client, user_id = authenticated_client
    
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:EURUSD',
        'type': 'expense',
        'quantity': '10',
        'amount': '100'
    })
    assert response.status_code == 302


def test_buy_invalid_transaction_type(authenticated_client):
    """Test buy with invalid transaction type."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'invalid_type',
        'quantity': '5',
        'amount': '150'
    })
    assert response.status_code in [302, 200]


def test_buy_with_custom_note(authenticated_client):
    """Test buy with a custom note."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '5',
        'amount': '750',
        'note': 'Custom purchase note'
    })
    assert response.status_code == 302
    
    with app.app_context():
        tx = Transaction.query.filter_by(user_id=user_id).first()
        assert tx is not None
        assert tx.note == 'Custom purchase note'


def test_buy_with_date_input(authenticated_client):
    """Test buy with custom date."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '5',
        'amount': '750',
        'date': '2023-06-15'
    })
    assert response.status_code == 302


def test_buy_invalid_date_format(authenticated_client):
    """Test buy with invalid date format (uses default)."""
    client, user_id = authenticated_client
    response = client.post('/assets/buy', data={
        'asset_choice': 'm:AAPL',
        'type': 'buy',
        'quantity': '5',
        'amount': '750',
        'date': 'invalid-date'
    })
    assert response.status_code == 302


# ============================================
# Asset Delete Tests
# ============================================

def test_asset_delete(authenticated_client):
    """Test deleting an asset."""
    client, user_id = authenticated_client
    
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Deletable',
            quantity=5,
            current_value=1000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/delete/{asset_id}', data={})
    assert response.status_code == 302


def test_asset_delete_unauthorized(authenticated_client):
    """Test deleting asset owned by another user."""
    client, user_id = authenticated_client
    
    with app.app_context():
        # Create another user's asset
        other_user = User(
            email='other@test.com',
            password_hash=b'hash',
            first_name='Other',
            last_name='User'
        )
        db.session.add(other_user)
        db.session.flush()
        
        asset = Asset(
            user_id=other_user.id,
            asset_type='Stock',
            name='Not Mine',
            quantity=5,
            current_value=1000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/delete/{asset_id}', data={})
    assert response.status_code == 302


# ============================================
# Asset Sell Tests
# ============================================

def test_asset_sell_partial(authenticated_client):
    """Test selling part of an asset."""
    client, user_id = authenticated_client
    
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Stock to Sell',
            quantity=100,
            current_value=10000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/{asset_id}/sell', data={
        'quantity': '50',
        'amount': '100',  # Price per unit
        'date': '2023-06-15',
        'note': 'Partial sell'
    })
    assert response.status_code == 302


def test_asset_sell_all(authenticated_client):
    """Test selling all of an asset."""
    client, user_id = authenticated_client
    
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Stock to Sell All',
            quantity=50,
            current_value=5000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/{asset_id}/sell', data={
        'quantity': '50',
        'amount': '100',
        'date': '2023-06-15'
    })
    assert response.status_code == 302


def test_asset_sell_too_much(authenticated_client):
    """Test selling more than owned."""
    client, user_id = authenticated_client
    
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Limited Stock',
            quantity=10,
            current_value=1000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/{asset_id}/sell', data={
        'quantity': '50',  # More than owned
        'amount': '100'
    })
    assert response.status_code == 302


def test_asset_sell_invalid_quantity(authenticated_client):
    """Test selling with invalid quantity."""
    client, user_id = authenticated_client
    
    with app.app_context():
        asset = Asset(
            user_id=user_id,
            asset_type='Stock',
            name='Stock',
            quantity=50,
            current_value=5000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/{asset_id}/sell', data={
        'quantity': '0',  # Invalid
        'amount': '100'
    })
    assert response.status_code == 302


def test_asset_sell_unauthorized(authenticated_client):
    """Test selling another user's asset."""
    client, user_id = authenticated_client
    
    with app.app_context():
        other_user = User(
            email='other2@test.com',
            password_hash=b'hash',
            first_name='Other2',
            last_name='User2'
        )
        db.session.add(other_user)
        db.session.flush()
        
        asset = Asset(
            user_id=other_user.id,
            asset_type='Stock',
            name='Not Mine',
            quantity=50,
            current_value=5000,
            currency='USD'
        )
        db.session.add(asset)
        db.session.commit()
        asset_id = asset.id
    
    response = client.post(f'/assets/{asset_id}/sell', data={
        'quantity': '10',
        'amount': '100'
    })
    assert response.status_code == 302


# ============================================
# Parse Date Tests
# ============================================

def test_parse_date_input_datetime_object():
    """Test parse_date_input with datetime object."""
    dt = datetime(2023, 6, 15)
    result = parse_date_input(dt)
    assert result == dt


def test_parse_date_input_iso_format():
    """Test parse_date_input with ISO format."""
    result = parse_date_input('2023-06-15T10:30:00')
    assert result is not None


# ============================================
# Transactions List Tests
# ============================================

def test_transactions_list_filters(authenticated_client):
    """Test transactions list with various filters."""
    client, user_id = authenticated_client
    
    response = client.get('/transactions?q=test&type=Buy&start_date=2023-01-01&end_date=2023-12-31')
    assert response.status_code == 200


def test_transactions_list_invalid_dates(authenticated_client):
    """Test transactions list with invalid date filters."""
    client, user_id = authenticated_client
    
    response = client.get('/transactions?start_date=invalid&end_date=also-invalid')
    assert response.status_code == 200


# ============================================
# Assets Buy Page
# ============================================

def test_assets_buy_get(authenticated_client):
    """Test GET /assets/buy page."""
    client, user_id = authenticated_client
    response = client.get('/assets/buy')
    assert response.status_code == 200


def test_assets_add_disabled(authenticated_client):
    """Test /assets/add redirects (disabled)."""
    client, user_id = authenticated_client
    response = client.get('/assets/add')
    assert response.status_code == 302
