import logging
from models.system import Account
from models.crypto import ExchangeBalance, CryptoEvent
from finance_reader.entities.exchanges import SUPPORTED_EXCHANGES

logger = logging.getLogger("exchange_read")


class ExchangeReader:
    def __init__(self):
        pass

    @staticmethod
    def _validate_data(data):
        logger.info("Validating data...")
        if 'account_id' not in data:
            return False
        if 'entity_name' not in data:
            return False
        return True

    def process(self, data:dict):
        if not self._validate_data(data):
            return

        account_id = data.get('account_id')
        exchange_key = data.get('entity_name').lower()

        exchange = SUPPORTED_EXCHANGES.get(exchange_key)
        if not exchange:
            logger.warning(f"Exchange '{exchange_key}' is not supported.")
            return

        logger.info(f"Logging into exchange: {exchange_key}")
        exchange.login(data)

        logger.info("Fetching exchange data...")
        balances = exchange.get_balances()
        orders = exchange.get_orders()
        # transactions = exchange.get_transactions()
        logger.info(f"Found {len(orders)} orders in {exchange_key}")

        self.parse_read(account_id, balances, orders)
        logger.info("Read done!")

    @staticmethod
    def _get_balance(balances):
        base_currency = 'eur'
        item = next((b for b in balances if b.currency.lower() == base_currency), None)
        if not item:
            item = next((b for b in balances if b.currency.lower() == 'usd'), None)
        if not item:
            item = next((b for b in balances if b.currency.lower() == 'btc'), None)
        return item

    @staticmethod
    def _update_account(account_id, base_balance):
        account = Account.get_by_account_id(account_id)
        account.balance = base_balance.balance
        account.currency = base_balance.currency
        account.save()
        return account

    def parse_read(self, account_id, balances, orders):
        logger.info(f"Updating account: {account_id}")

        # get balance and base currency
        base_balance = self._get_balance(balances)
        if base_balance:
            self._update_account(account_id, base_balance)

        logger.info(f"Inserting {len(balances)} balances into the database")
        ExchangeBalance.bulk_insert([balance.to_dict() for balance in balances])

        logger.info(f"Inserting {len(orders)} orders into the database")
        CryptoEvent.bulk_insert([order.to_dict() for order in orders])
