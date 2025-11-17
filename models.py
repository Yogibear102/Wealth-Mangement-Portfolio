from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    base_currency = db.Column(db.String(10), default='USD')
    liquid_equity = db.Column(db.Float, default=0.0)  # Available cash balance
    monthly_income = db.Column(db.Float, default=0.0)  # Monthly income for refresh
    assets = db.relationship('Asset', backref='user', lazy=True)
    transactions = db.relationship('Transaction', backref='user', lazy=True)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))


class Asset(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    asset_type = db.Column(db.String(50))
    name = db.Column(db.String(100))
    symbol = db.Column(db.String(50))  # Ticker symbol (AAPL, EURUSD, etc.)
    quantity = db.Column(db.Float)
    current_value = db.Column(db.Float, default=0.0)
    purchase_date = db.Column(db.String(20))
    currency = db.Column(db.String(10), default='USD')
    color = db.Column(db.String(20))
    transactions = db.relationship('Transaction', backref='asset', lazy=True)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    asset_id = db.Column(db.Integer, db.ForeignKey('asset.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    tx_type = db.Column(db.String(50))
    quantity = db.Column(db.Float, default=0.0)  # Number of units bought/sold
    amount = db.Column(db.Float, default=0.0)  # Total transaction value
    date = db.Column(db.DateTime, default=datetime.utcnow)
    note = db.Column(db.Text)


class MasterAsset(db.Model):
    """Master list of market/tradable assets (stocks, forex pairs, commodities).

    This table caches symbol metadata fetched from market-data providers.
    """
    id = db.Column(db.Integer, primary_key=True)
    symbol = db.Column(db.String(50), unique=True, nullable=False)
    name = db.Column(db.String(200))
    asset_type = db.Column(db.String(50))
    currency = db.Column(db.String(10))
    meta = db.Column(db.Text)  # JSON blob for provider-specific fields
    last_refreshed = db.Column(db.DateTime)

    def to_dict(self):
        return {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'asset_type': self.asset_type,
            'currency': self.currency,
            'meta': json.loads(self.meta) if self.meta else None,
            'last_refreshed': self.last_refreshed.isoformat() if self.last_refreshed else None
        }
