from app import app
from models import db, User, Asset, Transaction, MasterAsset
import bcrypt
from datetime import datetime
import os

# --- Database setup script ---
with app.app_context():
    # Ensure instance directory exists
    if not os.path.exists('instance'):
        os.makedirs('instance', exist_ok=True)

    print("🔄 Rebuilding database...")
    db.drop_all()  # Clears old schema (optional, use only for reset)
    db.create_all()

    # Check if demo user already exists
    user = User.query.filter_by(email='demo@example.com').first()
    if not user:
        print("👤 Creating demo user...")
        user = User(
            email='demo@example.com',
            password_hash=bcrypt.hashpw('Password123'.encode('utf-8'), bcrypt.gensalt()),
            base_currency='USD',
            first_name='Demo',
            last_name='User'
        )
        db.session.add(user)
        db.session.commit()

        print("💰 Creating sample assets...")
        a1 = Asset(
            user_id=user.id,
            asset_type='Realestate',
            name='House in Mumbai',
            quantity=1,
            current_value=12000000,
            purchase_date='2015-01-01',
            currency='INR',
            color='#1f77b4')
        a2 = Asset(
            user_id=user.id,
            asset_type='Gold',
            name='Gold Ornaments',
            quantity=2,
            current_value=400000,
            purchase_date='2020-05-10',
            currency='INR',
            color='#ff7f0e')
        a3 = Asset(
            user_id=user.id,
            asset_type='Stocks',
            name='TechCorp Shares',
            quantity=50,
            current_value=250000,
            purchase_date='2021-08-15',
            currency='INR',
            color='#2ca02c')

        db.session.add_all([a1, a2, a3])
        db.session.commit()

        print("🧾 Adding sample transactions...")
        t1 = Transaction(
            user_id=user.id,
            asset_id=a1.id,
            tx_type='Buy',
            amount=12000000,
            date=datetime(
                2015,
                1,
                1),
            note='Purchased property in Mumbai')
        t2 = Transaction(
            user_id=user.id,
            asset_id=a2.id,
            tx_type='Buy',
            amount=400000,
            date=datetime(
                2020,
                5,
                10),
            note='Bought gold ornaments')
        t3 = Transaction(
            user_id=user.id,
            asset_id=a3.id,
            tx_type='Buy',
            amount=250000,
            date=datetime(
                2021,
                8,
                15),
            note='Invested in TechCorp stocks')

        db.session.add_all([t1, t2, t3])
        db.session.commit()

        print("✅ Demo data inserted successfully!")
        print("Login with:")
        print("   Email: demo@example.com")
        print("   Password: Password123")

    else:
        print("⚠️ Demo user already exists, skipping creation.")
