import logging
from models.system import Account
from models.broker import Ticker, StockTransaction
from finance_reader.entities.csv_reader import SUPPORTED_CSV_READER
from finance_reader.handlers.broker_read import BrokerReader
from finance_reader.handlers.exchange_read import ExchangeReader

logger = logging.getLogger("csv_read")


class CSVReader:
    def __init__(self):
        pass

    @staticmethod
    def _validate_data(data):
        logger.info("Validating data...")
        return True

    def process(self, data):
        if not self._validate_data(data):
            logger.error("Invalid request data")
            return

        account_id = data.get('account_id')
        entity_type = data.get('entity_type')
        broker_name = data.get('entity_name').lower()
        content = data.get('data')

        csv_handler = SUPPORTED_CSV_READER.get(broker_name)
        if not csv_handler:
            return

        # account = Account.query.filter(Account.id==account_id).one()
        account = Account.get_by_account_id(account_id)
        logger.info("Processing CSV...")

        orders, transactions = csv_handler.process_csv(content, account)
        logger.info(f"Found {len(orders)} orders in {broker_name}")

        # TODO: define here the handler reader
        if entity_type == 'exchange':
            reader = ExchangeReader()
            reader.parse_read(account_id, [], orders, transactions)
        else:
            broker_reader = BrokerReader()
            broker_reader.parse_read(account_id, account, orders)
        return

        ExchangeReader()._parse_read(account_id, 0, orders, transactions)
        from models.crypto import ExchangeOrder, ExchangeTransaction
        ExchangeOrder.bulk_insert([o.to_dict() for o in orders])
        ExchangeTransaction.bulk_insert([o.to_dict() for o in transactions])
        logger.info("Read done!")
