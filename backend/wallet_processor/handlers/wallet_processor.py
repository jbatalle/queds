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
        orders = self.processor.get_orders(user_id)

        logger.info(f"Found {len(orders)} orders. Start calculation")
        tracked_orders = []
        queue = BalanceQueue()

        for order in orders:
            sell_order = self.processor.trade(queue, order)
            if sell_order:
                tracked_orders.append(sell_order)

        logger.info("Calculation done. Generating wallet...")
        self.processor.calc_wallet(user_id, orders, queue, tracked_orders)

        try:
            self.validate_wallet(queue, orders)
        except Exception as e:
            logger.error(f"Error validating wallet calculations: {e}")
        logger.info("Done")

    def validate_wallet(self, queue, orders):
        """
        We can try to check that the Wallet (Current balance) calculated is equal from whem we sum the operations
        """

        wallet_balance = self.calc_balance_with_queue(queue)
        wallet_balance = {k: v for k, v in wallet_balance.items() if v != 0.0}

        order_balance = self.processor.calc_balance_with_orders(orders)
        order_balance = {k: v for k, v in order_balance.items() if v != 0.0}

        wallet_balance = collections.OrderedDict(sorted(wallet_balance.items()))
        order_balance = collections.OrderedDict(sorted(order_balance.items()))

        # check diff
        diffs = set(wallet_balance.items()) ^ set(order_balance.items())
        logger.info(f"Diffs: {diffs}")

    @staticmethod
    def calc_balance_with_queue(queue):
        logger.info("Calc balance using queue")
        balance = {}
        for k, v in queue.queues.items():
            balance[k] = 0
            for q in v:
                balance[k] += q.amount

        return balance
