import logging
from models.system import Account
from models.crypto import ExchangeWallet, ExchangeOrder, ExchangeTransaction, ExchangeBalance
from finance_reader.entities.exchanges import SUPPORTED_EXCHANGES

logger = logging.getLogger("broker_read")


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

    def process(self, data):
        if not self._validate_data(data):
            return

        account_id = data.get('account_id')
        exchange_name = data.get('entity_name').lower()

        exchange = SUPPORTED_EXCHANGES.get(exchange_name)
        if not exchange:
            return

        logger.info("Login...")
        exchange.login(data)

        logger.info("Reading transactions...")
        balances = exchange.get_balances()
        orders = exchange.get_orders()
        transactions = exchange.get_transactions()
        logger.info(f"Found {len(orders)} orders and {len(transactions)} transactions in {exchange_name}")

        self._parse_read(account_id, balances, orders, transactions)
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

    def _parse_read(self, account_id, balances, orders, transactions):
        logger.info("Parsing read")

        # get balance and base currency
        base_balance = self._get_balance(balances)
        if not base_balance:
            logger.error("Check here, base balance is not EUR/USD")
            return

        logger.info(f"Updating account: {account_id}")
        self._update_account(account_id, base_balance)

        logger.info(f"Processing {len(orders)} balances")
        ExchangeBalance.bulk_insert([o.to_dict() for o in balances])

        logger.info(f"Processing {len(orders)} orders")
        ExchangeOrder.bulk_insert([o.to_dict() for o in orders])

        logger.info(f"Processing {len(transactions)} orders")
        ExchangeTransaction.bulk_insert([o.to_dict() for o in transactions])
