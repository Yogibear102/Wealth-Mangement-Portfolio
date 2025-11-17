# Setting up Twelve Data API

## Steps:

1. **Get your free API key:**

   - Go to: https://twelvedata.com/apikey
   - Sign up with your email
   - Copy your API key (looks like: `abc123def456...`)

2. **Create `.env` file:**

   ```bash
   cd /Users/deezathxrv/Downloads/PESU_RR_CSE_E_P06_Personal_Wealth_Management_Software_THE-QUAD-SQUAD
   cp .env.example .env
   ```

3. **Edit `.env` file:**
   Open `.env` and replace `your_api_key_here` with your actual API key:

   ```
   TWELVE_DATA_API_KEY=abc123def456your_actual_key_here
   ```

4. **Restart the app:**
   ```bash
   pkill -f "python3 app.py" 2>/dev/null
   source venv/bin/activate
   python3 app.py
   ```

## What you get with free tier:

- ✅ 800 API calls per day
- ✅ Real-time stock prices (AAPL, GOOGL, MSFT, etc.)
- ✅ Forex rates (EUR/USD, GBP/USD, etc.)
- ✅ Commodity prices (Gold, Silver as XAU/USD, XAG/USD)
- ✅ 5-minute caching to conserve requests
- ✅ Automatic fallback to yfinance if API fails

## Coverage estimate:

With 40-50 assets and 5-minute caching:

- Each price fetched once per 5 minutes
- Max ~12 times per hour per asset
- ~288 requests per day for all assets
- **Plenty of headroom within 800 limit!**
