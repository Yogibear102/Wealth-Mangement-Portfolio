#!/usr/bin/env bash
set -euo pipefail

# Quickstart helper for local development (zsh/bash)
# Usage: ./scripts/quickstart.sh
# Optionally set FINNHUB_API_KEY in environment to fetch live symbols.

# Activate virtualenv if present
if [ -f "venv/bin/activate" ]; then
  echo "Activating virtualenv..."
  # shellcheck disable=SC1091
  source venv/bin/activate
fi

echo "Installing requirements (if needed)..."
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
fi

echo "Running database setup (creates demo user and sample data)..."
python3 setup_db.py

echo "Updating master assets (uses FINNHUB_API_KEY if set, otherwise defaults)..."
python3 scripts/update_master_assets.py

echo "Starting Flask app at http://127.0.0.1:5000"
export FLASK_ENV=development
python3 app.py
    