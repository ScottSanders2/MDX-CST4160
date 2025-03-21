from flask import Flask, render_template, jsonify
from binance.spot import Spot
import time

app = Flask(__name__)

API_KEY = 'PK0eqkV0Wy0buE6eSmm0qkGMSIbZF0LEPcNjXpFIvpSG4KqdBG61TQmrDD1NVRUX'
API_SECRET = 'yDZKIcfldKSq9FIaFYw9VylTIVhRAJF7zsdsBd1NSuYXR6bQuhnWJ1zQ3B4nn4HS'


def get_crypto_prices():
    try:
        client = Spot(api_key=API_KEY, api_secret=API_SECRET)
        symbols = ['BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'ADAUSDT', 'SOLUSDT',
                   'XRPUSDT', 'DOTUSDT', 'DOGEUSDT', 'AVAXUSDT', 'SHIBUSDT']
        # Alternating colors: white and green
        colors = ['#FFFFFF', '#00FF00']  # White for odd index (0, 2, 4...), green for even (1, 3, 5...)
        ticker_data = []

        for symbol, color in zip(symbols, [colors[i % 2] for i in range(len(symbols))]):
            ticker = client.ticker_price(symbol)
            current_price = float(ticker['price'])
            ticker_24h = client.ticker_24hr(symbol)
            coin_data = {
                'current_price': f"${current_price:,.2f}",
                'change_24h': f"{float(ticker_24h['priceChangePercent']):.2f}%",
                'volume_24h': f"{float(ticker_24h['volume']):,.2f}",
                'symbol': symbol.replace('USDT', ''),
                'color': color
            }
            ticker_data.append(coin_data)

        ticker_text = ""
        for i, coin in enumerate(ticker_data):
            ticker_text += f'<span style="color: {coin["color"]}">{coin["symbol"]}/USDT: {coin["current_price"]} | 24h Change: {coin["change_24h"]} | Vol: {coin["volume_24h"]} {coin["symbol"]}</span>'
            if i < len(ticker_data) - 1:
                ticker_text += " | "

        # Repeat 2 times for continuous scrolling
        ticker_text = (ticker_text + " | ") * 2
        ticker_text = ticker_text.rstrip(" | ")

        print(f"[{time.strftime('%H:%M:%S')}] Generated ticker text, length: {len(ticker_text)} characters")
        return {
            'ticker_text': ticker_text,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        print(f"[{time.strftime('%H:%M:%S')}] Error in get_crypto_prices: {str(e)}")
        return {'error': str(e)}


@app.route('/')
def index():
    print(f"[{time.strftime('%H:%M:%S')}] Serving initial page")
    initial_data = get_crypto_prices()
    return render_template('index.html', initial_ticker_text=initial_data.get('ticker_text',
                                                                              '<span style="color: red">Error loading initial data</span>'))


@app.route('/api/price')
def api_price():
    print(f"[{time.strftime('%H:%M:%S')}] API price request received")
    price_data = get_crypto_prices()
    return jsonify(price_data)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)