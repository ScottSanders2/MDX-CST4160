# Crypto Tracker Backend (v4.1)
# Flask application with cryptocurrency price tracking, user preferences, database and news integration

# Import required libraries
from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from binance.spot import Spot  # Binance API client
import time
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import threading
import requests  # For News API integration

# Initialise Flask application
app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Change for production

# API configuration
API_KEY = 'PK0eqkV0Wy0buE6eSmm0qkGMSIbZF0LEPcNjXpFIvpSG4KqdBG61TQmrDD1NVRUX'  # Binance API key
API_SECRET = 'yDZKIcfldKSq9FIaFYw9VylTIVhRAJF7zsdsBd1NSuYXR6bQuhnWJ1zQ3B4nn4HS'  # Binance API secret
NEWSAPI_KEY = '8fef006f934b44feb0d763b7bda154ca'  # NewsAPI.org key
GUARDIAN_KEY = '88c40751-7bef-4a75-89a8-b450aca428e6'  # The Guardian API key

# Database configuration
DATABASE = 'crypto_tracker.db'  # SQLite database file

# Global variables for top 10 cryptocurrencies
top_10_lock = threading.Lock()  # Thread lock for top 10 list
top_10_cryptos = []  # Cached list of top 10 cryptos
last_updated = 0  # Timestamp of last update
UPDATE_INTERVAL = 300  # Update interval in seconds (5 minutes)

# Establishes and returns a database connection with row factory configuration
def get_db():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row  # Return rows as dictionaries
    return db

# Initialises the database with required tables and default data
def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()

        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL
            )
        ''')

        # Create preferences table with foreign key constraint
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id),
                UNIQUE(user_id, symbol)  # Prevent duplicate preferences
            )
        ''')

        # Default users and their preferred cryptocurrencies
        default_users = [
            ('Scott', 'password1'),
            ('Georgii', 'password2'),
            ('Ayushman', 'password3'),
            ('Kunal', 'password4')
        ]

        default_prefs = {
            'Scott': ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'],
            'Georgii': ['ADAUSDT', 'SOLUSDT', 'DOTUSDT'],
            'Ayushman': ['XRPUSDT', 'DOGEUSDT', 'AVAXUSDT'],
            'Kunal': ['SHIBUSDT', 'MATICUSDT', 'LTCUSDT']
        }

        # Insert default users and preferences
        for username, password in default_users:
            cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
            if not cursor.fetchone():
                hashed_pw = generate_password_hash(password)
                cursor.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                               (username, hashed_pw))
                user_id = cursor.lastrowid

                for symbol in default_prefs[username]:
                    cursor.execute('''
                        INSERT OR IGNORE INTO preferences (user_id, symbol) 
                        VALUES (?, ?)
                    ''', (user_id, symbol))

        db.commit()
        db.close()


# Create database if it doesn't exist
if not os.path.exists(DATABASE):
    init_db()

# Fetches and caches the top 10 cryptocurrencies by market cap from Binance
def get_top_10_cryptos():
    global top_10_cryptos, last_updated

    with top_10_lock:  # Thread-safe access to shared variables
        current_time = time.time()
        # Only update if cache is stale
        if current_time - last_updated > UPDATE_INTERVAL:
            try:
                client = Spot(api_key=API_KEY, api_secret=API_SECRET)
                tickers = client.ticker_24hr()

                # Filter for USDT pairs and sort by market cap (price*volume)
                usdt_pairs = [t for t in tickers if t['symbol'].endswith('USDT')]
                sorted_pairs = sorted(usdt_pairs,
                                      key=lambda x: float(x['lastPrice']) * float(x['volume']),
                                      reverse=True)

                # Update cache
                top_10_cryptos = [pair['symbol'] for pair in sorted_pairs[:10]]
                last_updated = current_time
            except Exception as e:
                app.logger.error(f"Error updating top 10 cryptos: {str(e)}")

    return top_10_cryptos

# Retrieves a user's saved cryptocurrency preferences from database
def get_user_preferences(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT symbol FROM preferences WHERE user_id = ?', (user_id,))
    preferences = [row['symbol'] for row in cursor.fetchall()]
    db.close()
    return preferences

# Updates a user's cryptocurrency preferences in the database
def update_user_preferences(user_id, symbols):
    try:
        db = get_db()
        cursor = db.cursor()

        # Start transaction
        cursor.execute('BEGIN TRANSACTION')

        # Clear existing preferences
        cursor.execute('DELETE FROM preferences WHERE user_id = ?', (user_id,))

        # Insert new preferences
        for symbol in symbols:
            cursor.execute('''
                INSERT INTO preferences (user_id, symbol) 
                VALUES (?, ?)
            ''', (user_id, symbol))

        db.commit()
        return True
    except Exception as e:
        db.rollback()  # Revert changes on error
        app.logger.error(f"Error updating preferences: {str(e)}")
        return False
    finally:
        db.close()  # Ensure connection is closed

# Fetches current prices and 24h changes for given cryptocurrencies
def get_crypto_prices(symbols):
    try:
        client = Spot(api_key=API_KEY, api_secret=API_SECRET)
        prices = {}

        # Process symbols in batches to avoid rate limiting
        batch_size = 10
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i + batch_size]

            # Get current prices for batch
            tickers = client.ticker_price(symbols=batch)
            ticker_map = {t['symbol']: t for t in tickers}

            # Get 24h changes for batch
            tickers_24h = client.ticker_24hr(symbols=batch)
            ticker_24h_map = {t['symbol']: t for t in tickers_24h}

            # Process each symbol in batch
            for symbol in batch:
                if symbol in ticker_map and symbol in ticker_24h_map:
                    current_price = float(ticker_map[symbol]['price'])
                    change_24h = float(ticker_24h_map[symbol]['priceChangePercent'])
                    prev_close = float(ticker_24h_map[symbol]['prevClosePrice'])

                    # Format price data with colors
                    prices[symbol] = {
                        'price': f"${current_price:,.2f}",
                        'change': f"{change_24h:.2f}%",
                        'price_color': '#00FF00' if current_price > prev_close else '#FF0000',
                        'change_color': '#00FF00' if change_24h >= 0 else '#FF0000',
                        'symbol_short': symbol.replace('USDT', '')
                    }

        return prices
    except Exception as e:
        app.logger.error(f"Error fetching prices: {str(e)}")
        return {}

# Fetches cryptocurrency news articles from NewsAPI
def get_newsapi_articles():
    try:
        url = "https://newsapi.org/v2/everything"
        params = {
            "q": "cryptocurrency OR bitcoin OR ethereum OR solana OR cardano OR ripple OR polkadot OR dogecoin OR litecoin OR stablecoin OR USDT OR USDC OR DAI OR crypto OR Binance OR Coinbase OR Kraken OR KuCoin OR OKX OR Bybit OR BingX OR HTX OR Huobi OR Bitget OR ICO OR SUI OR TRX FDUSD OR PEPE OR BNB",
            "sortBy": "publishedAt",
            "language": "en",
            "apiKey": NEWSAPI_KEY,
            "pageSize": 30
        }
        response = requests.get(url, params=params)
        data = response.json()
        articles = data.get("articles", [])
        return [{
            "title": a["title"],
            "url": a["url"],
            "description": a["description"],
            "publishedAt": a["publishedAt"][:10]
        } for a in articles]
    except Exception as e:
        app.logger.error(f"NewsAPI error: {str(e)}")
        return []

# Fetches cryptocurrency news articles from The Guardian API
def get_guardian_articles():
    try:
        url = "https://content.guardianapis.com/search"
        params = {
            "q": "cryptocurrency OR bitcoin OR ethereum OR solana OR cardano OR ripple OR polkadot OR dogecoin OR litecoin OR stablecoin OR USDT OR USDC OR DAI OR crypto OR Binance OR Coinbase OR Kraken OR KuCoin OR OKX OR Bybit OR BingX OR HTX OR Huobi OR Bitget OR ICO OR SUI OR TRX FDUSD OR PEPE OR BNB",
            "api-key": GUARDIAN_KEY,
            "show-fields": "trailText",
            "order-by": "newest",
            "page-size": 30
        }
        response = requests.get(url, params=params)
        data = response.json()
        results = data.get("response", {}).get("results", [])
        return [{
            "title": r["webTitle"],
            "url": r["webUrl"],
            "description": r.get("fields", {}).get("trailText", ""),
            "publishedAt": r["webPublicationDate"][:10]
        } for r in results]
    except Exception as e:
        app.logger.error(f"Guardian API error: {str(e)}")
        return []

# Combines news articles from multiple sources
def get_crypto_news():
    return get_newsapi_articles() + get_guardian_articles()

# Main application dashboard
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    top_10 = get_top_10_cryptos()  # Get top 10 cryptos
    user_prefs = get_user_preferences(user_id)  # Get user preferences

    # Combine and deduplicate symbols for price lookup
    all_symbols = list(set(top_10 + user_prefs))
    prices = get_crypto_prices(all_symbols)

    # Split preferences into top 10 and others for display
    top_10_prefs = [sym for sym in user_prefs if sym in top_10]
    other_prefs = [sym for sym in user_prefs if sym not in top_10]

    # Get news articles
    news = get_crypto_news()

    return render_template('index_v4.1.html',
                           username=session.get('username'),
                           top_10_cryptos=top_10,
                           top_10_prefs=top_10_prefs,
                           other_prefs=other_prefs,
                           prices=prices,
                           news=news)

# User authentication handling
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT id, password FROM users WHERE username = ?', (username,))
        user = cursor.fetchone()
        db.close()

        if user and check_password_hash(user['password'], password):
            # Successful login - set session
            session['user_id'] = user['id']
            session['username'] = username
            return redirect(url_for('index'))
        else:
            # Failed login
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

# Clears user session and redirects to login page
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# API endpoint for updating user preferences
@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    try:
        # Get JSON data from request
        data = request.get_json()
        if not data or 'symbols' not in data:
            return jsonify({'error': 'Invalid request data'}), 400

        symbols = data['symbols']
        if not isinstance(symbols, list):
            return jsonify({'error': 'Symbols must be an array'}), 400

        if len(symbols) == 0:
            return jsonify({'error': 'Please select at least one cryptocurrency'}), 400

        # Update preferences in database
        if not update_user_preferences(session['user_id'], symbols):
            return jsonify({'error': 'Failed to update database'}), 500

        # Get updated prices for response
        prices = get_crypto_prices(symbols)

        return jsonify({
            'success': True,
            'prices': prices,
            'symbols': symbols
        })

    except Exception as e:
        app.logger.error(f"Error updating preferences: {str(e)}")
        return jsonify({'error': str(e)}), 500

# API endpoint for fetching cryptocurrency prices
@app.route('/api/prices')
def api_prices():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    symbols = request.args.get('symbols')
    if symbols:
        symbols = symbols.split(',')
    else:
        symbols = get_user_preferences(session['user_id'])

    prices = get_crypto_prices(symbols)
    return jsonify(prices)

# API endpoint for fetching current top 10 cryptocurrencies
@app.route('/api/top10')
def api_top10():
    top_10 = get_top_10_cryptos()
    return jsonify({'top_10': top_10})

# API endpoint for fetching cryptocurrency news
@app.route('/api/news')
def api_news():
    return jsonify(get_crypto_news())

if __name__ == '__main__':
    # Initialize top 10 cryptos cache
    get_top_10_cryptos()

    # Find available port between 5000-5009
    port = 5002
    while port < 5010:
        try:
            app.run(debug=True, host='0.0.0.0', port=port)
            break
        except OSError as e:
            if "Address already in use" in str(e):
                print(f"Port {port} in use, trying next port...")
                port += 1
            else:
                raise
    else:
        print("Could not find an available port between 5000-5009")