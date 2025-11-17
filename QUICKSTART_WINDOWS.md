# Quick Start Guide - Windows

This guide will help you get the Wealth Management Website running on Windows.

## Prerequisites

- **Python 3.10+** - Download from [python.org](https://www.python.org/downloads/)
  - **IMPORTANT:** Check "Add Python to PATH" during installation
- **Git** - Download from [git-scm.com](https://git-scm.com/)
- A terminal: Command Prompt, PowerShell, or Windows Terminal (recommended)

## Step 1: Clone the Repository

```bash
git clone https://github.com/Yogibear102/Wealth-management-website-.git
cd Wealth-management-website-
```

## Step 2: Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate.bat
```

**On PowerShell:**

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

## Step 3: Run Quickstart

Once inside the virtual environment, simply run:

```bash
quickstart.bat
```

This will:

1. ✅ Install all dependencies from `requirements.txt`
2. ✅ Create and populate the SQLite database with demo data
3. ✅ Load master assets (stocks, forex, commodities, etc.)
4. ✅ Start the Flask development server

## Step 4: Access the Application

Open your browser and navigate to:

```
http://127.0.0.1:5000
```

### Demo Credentials

- **Email:** `demo@example.com`
- **Password:** `Password123`

## Manual Steps (if quickstart fails)

If `quickstart.bat` encounters issues, run these commands manually:

```bash
# Install dependencies
pip install -r requirements.txt

# Setup database
python setup_db.py

# Load master assets
python scripts\update_master_assets.py

# Start Flask app
python app.py
```

## Optional: Use Live Market Data

To fetch real stock data from Finnhub:

```bash
# Set API key (Windows Command Prompt)
set FINNHUB_API_KEY=your_api_key_here
quickstart.bat

# OR (Windows PowerShell)
$env:FINNHUB_API_KEY = "your_api_key_here"
quickstart.bat
```

Get your free API key from [finnhub.io](https://finnhub.io)

## Running Tests

```bash
# Run all tests with coverage report
pytest tests/ --cov=app --cov=models --cov=price_fetcher --cov-report=html

# Or just run tests
pytest tests/
```

## Troubleshooting

### Error: "python: command not found"

- Make sure Python is installed and added to PATH
- Restart your terminal after installing Python
- Try `python --version` to verify installation

### Error: "venv\Scripts\activate.bat" not found

- Create the virtual environment first: `python -m venv venv`
- Make sure you're in the project root directory

### Database Lock Error

- Delete the `instance/pwm.db` file and run `python setup_db.py` again

### Port 5000 Already in Use

- Edit `app.py` and change the port in the `app.run()` call
- Or kill the process using port 5000:
  ```bash
  # Find process using port 5000
  netstat -ano | findstr :5000
  # Kill the process
  taskkill /PID <PID> /F
  ```

## Project Structure

```
Wealth-management-website-/
├── app.py                    # Main Flask application
├── models.py                 # Database models
├── price_fetcher.py          # Market price fetching
├── setup_db.py               # Database initialization
├── requirements.txt          # Python dependencies
├── quickstart.bat            # Windows quickstart script
├── scripts/
│   ├── quickstart.sh         # Unix/Linux/Mac quickstart
│   └── update_master_assets.py
├── templates/                # HTML templates
├── static/                   # CSS, JS assets
├── tests/                    # Unit and integration tests
└── instance/                 # Database (created at runtime)
```

## Next Steps

1. **Explore the Dashboard** - View your assets and portfolio allocation
2. **Add Transactions** - Buy stocks, forex, commodities, or real estate
3. **Export Reports** - Generate CSV or PDF reports of your portfolio
4. **Customize Settings** - Change your base currency and personal settings

## Support

For issues or questions:

- Check the [README.md](../README.md)
- Review test files in `tests/` for usage examples
- Check GitHub issues: https://github.com/Yogibear102/Wealth-management-website-

---

**Happy Wealth Management! 💰**
