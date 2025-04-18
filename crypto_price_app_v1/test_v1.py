import unittest
import json
from unittest.mock import patch, MagicMock
from app import app, get_crypto_prices
#Updating
class TestGetCryptoPrices(unittest.TestCase):
    @patch('app.Spot')
    def test_get_crypto_prices_success(self, mock_spot_cls):
        # Mock Spot client so all calls return fixed values
        mock_client = MagicMock()
        mock_client.ticker_price.return_value = {'price': '100.0'}
        mock_client.ticker_24hr.return_value = {
            'priceChangePercent': '5.0',
            'prevClosePrice': '95.0',
            'volume': '1234.56'
        }
        mock_spot_cls.return_value = mock_client

        result = get_crypto_prices()
        # Should return a dict with ticker_text and timestamp
        self.assertIn('ticker_text', result)
        self.assertIn('timestamp', result)
        # Check that ticker_text contains at least one of our mock symbols
        self.assertIn('BTC/USDT', result['ticker_text'])
        # And our mocked price formatting
        self.assertIn('$100.00', result['ticker_text'])

    @patch('app.Spot', side_effect=Exception('API error'))
    def test_get_crypto_prices_failure(self, mock_spot_cls):
        result = get_crypto_prices()
        # On exception, get_crypto_prices should return {'error': ...}
        self.assertIn('error', result)
        self.assertEqual(result['error'], 'API error')


class TestFlaskRoutes(unittest.TestCase):
    def setUp(self):
        app.testing = True
        self.client = app.test_client()

    @patch('app.get_crypto_prices')
    def test_index_route(self, mock_get_prices):
        # Simulate get_crypto_prices returning simple span
        mock_get_prices.return_value = {
            'ticker_text': '<span>TESTCOIN/USDT: $123.45</span>'
        }
        resp = self.client.get('/')
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b'TESTCOIN/USDT: $123.45', resp.data)

    @patch('app.get_crypto_prices')
    def test_api_price_route(self, mock_get_prices):
        mock_get_prices.return_value = {
            'ticker_text': '<span>FOO/USDT: $1.00</span>',
            'timestamp': '2025-04-18 12:00:00'
        }
        resp = self.client.get('/api/price')
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn('ticker_text', data)
        self.assertIn('timestamp', data)
        self.assertEqual(data['ticker_text'], '<span>FOO/USDT: $1.00</span>')
        self.assertEqual(data['timestamp'], '2025-04-18 12:00:00')


if __name__ == '__main__':
    unittest.main()