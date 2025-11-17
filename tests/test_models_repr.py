# tests/test_models_repr.py
from models import User, Asset, Transaction
from datetime import datetime


def test_model_str_methods():
    u = User(
        email="x@test.com",
        password_hash=b"x",
        first_name="X",
        last_name="Y",
        base_currency="USD")
    a = Asset(
        user_id=1,
        asset_type="Gold",
        name="Test",
        quantity=1,
        current_value=100,
        currency="USD")
    t = Transaction(
        user_id=1,
        asset_id=1,
        tx_type="Buy",
        amount=100,
        date=datetime.utcnow(),
        note="Sample")
    assert str(u)
    assert str(a)
    assert str(t)
