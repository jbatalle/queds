import unittest
from mock import patch, create_autospec
from loader import load_models
load_models()
from wallet_processor.handlers.wallet_processor import WalletProcessor
from models.broker import StockTransaction, ProxyOrder

from finance_reader.handlers.exchange_read import ExchangeReader

class BaseTestClass(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass


class ReaderTestCase(BaseTestClass):

    # @patch('models.system.User.check_password')
    # @patch('wallet_processor.entities.broker.BrokerProcessor.get_orders')
    def test_read(self):

        reader = ExchangeReader()
        d = {
            "entity_name": "bittrex",
            "account_id": 2,
            "api_key": "",
            "api_secret": ""
        }
        d2 = {
            "entity_name": "binance",
            "account_id": 2,
            "api_key": "",
            "api_secret": ""
        }
        d2 = {
            "entity_name": "kraken",
            "account_id": 2,
            "api_key": "",
            "api_secret": ""
        }
        print("Start")
        reader.process(d)
        print("Done")
