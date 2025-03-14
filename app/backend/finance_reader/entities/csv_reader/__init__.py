from abc import ABC, abstractmethod
import logging


class CSVProcessor(ABC):

    def __init__(self):
        self.log = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def process_csv(self, csv_data):
        raise NotImplementedError

    def insert_db(self, orders, transactions):
        raise NotImplementedError


class BrokerCSVProcessor(CSVProcessor):

    def __init__(self):
        super(BrokerCSVProcessor, self).__init__()

    def insert_db(self, orders, transactions):
        from models.broker import StockTransaction
        StockTransaction.bulk_insert(orders)


class ExchangeCSVProcessor(CSVProcessor):

    def __init__(self):
        super(ExchangeCSVProcessor, self).__init__()

    def insert_db(self, orders, transactions):
        from models.crypto import ExchangeOrder, ExchangeTransaction
        ExchangeOrder.bulk_insert([o.to_dict() for o in orders])
        ExchangeTransaction.bulk_insert([o.to_dict() for o in transactions])


from finance_reader.entities.csv_reader.bitstamp import Bitstamp
from finance_reader.entities.csv_reader.bittrex import Bittrex
from finance_reader.entities.csv_reader.degiro import Degiro
from finance_reader.entities.csv_reader.kucoin import Kucoin
from finance_reader.entities.csv_reader.coinbase import Coinbase


SUPPORTED_CSV_READER = {
    "bitstamp": Bitstamp(),
    "bittrex": Bittrex(),
    "degiro": Degiro(),
    "kucoin": Kucoin(),
    "coinbase": Coinbase()
}
