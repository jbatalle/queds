from datetime import datetime
from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.crypto import ExchangeOrder, ExchangeTransaction, ExchangeWallet, ExchangeClosedOrder, ExchangeProxyOrder
from wallet_processor.utils import BalanceQueue, Transaction
from wallet_processor.utils.crypto_prices import get_price


class CryptoProcessor(AbstractEntity):

    def __init__(self):
        super(CryptoProcessor, self).__init__()

    def preprocess(self):
        pass
        # self.check_transactions(orders)
        #
        # orders_orders = [o for o in orders if not isinstance(o, TransactionOrder)]
        # iota_orders = [o for o in orders_orders if 'IOT' in o.pair]
        # iota_trans = [o for o in orders if isinstance(o, TransactionOrder) and 'IOT' in o.currency]
        # w = 0
        # for o in sorted(iota_orders + iota_trans, key=lambda x: x['time']):
        #     time = datetime.fromtimestamp(o.time)
        #     if isinstance(o, TransactionOrder):
        #         vol = o.amount
        #         if o.type == OrderType.WITHDRAWAL:
        #             vol = -o.amount
        #     if isinstance(o, Order):
        #         vol = o.vol
        #         if o.type == OrderType.SELL:
        #             vol = -o.vol
        #     print(f"{time},{o.type},{vol},{o.exchange}")

    @staticmethod
    def clean(transactions):
        ExchangeProxyOrder.query.filter(ExchangeProxyOrder.transaction_id.in_([t.id for t in transactions])).delete()
        ExchangeClosedOrder.query.filter(ExchangeClosedOrder.sell_transaction_id.in_([t.id for t in transactions])).delete()

    @staticmethod
    def get_orders(user_id):
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.EXCHANGE)).all()
        transactions = ExchangeOrder.query.filter(
            ExchangeOrder.account_id.in_([a.id for a in accounts])).order_by(
            ExchangeOrder.value_date.asc(), ExchangeOrder.type.asc()).all()
        return transactions

    def trade(self, queue, order):
        value_date = order.value_date
        if isinstance(order, ExchangeTransaction):
            order.currency = order.currency.upper()
            order.currency = order.currency.replace("IOT", "IOTA").replace("IOTAA", "IOTA").replace("XRB", "NANO")
            if order.type == ExchangeTransaction.Type.DEPOSIT and order.currency == 'EUR':
                print(f"{value_date} - Deposit {order.amount}{order.currency}. Target: {order.exchange} "
                      f"Current: {queue.current_amount(order.currency)}")
                queue.deposit(order)
            elif order.type == ExchangeTransaction.Type.WITHDRAWAL and order.currency == 'EUR':
                print(f"{value_date} - Withdrawal {order.amount}{order.currency}. Source: {order.exchange} "
                      f"Current: {queue.current_amount(order.currency)}")
                queue.withdrawal(order)
            return

        # order.vol = round(order.amount, 4)
        order.pair = order.pair.upper()
        order.pair = order.pair.replace("IOT", "IOTA").replace("IOTAA", "IOTA").replace("XRB", "NANO")
        order.cost = order.amount * order.price
        # order.amount = float("{:0.4f}".format(order.amount))
        # order.price = float("{:0.8f}".format(order.price))

        sell_info = None
        source = order.pair.split("/")[0]
        target = order.pair.split("/")[1]

        if order.type == ExchangeOrder.Type.BUY:
            self._logger.info(f"{value_date} - Buy {source} from {target}. Amount: {order.amount}{source}. "
                              f"Price: {order.price} Cost: {order.cost}{target}. {order.account_id} "
                              f"Current EUR: {queue.current_amount('EUR')}")
        else:
            self._logger.info(f"{value_date} - Sell {source} to {target}. Selling: {order.amount}{source}. "
                              f"Price: {order.price} Won: {order.cost}{target}. {order.account_id}. "
                              f"Current amount: {queue.current_amount(source)} "
                              f"Current EUR: {queue.current_amount('EUR')}")

        if order.type == ExchangeOrder.Type.BUY and target == 'EUR':
            buy_transaction = Transaction(order.id, Transaction.Type.BUY, order.value_date, source, order.amount, order.price)
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(order.id, Transaction.Type.SELL, order.value_date, target, order.cost, order.price,
                                           order.fee)
            queue.buy(buy_transaction)
            sell_info = queue.sell(sell_transaction)
            return None

        sell_transaction = None
        buy_transaction = None
        if order.type == ExchangeOrder.Type.BUY:
            # target can be other coins
            target_price = get_price(target, "EUR", order.value_date)
            source_price = get_price(source, "EUR", order.value_date)
            sell_transaction = Transaction(order.id, Transaction.Type.SELL, order.value_date, target, order.cost,
                                           target_price, order.fee)
            buy_transaction = Transaction(order.id, Transaction.Type.BUY, order.value_date, source, order.amount, source_price)
        elif order.type == ExchangeOrder.Type.SELL and target == 'EUR':
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(order.id, Transaction.Type.SELL, order.value_date, source, order.amount, order.price)
            buy_transaction = Transaction(order.id, Transaction.Type.BUY, order.value_date, target, order.cost, order.price,
                                          order.fee)
        elif order.type == ExchangeOrder.Type.SELL:
            target_price = get_price(target, "EUR", order.value_date)
            source_price = get_price(source, "EUR", order.value_date)
            sell_transaction = Transaction(order.id, Transaction.Type.SELL, order.value_date, source, order.amount, source_price)
            buy_transaction = Transaction(order.id, Transaction.Type.BUY, order.value_date, target, order.cost, target_price,
                                          order.fee)
        else:
            self._logger.warning("HEEY, something happened here!")

        if not sell_transaction or not buy_transaction:
            self._logger.debug("Not sell and buy transactions!")
            return

        if order.type == ExchangeOrder.Type.SELL:
            sell_info = queue.sell(sell_transaction)
            queue.buy(buy_transaction)
        else:
            sell_info = queue.sell(sell_transaction)
            queue.buy(buy_transaction)

        if sell_info:
            return sell_info
        return None

    def calc_wallet(self, user_id, orders, queue, tracked_orders):
        self._logger.info("Cleaning closed orders")
        self.clean(orders)

        self._logger.info("Generating new crypto wallet")
        order_benefits = []
        benefits_year = {}
        for sell_order in tracked_orders:
            closed_order = ExchangeClosedOrder(sell_transaction_id=sell_order.sell_trade.transaction_id)
            closed_order.save()

            for buy_order in sell_order.buy_items:
                if not buy_order.trade:
                    self._logger.warning("Some strange case!")
                    continue

                if sell_order.amount <= buy_order.amount:
                    partial_fee = buy_order.fee / (buy_order.trade.amount / sell_order.amount)
                else:
                    try:
                        partial_fee = buy_order.fee / (sell_order.amount / buy_order.amount)
                    except:
                        print("Amount is 0!")
                        partial_fee = 0
                ExchangeProxyOrder(
                    closed_order_id=closed_order.id,
                    transaction_id=buy_order.trade.transaction_id,
                    shares=buy_order.amount,
                    partial_fee=partial_fee
                ).save()

            close = {
                "amount": sell_order.amount,
                "price": sell_order.sell_trade.price,
                "time": sell_order.sell_trade.time,
            }

        # calculating wallet
        to_insert = []
        for ticker, partial_orders in queue.queues.items():
            self._logger.debug(f"Start processing ticker {ticker}")
            shares = 0
            avg_price = 0
            fees = 0
            total_cost = 0
            open_orders = []

            for order in partial_orders:
                if shares == 0:
                    shares += order.amount
                    avg_price = order.price
                    total_cost = shares * avg_price
                    fees = order.fee
                    continue

                avg_price = (shares * avg_price + order.amount * order.price) / (shares + order.amount)
                # TODO: calc average fee?
                shares += order.amount
                total_cost += order.price * order.amount  # * partial_order.trade.currency_rate
                fees += order.fee

            # Calculate current benefits taking into account sells
            current_benefits = 0
            current_benefits_eur = 0
            total_sell = 0
            for order in [w for w in tracked_orders if w.sell_trade.ticker == ticker]:
                current_benefits += order.benefits
                current_benefits_eur += order.benefits_in_eur
                total_sell += order.sell_trade.price * order.amount * order.sell_trade.currency_rate
                fees += order.sell_trade.fees

            # current_benefits += 0  # fees??

            if shares == 0:
                self._logger.info(f"Shares is 0 for ticker {ticker}!")
                continue
            break_even = (total_cost - total_sell) / shares
            if not ticker:
                self._logger.info("Ticker not found!")
            w = ExchangeWallet(
                currency=ticker,
                user_id=user_id,
                amount=shares,
                price=avg_price,  # in $
                cost=total_cost,  # in base currency without fees
                benefits=current_benefits_eur,  # in €, in front we should sum fees
                break_even=break_even if break_even > 0 else 0,  # in base_currency
                fees=fees)

            to_insert.append(w)

        ExchangeWallet.query.delete()
        ExchangeWallet.bulk_object(to_insert)
        self._logger.info("Wallet calculation done")

    @staticmethod
    def calc_balance_with_orders(orders):
        balance = {}
        for order in orders:
            if isinstance(order, ExchangeTransaction):
                if order.currency not in balance:
                    balance[order.currency] = 0

                if order.type == ExchangeTransaction.Type.DEPOSIT:
                    balance[order.currency] += order.amount
                else:
                    balance[order.currency] -= order.amount
                continue
            order.pair = order.pair.replace("XBT", "BTC").replace("IOT", "IOTA").replace("IOTAA", "IOTA")

            # logger.info(order.vol)
            source = order.pair.split("/")[0]
            target = order.pair.split("/")[1]

            # order.vol = float("{:0.8f}".format(order.amount))
            # order.cost = float("{:0.8f}".format(order.cost))

            if source not in balance:
                balance[source] = 0
            if target not in balance:
                balance[target] = 0
            if order.type == ExchangeOrder.Type.BUY:
                balance[source] += order.amount
                balance[target] -= order.cost
            else:
                balance[source] -= order.amount
                balance[target] += order.cost

        return balance

    def check_transactions(self, orders):
        transaction_orders = [o for o in orders if isinstance(o, ExchangeTransaction)]
        queue = {}
        pair_deposit_with = {}
        for order in transaction_orders:
            time = datetime.fromtimestamp(order.time)
            order.currency = order.currency.upper()
            if order.currency not in queue:
                queue[order.currency] = 0

            if order.type == ExchangeTransaction.Type.DEPOSIT:
                self._logger.info(f"{time} - Deposit {order.amount}{order.currency}. Target: {order.exchange}")
                queue[order.currency] += order.amount
                # queue.deposit(order)
            else:
                self._logger.info(f"{time} - Withdrawal {order.amount}{order.currency}. Source: {order.exchange}")
                queue[order.currency] -= order.amount
                # queue.withdrawal(order)

        self._logger.info("Done")
