import os
import sqlite3
import tempfile
import unittest
import json
from unittest.mock import patch

# Ensure we import the app after possibly removing any existing DB
if os.path.exists('crypto_tracker.db'):
    os.remove('crypto_tracker.db')

from app_v4 import app, init_db, get_crypto_prices, get_crypto_news

class CryptoAppTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary file to act as our database
        self.db_fd, self.db_path = tempfile.mkstemp()
        # Configure app for testing
        app.config['TESTING'] = True
        # Monkey‑patch sqlite3.connect to use the temp DB
        self._orig_connect = sqlite3.connect
        sqlite3.connect = lambda *args, **kwargs: self._orig_connect(self.db_path, **kwargs)
        # Initialize the fresh database with seed users/preferences
        init_db()
        self.client = app.test_client()

    def tearDown(self):
        # Restore original sqlite3.connect, remove temp DB
        sqlite3.connect = self._orig_connect
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login(self, username, password):
        return self.client.post('/login', data={
            'username': username,
            'password': password
        }, follow_redirects=True)

    def test_home_redirects_when_not_logged_in(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.location)

    def test_login_success(self):
        rv = self.login('Scott', 'password1')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Scott', rv.data)

    def test_login_failure(self):
        rv = self.login('Scott', 'wrongpassword')
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b'Invalid username or password', rv.data)

    @patch('app_v4.get_crypto_prices')
    @patch('app_v4.get_crypto_news')
    def test_index_authenticated(self, mock_news, mock_prices):
        # Mock both price and news calls
        mock_prices.return_value = {
            'BTCUSDT': {'price': '$40,000.00', 'change': '1.23%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'BTC'},
            'ETHUSDT': {'price': '$3,000.00', 'change': '0.50%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'ETH'},
            'BNBUSDT': {'price': '$500.00', 'change': '-1.00%', 'price_color': '#FF0000', 'change_color': '#FF0000',
                        'symbol_short': 'BNB'}
        }

        mock_news.return_value = [{'title':'Test News','url':'http://u','description':'desc','publishedAt':'2025-04-18'}]
        self.login('Scott', 'password1')
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'BTCUSDT', resp.data)
        self.assertIn(b'Test News', resp.data)

    def test_api_prices_unauthenticated(self):
        resp = self.client.get('/api/prices')
        self.assertEqual(resp.status_code, 401)
        data = json.loads(resp.data)
        self.assertIn('error', data)

    @patch('app_v4.get_crypto_prices')
    def test_api_prices_authenticated(self, mock_prices):
        mock_prices.return_value = {
            'BTCUSDT': {'price': '$40,000.00', 'change': '1.23%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'BTC'},
            'ETHUSDT': {'price': '$3,000.00', 'change': '-0.50%', 'price_color': '#FF0000', 'change_color': '#FF0000',
                        'symbol_short': 'ETH'},
            'BNBUSDT': {'price': '$500.00', 'change': '-1.00%', 'price_color': '#FF0000', 'change_color': '#FF0000',
                        'symbol_short': 'BNB'}
        }
        self.login('Scott', 'password1')
        resp = self.client.get('/api/prices')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('ETHUSDT', data)

    @patch('app_v4.get_crypto_news')
    def test_api_news(self, mock_news):
        mock_news.return_value = [{'title':'t','url':'u','description':'d','publishedAt':'2025-04-18'}]
        resp = self.client.get('/api/news')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)

    @patch('app_v4.get_crypto_prices')
    def test_update_preferences(self, mock_prices):
        mock_prices.return_value = {
            'ADAUSDT': {'price': '$2.00', 'change': '5.00%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'ADA'},
            'BTCUSDT': {'price': '$40,000.00', 'change': '1.23%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'BTC'},
            'ETHUSDT': {'price': '$3,000.00', 'change': '0.50%', 'price_color': '#00FF00', 'change_color': '#00FF00',
                        'symbol_short': 'ETH'},
            'BNBUSDT': {'price': '$500.00', 'change': '-1.00%', 'price_color': '#FF0000', 'change_color': '#FF0000',
                        'symbol_short': 'BNB'}
        }
        self.login('Scott', 'password1')
        resp = self.client.post('/update_preferences',
                                data=json.dumps({'symbols': ['ADAUSDT']}),
                                content_type='application/json'
                                )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        self.assertIn('ADAUSDT', data.get('symbols', []))


if __name__ == '__main__':
    unittest.main()
