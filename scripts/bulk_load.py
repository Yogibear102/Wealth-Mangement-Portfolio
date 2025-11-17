"""Bulk-load script to generate many transactions for performance testing.
Usage: python scripts/bulk_load.py --user demo@example.com --count 10000
"""
import argparse
import random
import datetime
from models import db, User, Asset, Transaction
from app import app


def find_user(email):
    return User.query.filter_by(email=email).first()


def create_transactions(user_email, count=10000):
    user = find_user(user_email)
    if not user:
        print('User not found:', user_email)
        return
    assets = Asset.query.filter_by(user_id=user.id).all()
    if not assets:
        print('No assets for user; create some first.')
        return
    for i in range(count):
        a = random.choice(assets)
        tx_type = random.choice(['buy', 'sell', 'income', 'expense'])
        amount = round(random.uniform(1, 500), 2)
        date = (
            datetime.datetime.utcnow() -
            datetime.timedelta(
                days=random.randint(
                    0,
                    3650))).date().isoformat()
        tx = Transaction(
            asset_id=a.id,
            tx_type=tx_type,
            amount=amount,
            date=date,
            note=f'bulk {i}')
        db.session.add(tx)
        # update asset value simple logic
        if tx_type in ['buy', 'expense']:
            a.current_value += amount
        else:
            a.current_value -= amount
            if a.current_value < 0:
                a.current_value = 0
        if i % 500 == 0:
            db.session.commit()
    db.session.commit()
    print(f'Created {count} transactions for user {user_email}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--user', required=True)
    parser.add_argument('--count', type=int, default=10000)
    args = parser.parse_args()
    with app.app_context():
        create_transactions(args.user, args.count)
