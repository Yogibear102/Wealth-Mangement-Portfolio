"""
Price fetching utilities for stocks, forex, and commodities.
Primary: Twelve Data API (free tier: 800 requests/day)
Fallback: yfinance (free, unlimited but currently unstable)

Get your free API key at: https://twelvedata.com/apikey
"""
import yfinance as yf
import requests
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Cache to avoid hitting APIs too frequently
_price_cache = {}
_cache_ttl = timedelta(minutes=5)

# Twelve Data API key - get free key from https://twelvedata.com/apikey
TWELVE_DATA_KEY = os.getenv('TWELVE_DATA_API_KEY', '')


def get_latest_price(symbol, asset_type='Stock'):
    """
    Fetch the latest price for a given symbol.
    Tries Twelve Data first, falls back to yfinance if API key not set.
    
    Args:
        symbol: The ticker symbol (e.g., 'AAPL', 'EUR/USD', 'GOLD')
        asset_type: 'Stock', 'Forex', 'Commodity', or 'Real Estate'
    
    Returns:
        float: The latest price, or None if unavailable
    """
    now = datetime.now()
    
    # Check cache
    cache_key = f"{symbol}:{asset_type}"
    if cache_key in _price_cache:
        cached_price, cached_time = _price_cache[cache_key]
        if now - cached_time < _cache_ttl:
            return cached_price
    
    price = None
    
    # Try Twelve Data first if API key is available
    if TWELVE_DATA_KEY:
        price = _fetch_twelve_data(symbol, asset_type)
    
    # Fallback to yfinance if Twelve Data fails or no API key
    if price is None:
        price = _fetch_yfinance(symbol, asset_type)
    
    # Cache result if successful
    if price and price > 0:
        _price_cache[cache_key] = (price, now)
    
    return price


def _fetch_twelve_data(symbol, asset_type):
    """Fetch price using Twelve Data API (800 requests/day free tier)."""
    if not TWELVE_DATA_KEY:
        return None
    
    try:
        base_url = "https://api.twelvedata.com/price"
        
        # Map symbol format for Twelve Data
        td_symbol = _map_to_twelve_data_symbol(symbol, asset_type)
        
        params = {
            'symbol': td_symbol,
            'apikey': TWELVE_DATA_KEY
        }
        
        response = requests.get(base_url, params=params, timeout=10)
        data = response.json()
        
        if 'price' in data:
            return float(data['price'])
        
        # Check for error messages
        if 'message' in data:
            print(f"Twelve Data error for {symbol}: {data['message']}")
        
        return None
    except Exception as e:
        print(f"Twelve Data error for {symbol}: {e}")
        return None


def _fetch_yfinance(symbol, asset_type):
    """Fetch price using yfinance (free, unlimited but may be unstable)."""
    try:
        yf_symbol = _map_to_yfinance_symbol(symbol, asset_type)
        ticker = yf.Ticker(yf_symbol)
        info = ticker.history(period='5d')
        
        if info.empty:
            return None
        
        price = float(info['Close'].iloc[-1])
        return price
    except Exception as e:
        print(f"yfinance error for {symbol}: {e}")
        return None


def _map_to_twelve_data_symbol(symbol, asset_type):
    """
    Map our symbols to Twelve Data format.
    
    Examples:
        AAPL -> AAPL (stocks are direct)
        EURUSD -> EUR/USD (forex uses slash)
        XAUUSD -> XAU/USD (gold as forex pair)
        GOLD -> XAU/USD
    """
    symbol_upper = symbol.upper()
    
    if asset_type == 'Stock' or asset_type == 'Real Estate':
        return symbol
    
    if asset_type == 'Forex':
        # Convert EURUSD to EUR/USD
        if '/' not in symbol_upper and len(symbol_upper) >= 6:
            return f"{symbol_upper[:3]}/{symbol_upper[3:6]}"
        return symbol
    
    if asset_type == 'Commodity':
        # Map commodities to forex pairs (Twelve Data supports these)
        commodity_map = {
            'XAUUSD': 'XAU/USD',  # Gold
            'GOLD': 'XAU/USD',
            'XAGUSD': 'XAG/USD',  # Silver
            'SILVER': 'XAG/USD',
        }
        mapped = commodity_map.get(symbol_upper)
        if mapped:
            return mapped
    
    return symbol


def _old_alpha_vantage_code(symbol, asset_type):
    """Old Alpha Vantage code - kept for reference but not used."""
    # Old Alpha Vantage implementation removed
    return None


def _map_to_yfinance_symbol(symbol, asset_type):
    """
    Map our symbols to yfinance format.
    
    Examples:
        AAPL -> AAPL (stocks are direct)
        EURUSD -> EURUSD=X (forex needs =X suffix)
        XAUUSD -> GC=F (gold futures)
        RELIANCE.NS -> RELIANCE.NS (Indian stocks already have .NS)
    """
    symbol_upper = symbol.upper()
    
    # Stocks: most are direct, Indian stocks already have .NS/.BO
    if asset_type == 'Stock':
        return symbol
    
    # Forex: add =X suffix if not already present
    if asset_type == 'Forex':
        if '=' not in symbol_upper:
            return f"{symbol_upper}=X"
        return symbol
    
    # Commodities
    if asset_type == 'Commodity':
        commodity_map = {
            'XAUUSD': 'GC=F',  # Gold futures
            'GOLD': 'GC=F',     # Gold spot -> futures
            'XAGUSD': 'SI=F',  # Silver futures
            'SILVER': 'SI=F',  # Silver spot -> futures
            'CRUDE': 'CL=F',   # Crude oil futures
            'BRENT': 'BZ=F',   # Brent oil futures
        }
        mapped = commodity_map.get(symbol_upper)
        if mapped:
            return mapped
        return symbol
    
    # Real Estate ETFs are like stocks
    if asset_type == 'Real Estate':
        return symbol
    
    return symbol


def clear_cache():
    """Clear the price cache."""
    global _price_cache
    _price_cache = {}
