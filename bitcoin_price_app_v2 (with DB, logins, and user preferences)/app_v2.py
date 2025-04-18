from flask import Flask, render_template, jsonify, request, redirect, url_for, session
from binance.spot import Spot
import time
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import os
import warnings

warnings.filterwarnings("ignore", category=Warning)

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

API_KEY = 'PK0eqkV0Wy0buE6eSmm0qkGMSIbZF0LEPcNjXpFIvpSG4KqdBG61TQmrDD1NVRUX'
API_SECRET = 'yDZKIcfldKSq9FIaFYw9VylTIVhRAJF7zsdsBd1NSuYXR6bQuhnWJ1zQ3B4nn4HS'


def init_db():
    conn = sqlite3.connect('crypto_tracker.db')
    c = conn.cursor()

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')

    c.execute('''CREATE TABLE IF NOT EXISTS preferences
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER NOT NULL,
                  symbol TEXT NOT NULL,
                  FOREIGN KEY(user_id) REFERENCES users(id))''')

    users = [
        ('Scott', 'password1', ['BTCUSDT', 'ETHUSDT', 'SOLUSDT']),
        ('Georgii', 'password2', ['BNBUSDT', 'ADAUSDT', 'DOTUSDT']),
        ('Ayushman', 'password3', ['XRPUSDT', 'DOGEUSDT', 'AVAXUSDT']),
        ('Kunal', 'password4', ['SHIBUSDT', 'MATICUSDT', 'LTCUSDT'])
    ]

    for username, password, preferred_symbols in users:
        c.execute("SELECT id FROM users WHERE username = ?", (username,))
        user = c.fetchone()

        if not user:
            hashed_pw = generate_password_hash(password, method='pbkdf2:sha256', salt_length=8)
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)",
                      (username, hashed_pw))
            user_id = c.lastrowid

            for symbol in preferred_symbols:
                c.execute("INSERT INTO preferences (user_id, symbol) VALUES (?, ?)",
                          (user_id, symbol))

    conn.commit()
    conn.close()


if not os.path.exists('crypto_tracker.db'):
    init_db()


def get_user_preferences(user_id):
    conn = sqlite3.connect('crypto_tracker.db')
    c = conn.cursor()
    c.execute("SELECT symbol FROM preferences WHERE user_id = ?", (user_id,))
    preferences = [row[0] for row in c.fetchall()]
    conn.close()
    return preferences or ['BTCUSDT', 'ETHUSDT', 'BNBUSDT']


def update_user_preferences(user_id, symbols):
    conn = sqlite3.connect('crypto_tracker.db')
    c = conn.cursor()
    c.execute("DELETE FROM preferences WHERE user_id = ?", (user_id,))
    for symbol in symbols:
        c.execute("INSERT INTO preferences (user_id, symbol) VALUES (?, ?)",
                  (user_id, symbol))
    conn.commit()
    conn.close()
    return True


def get_crypto_prices(symbols):
    try:
        client = Spot(api_key=API_KEY, api_secret=API_SECRET)
        prices = {}

        for symbol in symbols:
            ticker = client.ticker_price(symbol)
            ticker_24h = client.ticker_24hr(symbol)

            current_price = float(ticker['price'])
            change_24h = float(ticker_24h['priceChangePercent'])
            prev_close_price = float(ticker_24h['prevClosePrice'])

            price_color = '#00FF00' if current_price > prev_close_price else '#FF0000'
            change_color = '#00FF00' if change_24h >= 0 else '#FF0000'

            prices[symbol] = {
                'price': f"${current_price:,.2f}",
                'change': f"{change_24h:.2f}%",
                'price_color': price_color,
                'change_color': change_color,
                'symbol_short': symbol.replace('USDT', '')
            }

        return prices
    except Exception as e:
        print(f"Error fetching prices: {str(e)}")
        return {}


@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user_id = session['user_id']
    symbols = get_user_preferences(user_id)
    prices = get_crypto_prices(symbols)

    return render_template('index_v3.1.html',
                           username=session.get('username'),
                           symbols=symbols,
                           prices=prices)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('crypto_tracker.db')
        c = conn.cursor()
        c.execute("SELECT id, password FROM users WHERE username = ?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session['user_id'] = user[0]
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/update_preferences', methods=['POST'])
def update_preferences():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    symbols = request.form.getlist('symbols[]')
    if not symbols:
        return jsonify({'error': 'Please select at least one cryptocurrency'}), 400

    if update_user_preferences(session['user_id'], symbols):
        prices = get_crypto_prices(symbols)
        return jsonify({
            'success': True,
            'prices': prices,
            'symbols': symbols
        })
    return jsonify({'error': 'Failed to update preferences'}), 500


@app.route('/api/prices')
def api_prices():
    if 'user_id' not in session:
        return jsonify({'error': 'Not authenticated'}), 401

    symbols = get_user_preferences(session['user_id'])
    prices = get_crypto_prices(symbols)
    return jsonify(prices)


if __name__ == '__main__':
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
        print("Could not find an available port between 5002-5010")