from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, jsonify
from datetime import timedelta, datetime
from dotenv import load_dotenv
import os
import io
import csv
import json
from reportlab.lib.pagesizes import letter
from models import db, User, Asset, Transaction, MasterAsset
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import bcrypt
from price_fetcher import get_latest_price

# Load environment variables from .env file
load_dotenv()


# Local file for exchange rates 
# Story 4: minor noop comment for commit separation
# Story 4: noop change — safe placeholder for transaction story
def _story4_noop():
    """No-op helper to mark Story 4 changes (safe, no side effects)."""
    return True


DATA_RATES = 'data/exchange_rates.json'

ALLOWED_TRANSACTION_TYPES = {'buy', 'sell', 'income', 'expense'}

# export commonly used helpers for unit tests / other modules
__all__ = ['create_app', 'apply_transaction_effect', 'parse_date_input', 'ALLOWED_TRANSACTION_TYPES']


def load_rates():
    if os.path.exists(DATA_RATES):
        with open(DATA_RATES) as f:
            return json.load(f)
    return {'USD': 1.0, 'INR': 83.0, 'EUR': 0.92}


def apply_transaction_effect(asset, tx_type, amount, quantity=0, reverse=False):
    """
    Update the asset's current value and quantity based on transaction type.
    When reverse=True the previous effect is undone (used while editing).
    """
    if asset is None:
        raise ValueError('Asset is required to apply transaction effect.')

    if tx_type is None:
        raise ValueError('Transaction type is required.')

    normalized_type = tx_type.strip().lower()
    if normalized_type not in ALLOWED_TRANSACTION_TYPES:
        raise ValueError('Unsupported transaction type.')

    try:
        amount_val = float(amount)
    except (TypeError, ValueError):
        raise ValueError('Amount must be a number.')

    try:
        quantity_val = float(quantity)
    except (TypeError, ValueError):
        quantity_val = 0.0

    amount_val = abs(amount_val)
    if amount_val <= 0:
        raise ValueError('Amount must be greater than zero.')

    if normalized_type in {'buy', 'income'}:
        delta = amount_val
        qty_delta = abs(quantity_val)
    else:  # sell, expense
        delta = -amount_val
        qty_delta = -abs(quantity_val)

    if reverse:
        delta = -delta
        qty_delta = -qty_delta

    asset.current_value = max(asset.current_value + delta, 0)
    asset.quantity = max((asset.quantity or 0) + qty_delta, 0)
    return asset.current_value


def parse_date_filter(value):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d')
    except ValueError:
        return None


def create_app():
    # Ensure instance folder exists
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    instance_dir = os.path.join(BASE_DIR, 'instance')
    os.makedirs(instance_dir, exist_ok=True)

    app = Flask(__name__, template_folder='templates')
    app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(instance_dir, 'pwm.db')}"
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(
        minutes=15)  # session timeout
    db.init_app(app)
    return app


app = create_app()


@app.before_request
def make_session_permanent():
    session.permanent = True
    session.modified = True


@app.route('/health')
def health():
    return jsonify({'status': 'ok', 'time': datetime.utcnow().isoformat()})


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

# ---------------------------
# Auth routes (consistent hashing using werkzeug)
# ---------------------------


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        first_name = request.form['first_name'].strip().title()
        last_name = request.form['last_name'].strip().title()
        email = request.form['email'].lower().strip()
        password = request.form['password']
        
        # Get liquid equity and monthly income
        try:
            liquid_equity = float(request.form.get('liquid_equity', 10000))
            monthly_income = float(request.form.get('monthly_income', 5000))
        except (ValueError, TypeError):
            liquid_equity = 10000
            monthly_income = 5000

        if User.query.filter_by(email=email).first():
            flash('Email already registered. Please log in.', 'warning')
            return redirect(url_for('login'))

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        new_user = User(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password_hash=hashed_pw,
            base_currency='INR',
            liquid_equity=liquid_equity,
            monthly_income=monthly_income
        )
        db.session.add(new_user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and bcrypt.checkpw(
                password.encode('utf-8'),
                user.password_hash):
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = f"{user.first_name} {user.last_name}"
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

# ---------------------------
# User settings (base currency)
# ---------------------------


@app.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    rates = load_rates()
    if request.method == 'POST':
        user.base_currency = request.form.get('base_currency', 'USD')
        db.session.commit()
        flash('Settings saved', 'success')
        return redirect(url_for('settings'))
    return render_template(
        'settings.html',
        user=user,
        rates=list(
            rates.keys()))

# ---------------------------
# Dashboard
# ---------------------------


@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        flash('Session expired. Please log in again.', 'warning')
        return redirect(url_for('login'))
    
    rates = load_rates()
    # ✅ OPTIMIZATION: Use database-level filtering for quantity > 0 instead of Python
    from sqlalchemy import and_
    active_assets = Asset.query.filter(
        and_(Asset.user_id == user.id, Asset.quantity > 0)
    ).all()
    
    total = 0.0
    alloc = {}
    asset_map = {}  # Map asset name to asset object for efficient lookup

    for a in active_assets:
        rate_from = rates.get(a.currency, 1.0)
        rate_to = rates.get(user.base_currency, 1.0)
        converted = a.current_value / rate_from * \
            rate_to if rate_from else a.current_value
        total += converted
        
        # Use asset name for precious metals, otherwise use type
        asset_key = a.name  # Use individual asset name for grouping
        alloc[asset_key] = alloc.get(asset_key, 0.0) + converted
        asset_map[asset_key] = a  # Store reference for color assignment

    labels = list(alloc.keys())
    values = list(alloc.values())
    
    # Assign colors based on asset name and type
    colors = []
    for label in labels:
        label_lower = label.lower()
        if 'gold' in label_lower or 'gld' in label_lower or 'xau' in label_lower:
            colors.append('#FFD700')  # Gold color
        elif 'silver' in label_lower or 'slv' in label_lower or 'xag' in label_lower:
            colors.append('#C0C0C0')  # Silver color
        else:
            # Use the pre-built map instead of searching through active_assets
            asset = asset_map.get(label)
            if asset:
                if asset.asset_type.lower() == 'stock':
                    colors.append('#4E73DF')  # Blue for stocks
                elif asset.asset_type.lower() == 'real estate':
                    colors.append('#1CC88A')  # Green for real estate
                elif asset.asset_type.lower() == 'forex':
                    colors.append('#36B9CC')  # Cyan for forex
                elif asset.asset_type.lower() == 'commodity':
                    colors.append('#F6C23E')  # Yellow for other commodities
                else:
                    colors.append('#858796')  # Gray for others
            else:
                colors.append('#858796')  # Default gray

    return render_template(
        'dashboard.html',
        user=user,
        total=total,
        labels=labels,
        values=values,
        colors=colors,
        base_currency=user.base_currency,
        assets=active_assets,  # Only show assets with quantity > 0
        today=datetime.now().strftime('%Y-%m-%d'))


@app.route('/refresh-equity', methods=['POST'])
def refresh_equity():
    """Add monthly income to user's liquid equity."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('login'))
    
    user.liquid_equity += user.monthly_income
    db.session.commit()
    
    flash(f'Added {user.monthly_income:,.2f} {user.base_currency} to your liquid equity!', 'success')
    return redirect(url_for('dashboard'))

# ---------------------------
# Assets CRUD
# ---------------------------


@app.route('/assets')
def assets_list():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    # Filtering support via query params
    f_type = request.args.get('type', '').strip()
    f_currency = request.args.get('currency', '').strip()

    query = Asset.query.filter_by(user_id=user_id)
    if f_type:
        query = query.filter(Asset.asset_type == f_type)
    if f_currency:
        query = query.filter(Asset.currency == f_currency)

    assets = query.all()

    # Build lists for dropdowns (distinct values for this user)
    types_q = db.session.query(Asset.asset_type).filter(Asset.user_id == user_id).distinct().all()
    currencies_q = db.session.query(Asset.currency).filter(Asset.user_id == user_id).distinct().all()
    asset_types = [t[0] for t in types_q if t and t[0]]
    currencies = [c[0] for c in currencies_q if c and c[0]]

    return render_template('assets/list.html', assets=assets, asset_types=asset_types, currencies=currencies, f_type=f_type, f_currency=f_currency)


@app.route('/assets/add', methods=['GET', 'POST'])
def assets_add():
    """Disabled: Assets are now created automatically from transactions."""
    flash('Assets are created automatically when you add transactions. Please use the Transactions page.', 'info')
    return redirect(url_for('assets_buy'))


@app.route('/assets/edit/<int:asset_id>', methods=['GET', 'POST'])
def assets_edit(asset_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    asset = Asset.query.get_or_404(asset_id)
    # enforce ownership
    if asset.user_id != session['user_id']:
        flash('Not authorized', 'danger')
        return redirect(url_for('assets_list'))

    if request.method == 'POST':
        asset.name = request.form.get('name', asset.name)
        asset.quantity = float(
            request.form.get(
                'quantity',
                asset.quantity) or 0)
        asset.current_value = float(
            request.form.get(
                'current_value',
                asset.current_value) or 0)
        asset.purchase_date = request.form.get(
            'purchase_date') or asset.purchase_date
        asset.currency = request.form.get('currency') or asset.currency
        asset.color = request.form.get('color') or asset.color or '#4e73df'
        db.session.commit()
        flash('Asset updated', 'success')
        return redirect(url_for('assets_list'))
    return render_template('assets/edit.html', asset=asset)


@app.route('/assets/delete/<int:asset_id>', methods=['POST'])
def assets_delete(asset_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))

    asset = Asset.query.get_or_404(asset_id)

    # Ensure this asset belongs to the logged-in user
    if asset.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('assets_list'))

    # Delete all related transactions first
    Transaction.query.filter_by(asset_id=asset.id).delete()
    db.session.delete(asset)
    db.session.commit()

    flash('Asset and all related transactions deleted successfully.', 'success')
    return redirect(url_for('assets_list'))


@app.route('/assets/<int:asset_id>/sell', methods=['POST'])
def assets_sell(asset_id):
    """Sell (reduce quantity of) an asset by creating a Sell transaction."""
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    asset = Asset.query.get_or_404(asset_id)
    if asset.user_id != session['user_id']:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('dashboard'))
    
    try:
        quantity = float(request.form.get('quantity', 0))
        amount = float(request.form.get('amount', 0))  # Price per unit
        date_str = request.form.get('date')
        note = request.form.get('note', '').strip()
        
        if quantity <= 0 or amount <= 0:
            flash('Quantity and amount must be greater than zero.', 'danger')
            return redirect(url_for('dashboard'))
        
        if quantity > asset.quantity:
            flash(f'Cannot sell {quantity} units. Only {asset.quantity} units available.', 'danger')
            return redirect(url_for('dashboard'))
        
        # Parse date
        tx_date = parse_date_input(date_str)
        
        # Total sell value
        total_value = amount * quantity
        
        # Create Sell transaction
        tx = Transaction(
            user_id=session['user_id'],
            asset_id=asset_id,
            tx_type='Sell',
            quantity=quantity,
            amount=total_value,
            date=tx_date,
            note=note or f'Sold {quantity} units of {asset.name}'
        )
        db.session.add(tx)
        
        # Update asset using apply_transaction_effect
        apply_transaction_effect(asset, 'Sell', total_value, quantity)
        
        # Add proceeds to user's liquid equity
        user = User.query.get(session['user_id'])
        if user:
            user.liquid_equity += total_value
        
        # Keep the asset even if quantity is 0 (for transaction history)
        if asset.quantity <= 0:
            flash(f'Sold all units of {asset.name}. You no longer hold this asset. Added {total_value:,.2f} to liquid equity.', 'success')
        else:
            flash(f'Sold {quantity} units of {asset.name} successfully. Added {total_value:,.2f} to liquid equity.', 'success')
        
        db.session.commit()
        
    except Exception as e:
        db.session.rollback()
        flash(f'Error processing sale: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))


# ---------------------------
# Transactions
# ---------------------------
def parse_date_input(val):
    # Accept YYYY-MM-DD or ISO or datetime objects
    if val is None:
        return datetime.utcnow()
    if isinstance(val, datetime):
        return val
    try:
        # common form format
        return datetime.strptime(val, '%Y-%m-%d')
    except Exception:
        try:
            # attempt ISO parse
            return datetime.fromisoformat(val)
        except Exception:
            return datetime.utcnow()


@app.route('/transactions')
def transactions_list():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    q = request.args.get('q', '').strip()
    ttype = request.args.get('type', '')
    asset_id = request.args.get('asset_id', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    query = Transaction.query.join(Asset).filter(Asset.user_id == user_id)

    if q:
        query = query.filter(Transaction.note.ilike(f'%{q}%'))
    if ttype:
        query = query.filter(Transaction.tx_type == ttype)
    if asset_id:
        try:
            query = query.filter(Transaction.asset_id == int(asset_id))
        except ValueError:
            pass
    if start_date:
        try:
            query = query.filter(Transaction.date >= datetime.strptime(start_date, "%Y-%m-%d"))
        except Exception:
            pass
    if start_date:
        start_dt = parse_date_filter(start_date)
        if start_dt:
            query = query.filter(Transaction.date >= start_dt)
        else:
            flash('Invalid start date filter provided.', 'warning')
    if end_date:
        end_dt = parse_date_filter(end_date)
        if end_dt:
            query = query.filter(Transaction.date < end_dt + timedelta(days=1))
        else:
            flash('Invalid end date filter provided.', 'warning')

    txs = query.order_by(Transaction.date.desc()).all()
    assets = Asset.query.filter_by(user_id=user_id).all()
    asset_map = {a.id: a.name for a in assets}

    return render_template(
        'transactions/list.html',
        txs=txs,
        assets=assets,
        asset_map=asset_map,
        q=q,
        ttype=ttype,
        asset_id=asset_id,
        start_date=start_date,
        end_date=end_date)


@app.route('/api/master-assets')
def api_master_assets():
    """Search master assets (symbol/name). Returns JSON list.

    Query params:
      q: search string (symbol or name)
      type: optional asset_type filter
      limit: optional int (default 50)
    """
    if 'user_id' not in session:
        return jsonify({'error': 'not authenticated'}), 401

    q = request.args.get('q', '').strip()
    typ = request.args.get('type', '').strip()
    try:
        limit = min(int(request.args.get('limit', 50)), 200)
    except Exception:
        limit = 50

    query = MasterAsset.query
    if q:
        likeq = f"%{q}%"
        query = query.filter((MasterAsset.name.ilike(likeq)) | (MasterAsset.symbol.ilike(likeq)))
    if typ:
        query = query.filter(MasterAsset.asset_type == typ)

    results = query.order_by(MasterAsset.symbol).limit(limit).all()
    return jsonify([r.to_dict() for r in results])


@app.route('/api/price/<symbol>/<asset_type>')
def api_get_price(symbol, asset_type):
    """Get current market price for a symbol."""
    if 'user_id' not in session:
        return jsonify({'error': 'not authenticated'}), 401
    
    try:
        price = get_latest_price(symbol, asset_type)
        if price:
            return jsonify({'price': price, 'symbol': symbol})
        else:
            return jsonify({'error': 'Could not fetch price'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/assets/buy', methods=['GET', 'POST'])
@app.route('/transactions/add', methods=['GET', 'POST'])  # Keep old route for compatibility
def assets_buy():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    assets = Asset.query.filter_by(user_id=user_id).all()

    if request.method == 'POST':
        # ✅ Parse quantity and amount first (needed before asset creation)
        try:
            quantity = float(request.form.get('quantity', 1) or 1)
        except Exception:
            quantity = 1.0
        quantity = abs(quantity)
        if quantity <= 0:
            flash('Quantity must be greater than zero.', 'danger')
            return redirect(url_for('assets_buy'))

        # ✅ Asset Selection: support user's asset or master asset selection
        raw_choice = request.form.get('asset_choice') or request.form.get('asset_id')
        if not raw_choice:
            flash('Invalid asset selected', 'warning')
            return redirect(url_for('assets_buy'))

        asset = None
        master = None
        # user asset prefix
        if str(raw_choice).startswith('u:'):
            try:
                asset_id = int(raw_choice.split(':', 1)[1])
            except Exception:
                flash('Invalid asset selection', 'warning')
                return redirect(url_for('assets_buy'))
            asset = Asset.query.get(asset_id)
        elif str(raw_choice).startswith('m:'):
            # master asset selected: create per-user Asset if missing
            symbol = raw_choice.split(':', 1)[1]
            master = MasterAsset.query.filter_by(symbol=symbol).first()
            if not master:
                flash('Selected market asset not found', 'warning')
                return redirect(url_for('assets_buy'))
            # try find existing user asset by name
            asset = Asset.query.filter_by(user_id=user_id, name=master.name).first()
            if not asset:
                # Create with initial 0 values, will be updated by transaction effect
                asset = Asset(
                    user_id=user_id,
                    asset_type=master.asset_type or 'Market',
                    name=master.name or symbol,
                    symbol=master.symbol,  # Store the ticker symbol
                    quantity=0,
                    current_value=0,
                    purchase_date=None,
                    currency=master.currency or 'USD',
                    color=None
                )
                db.session.add(asset)
                db.session.flush()
            asset_id = asset.id
        else:
            # backward-compatible numeric id
            try:
                asset_id = int(raw_choice)
            except Exception:
                flash('Invalid asset selection', 'warning')
                return redirect(url_for('assets_buy'))
            asset = Asset.query.get(asset_id)

        tx_type_raw = request.form.get('type', 'Income').strip()
        normalized_type = tx_type_raw.lower()
        if normalized_type not in ALLOWED_TRANSACTION_TYPES:
            flash('Invalid transaction type selected.', 'danger')
            return redirect(url_for('assets_buy'))
        # Normalize stored tx type to Title case (Buy, Sell, Income, Expense)
        tx_type = normalized_type.title()

        # ✅ Amount Validation - if not provided, try to fetch price and calculate
        amount_raw = request.form.get('amount', '').strip()
        if not amount_raw or amount_raw == '':
            # Try to fetch current price for the asset
            current_price = None
            symbol_to_fetch = None
            asset_type_to_use = None
            
            if master:  # If selecting from master asset, use the symbol directly
                symbol_to_fetch = master.symbol
                asset_type_to_use = master.asset_type
            elif asset:  # If using existing user asset, extract symbol from name
                # Try to extract symbol from name (format: "Name (Type)")
                asset_name = asset.name
                if '(' in asset_name:
                    symbol_to_fetch = asset_name.split('(')[0].strip()
                else:
                    symbol_to_fetch = asset_name
                asset_type_to_use = asset.asset_type
            
            if symbol_to_fetch:
                current_price = get_latest_price(symbol_to_fetch, asset_type_to_use)
            
            if current_price and current_price > 0:
                amount = quantity * current_price
                flash(f'Price fetched: {current_price:.2f} per unit. Total: {amount:.2f}', 'info')
            else:
                # If price fetch fails, require manual entry
                flash('Could not fetch price automatically. Please enter the amount manually.', 'warning')
                return redirect(url_for('assets_buy'))
        else:
            try:
                amount = float(amount_raw)
            except Exception:
                amount = 0.0
        
        amount = abs(amount)
        if amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('assets_buy'))
        
        # Get current user for liquid equity check
        user = User.query.get(user_id)
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('login'))
        
        # Check if user has enough liquid equity for Buy transactions
        if tx_type.lower() == 'buy':
            if user.liquid_equity < amount:
                flash(f'Insufficient liquid equity! You need {amount:,.2f} but only have {user.liquid_equity:,.2f} {user.base_currency}', 'danger')
                return redirect(url_for('assets_buy'))

        # ✅ Description / Note
        note_raw = request.form.get('note', '')
        note = note_raw.strip() if note_raw else ''
        # ✅ Date Validation
        date_raw = request.form.get('date')
        date = parse_date_input(date_raw)

        # ✅ Ensure asset belongs to the current user
        if not asset or asset.user_id != user_id:
            flash('Invalid asset', 'danger')
            return redirect(url_for('assets_buy'))

        # ✅ Create Transaction
        tx = Transaction(
            asset_id=asset_id,
            tx_type=tx_type,
            quantity=quantity,
            amount=amount,
            date=date,
            note=note or None,
            user_id=user_id
        )

        db.session.add(tx)

        try:
            # apply business logic that may raise ValueError (e.g., invalid sell)
            apply_transaction_effect(asset, tx_type, amount, quantity)
            
            # Update user's liquid equity based on transaction type
            if tx_type.lower() == 'buy':
                user.liquid_equity -= amount  # Deduct money when buying
            elif tx_type.lower() == 'sell':
                user.liquid_equity += amount  # Add money when selling
                
        except ValueError as exc:
            db.session.rollback()
            flash(str(exc), 'danger')
            return redirect(url_for('assets_buy'))

        # apply_transaction_effect already updated `asset.current_value`.
        # Just persist the transaction and asset state.
        db.session.commit()
        flash('Transaction recorded successfully!', 'success')
        return redirect(url_for('transactions_list'))

    # Convert Asset objects to dictionaries for JSON serialization in template
    assets_data = [{'id': a.id, 'name': a.name, 'asset_type': a.asset_type, 'currency': a.currency} for a in assets]
    return render_template('transactions/add.html', assets=assets_data)



@app.route('/transactions/edit/<int:tx_id>', methods=['GET', 'POST'])
def transactions_edit(tx_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user_id = session['user_id']
    tx = Transaction.query.get_or_404(tx_id)
    assets = Asset.query.filter_by(user_id=user_id).all()
    # Ensure this transaction belongs to the logged-in user's asset
    if tx.user_id != user_id:
        flash('Unauthorized access', 'danger')
        return redirect(url_for('transactions_list'))
    if request.method == 'POST':
        original_asset = tx.asset
        original_type = tx.tx_type
        original_amount = tx.amount
        original_note = tx.note
        original_date = tx.date

        try:
            new_asset_id = int(request.form.get('asset_id', tx.asset_id))
        except (TypeError, ValueError):
            flash('Invalid asset selection.', 'danger')
            return redirect(url_for('transactions_edit', tx_id=tx_id))

        new_asset = next((a for a in assets if a.id == new_asset_id), None)
        if not new_asset:
            flash('Invalid asset selection.', 'danger')
            return redirect(url_for('transactions_edit', tx_id=tx_id))

        new_type_raw = request.form.get('type', tx.tx_type or '').strip()
        normalized_type = new_type_raw.lower()
        if normalized_type not in ALLOWED_TRANSACTION_TYPES:
            flash('Invalid transaction type.', 'danger')
            return redirect(url_for('transactions_edit', tx_id=tx_id))
        new_type = normalized_type.title()

        try:
            new_amount = float(request.form.get('amount', tx.amount))
        except (TypeError, ValueError):
            new_amount = 0.0

        if new_amount <= 0:
            flash('Amount must be greater than zero.', 'danger')
            return redirect(url_for('transactions_edit', tx_id=tx_id))

        new_amount = abs(new_amount)

        try:
            apply_transaction_effect(original_asset, original_type, original_amount, reverse=True)
        except ValueError:
            db.session.rollback()
            flash('Failed to update transaction due to inconsistent data.', 'danger')
            return redirect(url_for('transactions_list'))

        tx.asset_id = new_asset.id
        tx.tx_type = new_type
        tx.amount = new_amount
        new_note = request.form.get('note', '')
        tx.note = new_note.strip() if new_note is not None else ''
        if tx.note == '':
            tx.note = None

        date_input = request.form.get('date', None)
        if date_input:
            tx.date = parse_date_input(date_input)

        try:
            apply_transaction_effect(new_asset, new_type, new_amount)
        except ValueError as exc:
            apply_transaction_effect(original_asset, original_type, original_amount)
            tx.asset_id = original_asset.id
            tx.tx_type = original_type
            tx.amount = original_amount
            tx.note = original_note
            tx.date = original_date
            db.session.rollback()
            flash(str(exc), 'danger')
            return redirect(url_for('transactions_edit', tx_id=tx_id))

        db.session.commit()
        flash('Transaction updated successfully!', 'success')
        return redirect(url_for('transactions_list'))

    return render_template('transactions/edit.html', tx=tx, assets=assets)


# ---------------------------
# Exports (CSV & PDF) - convert to user's base currency
# ---------------------------
@app.route('/export/csv')
def export_csv():  # pragma: no cover
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    rates = load_rates()
    assets = Asset.query.filter_by(user_id=session['user_id']).all()
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow(['asset_type',
                 'name',
                 'quantity',
                 'value_in_asset_currency',
                 'asset_currency',
                 'value_in_base_currency',
                 'base_currency',
                 'purchase_date',
                 'color'])
    for a in assets:
        rate_from = rates.get(a.currency, 1.0)
        rate_to = rates.get(user.base_currency, 1.0)
        converted = a.current_value / rate_from * \
            rate_to if rate_from else a.current_value
        cw.writerow([a.asset_type,
                     a.name,
                     a.quantity,
                     a.current_value,
                     a.currency,
                     converted,
                     user.base_currency,
                     a.purchase_date or '',
                     a.color or ''])
    mem = io.BytesIO()
    mem.write(si.getvalue().encode('utf-8'))
    mem.seek(0)
    return send_file(
        mem,
        mimetype='text/csv',
        download_name='assets_converted.csv',
        as_attachment=True)


@app.route('/export/pdf')
def export_pdf():  # pragma: no cover
    if 'user_id' not in session:
        return redirect(url_for('login'))
    user = User.query.get(session['user_id'])
    rates = load_rates()
    assets = Asset.query.filter_by(user_id=session['user_id']).all()

    # Prepare memory buffer
    mem = io.BytesIO()
    doc = SimpleDocTemplate(mem, pagesize=letter)
    elements = []

    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'title_style',
        parent=styles['Heading1'],
        fontSize=16,
        leading=22,
        textColor=colors.HexColor('#333'))
    # Title
    title = Paragraph(
        f"Assets Report (Base Currency: {user.base_currency})",
        title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table header
    data = [['Type', 'Name', 'Quantity', 'Asset Value', 'Currency',
             f'Value in {user.base_currency}', 'Purchase Date', 'Color']]

    total_networth = 0.0
    for a in assets:
        rate_from = rates.get(a.currency, 1.0)
        rate_to = rates.get(user.base_currency, 1.0)
        converted = a.current_value / rate_from * \
            rate_to if rate_from else a.current_value
        total_networth += converted
        data.append([
            a.asset_type.capitalize(),
            a.name,
            f"{a.quantity:,.2f}",
            f"{a.current_value:,.2f}",
            a.currency,
            f"{converted:,.2f}",
            a.purchase_date or '-',
            a.color or ''
        ])

    # Create Table
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e3f2fd')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#0d47a1')),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9)
    ]))

    elements.append(table)
    elements.append(Spacer(1, 20))

    # Add total net worth section
    total_style = ParagraphStyle(
        'total_style',
        parent=styles['Heading2'],
        fontSize=14,
        leading=18,
        textColor=colors.HexColor('#1b5e20'),
        alignment=1
    )
    total_para = Paragraph(
        f"<b>Total Net Worth: {total_networth:,.2f} {user.base_currency}</b>",
        total_style)
    elements.append(total_para)

    # Build PDF
    doc.build(elements)
    mem.seek(0)
    return send_file(
        mem,
        mimetype='application/pdf',
        download_name='assets_report.pdf',
        as_attachment=True)
# ---------------------------
# API networth
# ---------------------------


@app.route('/api/networth')
def api_networth():
    if 'user_id' not in session:
        return jsonify({'error': 'not authenticated'}), 401
    user = User.query.get(session['user_id'])
    rates = load_rates()
    assets = Asset.query.filter_by(user_id=user.id).all()
    total = 0.0
    for a in assets:
        rate_from = rates.get(a.currency, 1.0)
        rate_to = rates.get(user.base_currency, 1.0)
        converted = a.current_value / rate_from * \
            rate_to if rate_from else a.current_value
        total += converted
    return jsonify({'networth': total, 'currency': user.base_currency})

# ---------------------------
# Template context processor
# ---------------------------

if __name__ == '__main__':  # pragma: no cover
    app.run(debug=True)
