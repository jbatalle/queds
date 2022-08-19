import collections
import logging
from wallet_processor.entities.broker import BrokerProcessor
from wallet_processor.entities.crypto import CryptoProcessor
from wallet_processor.utils import BalanceQueue, Transaction

logger = logging.getLogger("wallet_processor")


class WalletProcessor:
    def __init__(self):
        self.processor = None

    @staticmethod
    def _validate_data(data):
        if 'user_id' not in data:
            return False
        if 'mode' not in data:
            return False

        return True

    def process(self, data):
        if not self._validate_data(data):
            logger.error("Received invalid data")
            return

        mode = data.get('mode')
        user_id = data.get('user_id')

        logger.info(f"Received action for user {user_id} and mode {mode}")
        if mode == 'crypto':
            self.processor = CryptoProcessor()
        elif mode == 'stock':
            self.processor = BrokerProcessor()
        else:
            logger.warning(f"Unhandled mode: {mode}")
            return

        logger.info("Processor initialized. Retrieving orders")
        accounts = self.processor.get_accounts(user_id)
        orders = self.processor.get_orders(accounts)
        transactions = self.processor.get_transactions(accounts)
        orders = sorted(orders + transactions, key=lambda x: x.value_date)

        orders = self.processor.preprocess(orders)

        logger.info(f"Found: {len(orders)} orders and {len(transactions)} transactions. Starting wallet calculation..")
        tracked_orders = []
        queue = BalanceQueue()

        for order in orders:
            sell_order = self.processor.trade(queue, order)
            if sell_order:
                tracked_orders.append(sell_order)

        try:
            self.validate_wallet(queue, orders)
        except Exception as e:
            logger.error(f"Error validating wallet calculations: {e}")
            logger.exception(e)

        logger.info("Calculation done. Generating wallet...")
        self.processor.create_closed_orders(orders, tracked_orders)
        self.processor.calc_wallet(user_id, orders, queue, tracked_orders)

        logger.info("Done")

    def validate_wallet(self, queue, orders):
        """
        We can try to check that the Wallet (Current balance) calculated is equal to the sum of all operations
        """

        wallet_balance = self.calc_balance_with_queue(queue)
        wallet_balance = {k: round(v, 8) for k, v in wallet_balance.items() if v > 0.000000001}
        wallet_balance = collections.OrderedDict(sorted(wallet_balance.items()))

        order_balance = self.processor.calc_balance_with_orders(orders)
        order_balance = {k: round(v, 8) for k, v in order_balance.items() if v > 0.000000001}
        order_balance = collections.OrderedDict(sorted(order_balance.items()))

        # check diff
        diffs = set(wallet_balance.items()) ^ set(order_balance.items())
        diffs_dict = {}
        for d in diffs:
            if d[0] not in diffs_dict:
                diffs_dict[d[0]] = []
            diffs_dict[d[0]].append(d[1])

        if diffs_dict:
            logger.warning(f"Found following diffs between orders and wallet calculation: {diffs_dict}")

    @staticmethod
    def calc_balance_with_queue(queue):
        logger.info("Calc balance using queue")
        balance = {}
        for k, v in queue.queues.items():
            if not isinstance(k, str):
                k = k.ticker

            if k not in balance:
                balance[k] = 0
            for q in v:
                balance[k] += q.amount

        return balance
