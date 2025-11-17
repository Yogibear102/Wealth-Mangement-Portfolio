"""
Populate/refresh `MasterAsset` table from market-data providers.

Usage:
  FINNHUB_API_KEY=... python scripts/update_master_assets.py

Behavior/limits:
- If `FINNHUB_API_KEY` is set, fetch US exchange symbols and insert up to N symbols (default 1000).
- If no key provided, script will insert a small default set (EURUSD, USDINR, GOLD, AAPL).
- The script performs upserts and sets `last_refreshed`.

This script uses a conservative default batch size to avoid hitting API rate limits.
"""
from datetime import datetime
import os
import json
import sys
import time
import requests

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from models import db, MasterAsset

# Config
FINNHUB_KEY = os.environ.get('FINNHUB_API_KEY')
BATCH_LIMIT = int(os.environ.get('MASTER_ASSET_LIMIT', '1000'))


def upsert_master_asset(session, symbol, name, asset_type='Stock', currency='USD', meta=None):
    ma = session.query(MasterAsset).filter_by(symbol=symbol).first()
    now = datetime.utcnow()
    meta_json = json.dumps(meta or {})
    if ma:
        ma.name = name
        ma.asset_type = asset_type
        ma.currency = currency
        ma.meta = meta_json
        ma.last_refreshed = now
    else:
        ma = MasterAsset(symbol=symbol, name=name, asset_type=asset_type, currency=currency, meta=meta_json, last_refreshed=now)
        session.add(ma)
    return ma


def fetch_from_finnhub(limit=BATCH_LIMIT):
    url = 'https://finnhub.io/api/v1/stock/symbol'
    params = {'exchange': 'US', 'token': FINNHUB_KEY}
    print('Fetching symbols from Finnhub...')
    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    # data is a list of dicts; we'll limit to avoid huge loads
    result = []
    for i, item in enumerate(data):
        if i >= limit:
            break
        sym = item.get('symbol')
        name = item.get('description') or item.get('displaySymbol') or sym
        result.append((sym, name))
    return result


def insert_defaults(session):
    print('Inserting comprehensive master assets...')
    defaults = [
        # Major Stocks (US Tech Giants)
        ('AAPL', 'Apple Inc.', 'Stock', 'USD'),
        ('GOOGL', 'Alphabet Inc. (Google)', 'Stock', 'USD'),
        ('MSFT', 'Microsoft Corporation', 'Stock', 'USD'),
        ('AMZN', 'Amazon.com Inc.', 'Stock', 'USD'),
        ('TSLA', 'Tesla Inc.', 'Stock', 'USD'),
        ('META', 'Meta Platforms Inc. (Facebook)', 'Stock', 'USD'),
        ('NVDA', 'NVIDIA Corporation', 'Stock', 'USD'),
        ('JPM', 'JPMorgan Chase & Co.', 'Stock', 'USD'),
        ('V', 'Visa Inc.', 'Stock', 'USD'),
        ('WMT', 'Walmart Inc.', 'Stock', 'USD'),
        
        # Indian Stocks
        ('RELIANCE.NS', 'Reliance Industries Ltd', 'Stock', 'INR'),
        ('TCS.NS', 'Tata Consultancy Services', 'Stock', 'INR'),
        ('INFY.NS', 'Infosys Limited', 'Stock', 'INR'),
        ('HDFCBANK.NS', 'HDFC Bank Limited', 'Stock', 'INR'),
        ('ICICIBANK.NS', 'ICICI Bank Limited', 'Stock', 'INR'),
        
        # Forex Pairs
        ('EURUSD', 'EUR/USD', 'Forex', 'EUR'),
        ('GBPUSD', 'GBP/USD', 'Forex', 'GBP'),
        ('USDJPY', 'USD/JPY', 'Forex', 'USD'),
        ('AUDUSD', 'AUD/USD', 'Forex', 'AUD'),
        ('USDCAD', 'USD/CAD', 'Forex', 'USD'),
        ('USDINR', 'USD/INR', 'Forex', 'USD'),
        ('USDCHF', 'USD/CHF', 'Forex', 'USD'),
        
        # Precious Metals / Commodities
        ('XAUUSD', 'Gold (XAU/USD)', 'Commodity', 'USD'),
        ('GOLD', 'Gold Spot', 'Commodity', 'USD'),
        ('SLV', 'iShares Silver Trust (Silver ETF)', 'Commodity', 'USD'),
        ('GLD', 'SPDR Gold Trust (Gold ETF)', 'Commodity', 'USD'),
        ('SILVER', 'Silver Spot', 'Commodity', 'USD'),
        
        # Real Estate Indices / REITs
        ('VNQ', 'Vanguard Real Estate ETF', 'Real Estate', 'USD'),
        ('IYR', 'iShares US Real Estate ETF', 'Real Estate', 'USD'),
        ('REET', 'iShares Global REIT ETF', 'Real Estate', 'USD'),
        ('REALTY.NS', 'Realty Income REIT', 'Real Estate', 'INR'),
    ]
    for sym, name, typ, cur in defaults:
        upsert_master_asset(session, sym, name, asset_type=typ, currency=cur, meta={'source': 'defaults'})


def main():
    with app.app_context():
        session = db.session
        try:
            if FINNHUB_KEY:
                items = fetch_from_finnhub()
                print(f'Fetched {len(items)} symbols (upserting up to {BATCH_LIMIT}).')
                for sym, name in items:
                    upsert_master_asset(session, sym, name, asset_type='Stock', currency='USD', meta={'source': 'finnhub'})
                # add a few common forex/commodity entries
                upsert_master_asset(session, 'EURUSD', 'EUR/USD', asset_type='Forex', currency='EUR', meta={'source': 'manual'})
                upsert_master_asset(session, 'USDINR', 'USD/INR', asset_type='Forex', currency='USD', meta={'source': 'manual'})
                upsert_master_asset(session, 'XAUUSD', 'Gold (XAU/USD)', asset_type='Commodity', currency='USD', meta={'source': 'manual'})
            else:
                insert_defaults(session)

            session.commit()
            print('Master assets update complete.')
        except Exception as e:
            session.rollback()
            print('Failed to update master assets:', e)


if __name__ == '__main__':
    main()
