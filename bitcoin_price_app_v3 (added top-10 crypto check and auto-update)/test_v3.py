import unittest
import json
from unittest.mock import patch, MagicMock
import app

# — use an in‑memory database for all tests —
app.DATABASE = ':memory:'
app.init_db()


class TestCryptoUtils(unittest.TestCase):
    @patch('app.Spot')
    def test_get_top_10_cryptos(self, mock_spot_cls):
        # fake tickers: only USDT pairs count, sorted by lastPrice*volume
        fake_tickers = [
            {'symbol': 'AAAUSDT', 'lastPrice': '2', 'volume': '100'},   # cap=200
            {'symbol': 'ZZZUSDT', 'lastPrice': '1', 'volume': '500'},   # cap=500
            {'symbol': 'CCCUSDT', 'lastPrice': '3', 'volume': '100'},   # cap=300
            {'symbol': 'NOTUSD',  'lastPrice': '5', 'volume': '1000'},  # dropped
        ]
        mock_client = MagicMock()
        mock_client.ticker_24hr.return_value = fake_tickers
        mock_spot_cls.return_value = mock_client

        top10 = app.get_top_10_cryptos()
        # should only include our USDT pairs, in descending cap order
        self.assertEqual(top10, ['ZZZUSDT', 'CCCUSDT', 'AAAUSDT'])

    def test_user_preferences_default(self):
        # grab Scott's user_id from the freshly initialized DB
        db = app.get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username='Scott'")
        user_id = cur.fetchone()['id']
        db.close()

        prefs = app.get_user_preferences(user_id)
        self.assertCountEqual(prefs, ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'])

    def test_update_user_preferences(self):
        db = app.get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username='Scott'")
        user_id = cur.fetchone()['id']
        db.close()

        # overwrite Scott's prefs
        new_syms = ['SOLUSDT', 'DOTUSDT']
        ok = app.update_user_preferences(user_id, new_syms)
        self.assertTrue(ok)

        # confirm they stuck
        prefs = app.get_user_preferences(user_id)
        self.assertCountEqual(prefs, new_syms)

    @patch('app.Spot')
    def test_get_crypto_prices(self, mock_spot_cls):
        symbols = ['BTCUSDT', 'ETHUSDT']

        # Binance client returns lists for batch requests
        fake_prices = [
            {'symbol': 'BTCUSDT', 'price': '100.0'},
            {'symbol': 'ETHUSDT', 'price': '50.0'}
        ]
        fake_24h = [
            {'symbol': 'BTCUSDT', 'priceChangePercent': '10', 'prevClosePrice': '90', 'volume': '1000'},
            {'symbol': 'ETHUSDT', 'priceChangePercent': '-5', 'prevClosePrice': '55', 'volume': '500'}
        ]

        mock_client = MagicMock()
        mock_client.ticker_price.return_value = fake_prices
        mock_client.ticker_24hr.return_value = fake_24h
        mock_spot_cls.return_value = mock_client

        prices = app.get_crypto_prices(symbols)
        # BTC
        self.assertIn('BTCUSDT', prices)
        self.assertEqual(prices['BTCUSDT']['price'], '$100.00')
        self.assertEqual(prices['BTCUSDT']['change'], '10.00%')
        self.assertEqual(prices['BTCUSDT']['price_color'], '#00FF00')
        # ETH negative change
        self.assertEqual(prices['ETHUSDT']['change_color'], '#FF0000')


class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        app.app.testing = True
        self.client = app.app.test_client()

    def login(self, user='Scott', pwd='password1'):
        return self.client.post('/login', data={'username': user, 'password': pwd})

    def test_login_logout_flow(self):
        # POST /login
        resp = self.login()
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/', resp.headers['Location'])

        # GET /logout clears session
        resp2 = self.client.get('/logout')
        self.assertEqual(resp2.status_code, 302)
        self.assertIn('/login', resp2.headers['Location'])

    def test_index_requires_auth(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    @patch('app.get_top_10_cryptos', return_value=['AAAUSDT'])
    @patch('app.get_crypto_prices', return_value={'AAAUSDT': {'price': '$1.00'}})
    def test_index_shows_data_after_login(self, mock_prices, mock_top10):
        # login then hit /
        self.login()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        # our mocked coin should appear in the HTML
        self.assertIn(b'AAAUSDT', resp.data)

    @patch('app.get_crypto_prices', return_value={'SOLUSDT': {'price': '$2.00'}})
    def test_update_preferences_endpoint(self, mock_prices):
        self.login()
        resp = self.client.post(
            '/update_preferences',
            json={'symbols': ['SOLUSDT']}
        )
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('symbols'), ['SOLUSDT'])
        self.assertIn('prices', data)

    @patch('app.get_crypto_prices', return_value={'FOO': {'price': '$3.00'}})
    def test_api_prices_with_query(self, mock_prices):
        self.login()
        resp = self.client.get('/api/prices?symbols=FOO,BAR')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('FOO', data)

    @patch('app.get_crypto_prices', return_value={'DEFAULT': {'price': '$4.00'}})
    def test_api_prices_default_to_user_prefs(self, mock_prices):
        self.login()
        resp = self.client.get('/api/prices')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('DEFAULT', data)

    @patch('app.get_top_10_cryptos', return_value=['ZZZ'])
    def test_api_top10(self, mock_top10):
        resp = self.client.get('/api/top10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data.get('top_10'), ['ZZZ'])


if __name__ == '__main__':
    unittest.main()