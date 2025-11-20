import logging
from models.system import Account, Entity
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
        required_fields = ['account_id', 'entity_name', 'data']
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        return True

    def process(self, data):
        if not self._validate_data(data):
            logger.error("Invalid request data")
            return

        logger.info(f"Starting CSV processing for {data['entity_name']}...")
        account_id = data.get('account_id')
        entity_type = data.get('entity_type')
        broker_name = data.get('entity_name').lower()
        content = data.get('data')

        csv_handler = SUPPORTED_CSV_READER.get(broker_name)
        if not csv_handler:
            return

        account = Account.get_by_account_id(account_id)
        logger.info("Processing CSV for account {account.id}...")

        orders, transactions = csv_handler.process_csv(content, account)
        logger.info(f"Found {len(orders)} orders in {broker_name}")

        if entity_type == Entity.Type.EXCHANGE:
            reader = ExchangeReader()
            orders = reader._join_orders(orders, transactions)
            reader.parse_read(account_id, [], orders)
        else:
            broker_reader = BrokerReader()
            broker_reader.parse_read(account_id, account, orders)

        return
