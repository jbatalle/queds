from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.crypto import ExchangeOrder, ExchangeTransaction, ExchangeWallet, ExchangeClosedOrder, ExchangeProxyOrder, \
    ExchangeOpenOrder
from wallet_processor.utils import BalanceQueue, Transaction
from wallet_processor.utils.crypto_prices import get_price, get_prices
from sqlalchemy.orm import joinedload


class CryptoProcessor(AbstractEntity):

    def __init__(self):
        super(CryptoProcessor, self).__init__()

    @staticmethod
    def preprocess(orders):
        for order in orders:
            if order.__name__ == 'ExchangeTransactionDTO':
                order.currency = order.currency.upper().replace("IOT", "IOTA").replace("IOTAA", "IOTA").\
                    replace("XRB", "NANO").replace("XBT", "BTC")
            else:
                order.pair = order.pair.upper().replace("IOT", "IOTA").replace("IOTAA", "IOTA").\
                    replace("XRB", "NANO").replace("XBT", "BTC")
        return orders

    @staticmethod
    def clean(orders):
        # Remove all closed orders and proxy orders
        ids = [o.id for o in orders]
        ExchangeProxyOrder.query.filter(ExchangeProxyOrder.order_id.in_(ids)).delete()
        ExchangeClosedOrder.query.filter(ExchangeClosedOrder.sell_order_id.in_(ids)).delete()

    @staticmethod
    def get_accounts(user_id):
        return Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                              Account.entity.has(type=Entity.Type.EXCHANGE)).all()

    @staticmethod
    def get_orders(accounts):
        """
        Get all crypto orders of user user_id in ASC order
        """
        orders = ExchangeOrder.query\
            .options(joinedload(ExchangeOrder.account)) \
            .filter(ExchangeOrder.account_id.in_([a.id for a in accounts]))\
            .order_by(ExchangeOrder.value_date.asc(), ExchangeOrder.type.asc())\
            .all()
        return [o.dto for o in orders]

    @staticmethod
    def get_transactions(accounts):
        """
        Get all crypto transactions of user user_id in ASC order
        """
        transactions = ExchangeTransaction.query\
            .options(joinedload(ExchangeTransaction.account)) \
            .filter(ExchangeTransaction.account_id.in_([a.id for a in accounts]))\
            .order_by(ExchangeTransaction.value_date.asc(), ExchangeTransaction.type.asc())\
            .all()
        return [o.dto for o in transactions]

    def trade(self, queue, order):
        """
        This function calculates the trade operations. Creates the queue and returns the sell orders
        """
        if order.amount == 0:
            return None, None
        value_date = order.value_date
        if order.__name__ == 'ExchangeTransactionDTO':
            if not order.rx_address or (order.rx_address and 'MAINTENANCE' not in order.rx_address):
                self._logger.debug(
                    f"{value_date.strftime('%Y-%m-%d %H:%M:%S')} - {ExchangeTransaction.get_type(order.type)} - {order.amount}{order.currency} to/from {order.account.entity.name}. "
                    f"Current: {queue.current_amount(order.currency)}{order.currency}")

                if order.type == ExchangeTransaction.Type.DEPOSIT:# and order.currency == 'EUR':
                    queue.deposit(order)
                elif order.type == ExchangeTransaction.Type.WITHDRAWAL: # and order.currency == 'EUR':
                    queue.withdrawal(order)
                return None, None

        order.cost = round(order.amount * order.price, 8)
        source = order.pair.split("/")[0]
        target = order.pair.split("/")[1]

        if order.type == ExchangeOrder.Type.BUY:
            self._logger.debug(f"{value_date.strftime('%Y-%m-%d %H:%M:%S')} - Buy {order.amount}{source}@{order.price} from {target}. "
                               f"Cost: {order.cost}{target}. {order.account.entity.name}. "
                               f"Current EUR: {queue.current_amount('EUR')}")
        else:
            self._logger.debug(f"{value_date.strftime('%Y-%m-%d %H:%M:%S')} - Sell {order.amount}{source}@{order.price} to {target}. "
                               f"Won: {order.cost}{target}. {order.account.entity.name}. "
                               f"Current amount: {queue.current_amount(source)}{source}. "
                               f"Current EUR: {queue.current_amount('EUR')}")

        if order.type == ExchangeOrder.Type.BUY and target == 'EUR':
            buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, order.price)
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, order.price, order.fee)
            queue.buy(buy_transaction)
            queue.sell(sell_transaction)
            self._logger.debug(f"Current EUR: {queue.current_amount('EUR')}. Current {source}: {queue.current_amount(source)}")
            return None, None

        if order.type == ExchangeOrder.Type.BUY:
            # target can be other coins
            # target_price, source_price = get_prices([target, source], 'EUR', order.value_date)
            # target_price, source_price = get_prices([target, "EUR"], source, order.value_date)
            target_price = get_price(target, "EUR", order.value_date)
            # target_price2 = get_price(source, "EUR", order.value_date)
            source_price = order.price * target_price
            # print(f"Diff: {source_price} - {source_price2}")
            sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, target_price, order.fee)
            buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, source_price)
        elif order.type == ExchangeOrder.Type.SELL and target == 'EUR':
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(Transaction.Type.SELL, order, source, order.amount, order.price)
            buy_transaction = Transaction(Transaction.Type.BUY, order, target, order.cost, order.price, order.fee)
        elif order.type == ExchangeOrder.Type.SELL:
            # target_price, source_price = get_prices([target, "EUR"], source, order.value_date)
            target_price = get_price(target, "EUR", order.value_date)
            source_price = order.price * target_price
            sell_transaction = Transaction(Transaction.Type.SELL, order, source, order.amount, source_price)
            buy_transaction = Transaction(Transaction.Type.BUY, order, target, order.cost, target_price, order.fee)
        else:
            self._logger.debug("Not sell and buy transactions, something happened here!")
            return None, None

        sell_info = queue.sell(sell_transaction)
        queue.buy(buy_transaction)
        self._logger.debug(f"Current EUR: {queue.current_amount('EUR')}. Current {source}: {queue.current_amount(source)}. Current {target}: {queue.current_amount(target)}")

        if sell_info:
            return sell_info, None
        return None, None

    def create_closed_orders(self, orders, tracked_orders):
        """
        Insert closed orders to database
        """
        self._logger.debug("Cleaning closed/wallet/proxy orders")
        self.clean(orders)

        self._logger.debug("Generating new closed/wallet/proxy orders")
        closed_orders = []
        proxy_orders = []
        stable_currencies_orders = []
        for sell_order in tracked_orders:
            if sell_order.sell_trade.order_type != 'ExchangeOrderDTO':
                continue

            if sell_order.sell_trade.ticker in ['EUR', 'USD', 'USDT']:
                # process this later
                stable_currencies_orders.append(sell_order)
                continue

            closed_order = ExchangeClosedOrder(sell_order_id=sell_order.sell_trade.transaction_id)
            closed_orders.append(closed_order)

            for buy_order in sell_order.buy_items:
                if not buy_order.trade:
                    self._logger.warning(f"Sell order without buy! "
                                         f"{buy_order.amount}{sell_order.sell_trade.ticker} at {sell_order.sell_trade.time}")
                    continue

                if sell_order.amount <= buy_order.amount:
                    partial_fee = buy_order.fee / (buy_order.trade.amount / sell_order.amount)
                else:
                    try:
                        partial_fee = buy_order.fee / (sell_order.amount / buy_order.amount)
                    except:
                        self._logger.warning(f"Amount is 0! When checking order {buy_order.amount}{sell_order.sell_trade.ticker}")
                        partial_fee = 0

                proxy_order = ExchangeProxyOrder(
                    closed_order=closed_order,
                    order_id=buy_order.trade.transaction_id,
                    amount=buy_order.amount,
                    partial_fee=partial_fee
                )
                proxy_orders.append(proxy_order)

        # Save the objects in a single database query
        ExchangeClosedOrder.bulk_save_objects(closed_orders)
        for proxy_order in proxy_orders:
            proxy_order.closed_order_id = proxy_order.closed_order.id

        ExchangeProxyOrder.bulk_save_objects(proxy_orders)
        self._logger.debug("Closed and proxy orders inserted correctly!")

    def calc_wallet(self, user_id, orders, queue, tracked_orders):
        """
        Calculate current open orders
        """
        to_insert = []
        for ticker, partial_orders in queue.queues.items():
            amount = 0
            avg_price = 0
            fees = 0
            total_cost = 0
            open_orders = []

            for order in partial_orders:
                if not order.trade:
                    self._logger.error(f"Order {ticker} without trade!")
                    continue
                if amount == 0:
                    amount += order.amount
                    avg_price = order.price
                    total_cost = amount * avg_price
                    fees = order.fee
                    # TODO: its required to save an amount = 0?
                    open_orders.append(ExchangeOpenOrder(order_id=order.trade.transaction_id, amount=order.amount))
                    continue

                avg_price = (amount * avg_price + order.amount * order.price) / (amount + order.amount)
                # TODO: calc average fee?
                amount += order.amount
                total_cost += order.price * order.amount  # * partial_order.trade.currency_rate
                fees += order.fee
                open_orders.append(ExchangeOpenOrder(order_id=order.trade.transaction_id, amount=order.amount))

            if amount == 0:
                self._logger.info(f"Amount is 0 for ticker {ticker}!")
                continue

            # Calculate current benefits taking into account sells
            # current_benefits = 0
            current_benefits_eur = 0
            total_sell = 0
            for order in [w for w in tracked_orders if w.sell_trade.ticker == ticker]:
                # current_benefits += order.benefits
                current_benefits_eur += order.benefits_in_eur
                total_sell += order.sell_trade.price * order.amount * order.sell_trade.currency_rate
                fees += order.sell_trade.fees

            # current_benefits += 0  # fees??

            break_even = (total_cost - total_sell) / amount
            w = ExchangeWallet(
                currency=ticker,
                user_id=user_id,
                amount=amount,
                price=avg_price,  # in $
                cost=total_cost,  # in base currency without fees
                benefits=current_benefits_eur,  # in €, in front we should sum fees
                break_even=break_even if break_even > 0 else 0,  # in base_currency
                fees=fees)
            w.open_orders.extend(open_orders)
            to_insert.append(w)

        ExchangeOpenOrder.query.filter(ExchangeOpenOrder.order_id.in_([t.id for t in orders])).delete()

        ExchangeWallet.query.delete()
        ExchangeWallet.bulk_object(to_insert)
        self._logger.info("Wallet calculation done")

    @staticmethod
    def calc_balance_with_orders(orders):
        balance = {}
        for order in sorted(orders, key=lambda x: x.value_date):
            if order.__name__ == 'ExchangeTransactionDTO':
                if order.currency not in balance:
                    balance[order.currency] = 0

                if order.type == ExchangeTransaction.Type.DEPOSIT:
                    balance[order.currency] += order.amount
                else:
                    balance[order.currency] -= order.amount
                continue

            source = order.pair.split("/")[0]
            target = order.pair.split("/")[1]
            try:
                order.cost
            except:
                order.cost = round(order.amount * order.price, 8)

            if source not in balance:
                balance[source] = 0
            if target not in balance:
                balance[target] = 0

            if order.type == ExchangeOrder.Type.BUY:
                balance[source] += order.amount
                balance[target] -= order.cost + order.fee
            else:
                balance[source] -= order.amount
                balance[target] += order.cost - order.fee

        return balance

    def check_benefits(self, queue, orders, tracked_orders):
        pass

    def process_pending_transactions(self, queue, orders, tracked_orders):
        print("Check pending withdrawals")

        withdrawals = queue.withdrawals
        for currency, withdrawal in withdrawals.items():
            for wth in withdrawal:
                if wth.status == 'DEPOSITED':
                    self._logger.info(f"Deposit: {wth.amount}{wth.currency} at {wth.value_date} to {wth.account.entity.name}. Fees: {wth.fee}")
                    continue

                self._logger.info(f"Pending withdrawal: {wth.amount}{wth.currency} at {wth.value_date} from {wth.account.entity.name}")
                order = Transaction(Transaction.Type.SELL, wth, wth.currency, wth.amount, 0, wth.fee)
                sell_order = queue.withdrawal_old(order)
                tracked_orders.append(sell_order)
