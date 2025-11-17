from models import db, User, Asset, Transaction
from datetime import datetime


def test_asset_creation_and_value_update(client):
    """System test: Validate full asset lifecycle — creation, transaction, and updated value."""

    # ✅ Step 1: Create a user
    user = User(
        email="qa@test.com",
        password_hash=b"testhash",
        base_currency="USD"
    )
    db.session.add(user)
    db.session.commit()
    assert user.id is not None, "User should be committed successfully"

    # ✅ Step 2: Create an asset for that user
    asset = Asset(
        user_id=user.id,
        asset_type="Stock",
        name="QA Corp",
        quantity=10,
        current_value=1000,
        currency="USD"
    )
    db.session.add(asset)
    db.session.commit()

    # Verify basic creation
    assert Asset.query.count() == 1
    assert asset.current_value == 1000
    assert asset.user_id == user.id

    # ✅ Step 3: Add a transaction for this asset (simulate buy)
    tx = Transaction(
        asset_id=asset.id,
        user_id=user.id,
        tx_type="Buy",
        amount=501,
        date=datetime.utcnow(),
        note="Test buy"
    )
    db.session.add(tx)

    # Simulate value update after transaction
    asset.current_value += tx.amount
    db.session.commit()

    # ✅ Step 4: Validate asset value after update
    updated_asset = Asset.query.get(asset.id)
    assert updated_asset.current_value == 1501, "Asset value should update correctly after transaction"

    # ✅ Step 5: Verify transaction linkage
    saved_tx = Transaction.query.filter_by(asset_id=asset.id).first()
    assert saved_tx is not None, "Transaction should be stored correctly"
    assert saved_tx.amount == 501
    assert saved_tx.note == "Test buy"
    assert saved_tx.tx_type.lower() == "buy"

    # ✅ Step 6: Simulate a sell transaction (reduce value)
    sell_tx = Transaction(
        asset_id=asset.id,
        user_id=user.id,
        tx_type="Sell",
        amount=500,
        date=datetime.utcnow(),
        note="Test sell"
    )
    db.session.add(sell_tx)
    asset.current_value -= sell_tx.amount
    db.session.commit()

    # ✅ Step 7: Verify value after sell
    reloaded_asset = Asset.query.get(asset.id)
    assert reloaded_asset.current_value == 1001, "Asset value should decrease correctly after sell"

    # ✅ Step 8: Final DB consistency checks
    total_txs = Transaction.query.filter_by(asset_id=asset.id).count()
    assert total_txs == 2, "There should be 2 transactions recorded (buy + sell)"
    assert reloaded_asset.user_id == user.id, "Asset should remain linked to same user"

    # ✅ Step 9: Optional sanity log for debugging
    print(f"✅ Asset '{reloaded_asset.name}' lifecycle verified with total value {reloaded_asset.current_value} USD.")
