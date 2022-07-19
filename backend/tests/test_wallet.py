import unittest
from mock import patch, create_autospec
from loader import load_models
load_models()
from wallet_processor.handlers.wallet_processor import WalletProcessor
from models.broker import StockTransaction, ProxyOrder


class BaseTestClass(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


class PostModelTestCase(BaseTestClass):

    # @patch('models.system.User.check_password')
    @patch('wallet_processor.entities.broker.BrokerProcessor.get_orders')
    def test_login(self, mock_orders):
        data = {
            "user_id": 1,
            "mode": "stock"
        }
        trans = StockTransaction(
            account_id=1,
            external_id=f"external_id",
            value_date=f"2021-01-01",
            name="TESLA",
            ticker_id=1,
            shares=10,
            type=StockTransaction.Type.BUY,
            currency="USD",
            price=500.2 + 1,
            fee=2,
            exchange_fee=1,
            currency_rate=1)
        mock_orders.return_value = [trans]
        w = WalletProcessor()
        w.process(data)

        # self.assertEqual(200, res.status_code)
        # self.assertIn('token', response)
