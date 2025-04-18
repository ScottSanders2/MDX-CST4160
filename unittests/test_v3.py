import unittest
import json
from unittest.mock import patch, MagicMock
import app_v3 as app
import tempfile


class TestCryptoUtils(unittest.TestCase):
    def setUp(self):
        app.DATABASE = 'file::memory:?cache=shared'
        app.init_db()

    @patch('app_v3.Spot')
    def test_get_top_10_cryptos(self, mock_spot_cls):
        fake = [
            {'symbol': 'AAAUSDT', 'lastPrice': '2', 'volume': '100'},
            {'symbol': 'BBBABC', 'lastPrice': '5', 'volume': '10'}
        ]
        mock_client = MagicMock()
        mock_client.ticker_24hr.return_value = fake
        mock_spot_cls.return_value = mock_client

        top10 = app.get_top_10_cryptos()
        self.assertIn('AAAUSDT', top10)
        self.assertNotIn('BBBABC', top10)

    @patch('app_v3.Spot')
    def test_get_crypto_prices(self, mock_spot_cls):
        symbols = ['BTCUSDT', 'ETHUSDT']
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
        self.assertEqual(prices['BTCUSDT']['price'], '$100.00')
        self.assertEqual(prices['BTCUSDT']['change'], '10.00%')
        self.assertEqual(prices['BTCUSDT']['price_color'], '#00FF00')
        self.assertEqual(prices['ETHUSDT']['change_color'], '#FF0000')

    def test_update_user_preferences_and_get(self):
        db = app.get_db()
        cur = db.cursor()
        cur.execute("SELECT id FROM users WHERE username='Scott'")
        uid = cur.fetchone()['id']
        db.close()

        new_syms = ['SOLUSDT', 'DOTUSDT']
        ok = app.update_user_preferences(uid, new_syms)
        self.assertTrue(ok)

        prefs = app.get_user_preferences(uid)
        self.assertCountEqual(prefs, new_syms)


class TestAppRoutes(unittest.TestCase):
    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp()
        app.DATABASE = self.db_path
        app.init_db()
        app.app.testing = True
        self.client = app.app.test_client()

    def tearDown(self):
        import os
        os.close(self.db_fd)
        os.unlink(self.db_path)

    def login(self, user='Scott', pwd='password1'):
        return self.client.post('/login', data={'username': user, 'password': pwd})

    def test_login_logout_flow(self):
        resp = self.login()
        self.assertEqual(resp.status_code, 302)
        resp2 = self.client.get('/logout')
        self.assertEqual(resp2.status_code, 302)
        self.assertIn('/login', resp2.headers['Location'])

    def test_index_requires_auth(self):
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 302)
        self.assertIn('/login', resp.headers['Location'])

    @patch('app_v3.get_crypto_prices', return_value={'SOLUSDT': {'price': '$2.00'}})
    def test_update_preferences_endpoint(self, mock_prices):
        self.login()
        resp = self.client.post('/update_preferences', json={'symbols': ['SOLUSDT']})
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertTrue(data.get('success'))
        self.assertEqual(data.get('symbols'), ['SOLUSDT'])
        self.assertIn('prices', data)

    @patch('app_v3.get_crypto_prices', return_value={'FOO': {'price': '$3.00'}})
    def test_api_prices_with_query(self, mock_prices):
        self.login()
        resp = self.client.get('/api/prices?symbols=FOO')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('FOO', data)

    @patch('app_v3.get_user_preferences', return_value=['DEFAULT'])
    @patch('app_v3.get_crypto_prices', return_value={'DEFAULT': {'price': '$4.00'}})
    def test_api_prices_default_to_user_prefs(self, mock_prices, mock_prefs):
        self.login()
        resp = self.client.get('/api/prices')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('DEFAULT', data)

    @patch('app_v3.get_top_10_cryptos', return_value=['ZZZ'])
    def test_api_top10(self, mock_top10):
        resp = self.client.get('/api/top10')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data.get('top_10'), ['ZZZ'])


if _name_ == '_main_':
    unittest.main()