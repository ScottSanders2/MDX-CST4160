# test.py

import unittest
import json
from unittest.mock import patch, MagicMock
import app

# Use an in‑memory database for all tests
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
        # grab Scott's user_id from the in‑memory DB
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
        # BTC assertions
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
        self.login()
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'AAAUSDT', resp.data)

    @patch('app.get_crypto_prices', return_value={'SOLUSDT': {'price': '$2.00'}})
    def test_update_preferences_endpoint(self, mock_prices):
        self.login()
        resp = self.client.post('/update_preferences', json={'symbols': ['SOLUSDT']})
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

class TestCryptoNewsAPIs(unittest.TestCase):
    @patch('app.requests.get')
    def test_get_newsapi_articles_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "articles": [
                {
                    "title": "Crypto Boom",
                    "url": "https://news.example.com/crypto-boom",
                    "description": "Prices are soaring",
                    "publishedAt": "2025-04-18T10:00:00Z"
                }
            ]
        }
        mock_get.return_value = mock_resp

        articles = app.get_newsapi_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["publishedAt"], "2025-04-18")

    @patch('app.requests.get')
    def test_get_guardian_articles_success(self, mock_get):
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "response": {
                "results": [
                    {
                        "webTitle": "Ethereum Surges",
                        "webUrl": "https://guardian.example.com/eth-surges",
                        "webPublicationDate": "2025-04-17T15:30:00Z",
                        "fields": {"trailText": "ETH price rally"}
                    }
                ]
            }
        }
        mock_get.return_value = mock_resp

        articles = app.get_guardian_articles()
        self.assertEqual(len(articles), 1)
        self.assertEqual(articles[0]["publishedAt"], "2025-04-17")

    @patch('app.get_newsapi_articles', return_value=[{"title": "A"}])
    @patch('app.get_guardian_articles', return_value=[{"title": "B"}])
    def test_get_crypto_news_combines(self, mock_guardian, mock_newsapi):
        news = app.get_crypto_news()
        self.assertEqual(news, [{"title": "A"}] + [{"title": "B"}])

class TestNewsEndpoint(unittest.TestCase):
    def setUp(self):
        app.app.testing = True
        self.client = app.app.test_client()

    @patch('app.get_crypto_news', return_value=[{"title": "Test News"}])
    def test_api_news_route(self, mock_news):
        resp = self.client.get('/api/news')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertEqual(data, [{"title": "Test News"}])

if __name__ == '__main__':
    unittest.main()