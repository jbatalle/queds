from collections import deque, defaultdict
from functools import reduce
import logging

logger = logging.getLogger("utils.process")


class Transaction:
    """
    Generic transaction used by Stock and Crypto
    """
    class Type:
        BUY = 0
        SELL = 1

    def __init__(self, type, order, ticker, amount, price, fees=None):
        self.order_type = order.__name__
        self.transaction_id = order.id
        self.type = type
        self.time = order.value_date
        self.ticker = ticker
        self.amount = amount
        self.price = price
        self.fees = round(fees, 4) if fees else 0.0
        self.currency_rate = round(order.currency_rate, 4) if hasattr(order, 'currency_rate') else 1

    @property
    def cost(self):
        return round(self.amount * self.price, 4)

    @property
    def cost_base_currency(self):
        return round(self.amount * self.price * self.currency_rate - self.fees, 4)

    def __str__(self):
        return f"Ticker: {self.ticker}-{self.amount}@{self.price}-Fees:{self.fees}"


class PartialOrder:
    """
    Represents a percentage of an amount bought in the past, and the corresponding trade.
    """

    def __init__(self, amount, order):
        """
        :param order: corresponding trade or None if unaccounted
        """
        self.amount = amount
        self.trade = order

    @property
    def fee(self):
        if self.trade:
            return self.trade.fees
        return 0

    @property
    def price(self):
        if self.trade is None:
            return 0

        return self.trade.price

    @property
    def cost(self):
        """
        The cost of the item
        """

        if self.trade is None:
            return 0

        return self.trade.price * self.amount# + self.trade.fees


class SellInfo:
    """
    Information about a sell action, such as cost / proceeds, profit / loss, etc.
    """

    def __init__(self, sell_trade, buy_items):
        self.sell_trade = sell_trade  # the trade representing the sale
        if not buy_items:
            logger.debug("No buy items found!")
        for b in buy_items:
            if not isinstance(b, PartialOrder):
                logger.error("No PartialOrder found!")
        self.buy_items = buy_items  # list of buys from the past associated with the sale

    @property
    def amount(self):
        """
        The amount sold (in original currency).
        """
        amount = 0
        for buy_item in self.buy_items:
            amount += buy_item.amount
        return amount

    @property
    def cost_sell(self):
        """
        Cost when selling (in tax currency).
        """
        # take into account that fees can be in other currency!
        return self.sell_trade.amount * self.sell_trade.price - self.sell_trade.fees

    @property
    def cost_sell_eur(self):
        """
        Cost when selling (in tax currency).
        """
        currency_rate = 1
        if self.sell_trade.currency_rate is not None:
            currency_rate = self.sell_trade.currency_rate
        return self.sell_trade.amount * self.sell_trade.price * currency_rate + self.sell_trade.fees

    @property
    def cost_buy(self):
        """
        Cost when buying (in tax currency).
        """

        return reduce(lambda a, b: a + b.cost, self.buy_items, 0.0)  # summarize cost of all buy items

    @property
    def cost_buy_in_eur(self):
        """
        Cost when buying (in tax currency).
        Summarize cost of all buy items
        """
        # TODO: fees should be splited between the buys
        return reduce(lambda a, b: a + b.cost * b.trade.currency_rate - b.trade.fees if hasattr(b.trade, 'currency_rate') else 1, self.buy_items, 0.0)

    @property
    def benefits(self):
        return self.cost_sell - self.cost_buy

    @property
    def fees(self):
        return self.sell_trade.fees

    @property
    def benefits_in_eur(self):
        # if self.trade is None or self.open_order is None:
        #     return 0
        #
        # if self.sell_trade.currency_rate:
        #     return self.cost_sell - self.cost_buy

        # return self.cost_sell * self.sell_trade.currency_rate - self.cost_buy * self.sell_trade.currency_rate
        if self.sell_trade.currency_rate is None:
            currency_rate = 0
        else:
            currency_rate = self.sell_trade.currency_rate
        return self.cost_sell_eur - self.cost_buy_in_eur


class BalanceQueue:

    def __init__(self):
        self.queues = defaultdict(lambda: deque())
        self.withdrawals = defaultdict()
        self.reverse_splits = defaultdict()

    def current_amount(self, ticker):
        return round(sum([o.amount for o in self.queues[ticker]]), 8)

    @staticmethod
    def _is_empty(queue):
        return len(queue) == 0

    @staticmethod
    def _pop(queue):
        item = queue.popleft()
        return item

    @staticmethod
    def _put_back(queue, item):
        queue.appendleft(item)

    @staticmethod
    def _put(queue, item):
        queue.append(item)

    def deposit(self, order):
        self._put(self.queues[order.currency], PartialOrder(order.amount, None))
        return

        if order.currency not in self.withdrawals:
            self._put(self.queues[order.currency], PartialOrder(order.amount, None))
            return

        if order.currency == 'EUR':
            self._put(self.queues[order.currency], PartialOrder(order.amount, None))
            return

        try:
            wth_order = next((o for o in self.withdrawals[order.currency] if (o.amount - o.fee) == order.amount or o.amount == order.amount), None)
        except:
            return
        if len(self.withdrawals[order.currency]) == 1:
            logger.info("Assign withdrawal to diposit?")
        if not wth_order:
            logger.info(f"{order.currency} - Unable to match withdrawal order with deposit order. Deposit amount: {order.amount}")
            for o in self.withdrawals[order.currency]:
                logger.info(f"Withdrawal amount: {o.amount} Fee: {o.fee}")
            self._put(self.queues[order.currency], PartialOrder(order.amount, None))
            return
        # remove from dict
        self._put(self.queues[order.currency], PartialOrder(order.amount, None))
        # self._put(self.queues[order.currency], PartialOrder(wth_order.amount, wth_order))

    def withdrawal(self, order):
        queue = self.queues[order.currency]
        remaining_sell_amount = order.amount
        if order.currency not in self.withdrawals:
            self.withdrawals[order.currency] = []
        # self.withdrawals[order.currency].append(order)
        # return

        while remaining_sell_amount > 0:
            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                # items_bought.append(PartialOrder(remaining_sell_amount, None))
                logger.warning(f"ALERT - NO BOUGHT ITEM LEFT for withdrawal! Pair: {order.currency}. Current amount is {self.current_amount(order.currency)}")
                break

            item = self._pop(queue)
            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - (order.fee if order.fee else 0)))
                self._put_back(queue, item)
                # self.withdrawals[order.currency].append(item)
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                # remaining_sell_amount -= item.amount
                remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
            else:
                logger.error("Unhandled condition. Please check!")

    def buy(self, order):
        if order.order_type == 'StockTransactionDTO':
            amount = order.amount
        else:
            amount = order.amount - order.fees
        self._put(self.queues[order.ticker], PartialOrder(amount, order))

    def sell(self, order):
        remaining_sell_amount = order.amount
        items_bought = []
        queue = self.queues[order.ticker]
        fees = order.fees if order.order_type != 'StockTransactionDTO' else 0

        while remaining_sell_amount > 0:

            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                items_bought.append(PartialOrder(remaining_sell_amount, None))
                logger.warning(f"ALERT - NO BOUGHT ITEM LEFT!! Pair: {order.ticker} Current amount is {self.current_amount(order.ticker)}")
                break

            item = self._pop(queue)
            if item.trade and item.trade.ticker != order.ticker:
                logger.warning("Different items: {} vs {}".format(item.trade.ticker, order.ticker))

            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                items_bought.append(PartialOrder(remaining_sell_amount, item.trade))
                # item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - order.fee))
                item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - fees))
                self._put_back(queue, item)
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                # remaining_sell_amount -= item.amount
                remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
            else:
                logger.error("Unhandled condition. Please check!")

        return SellInfo(order, items_bought)

    def apply_reverse(self, order):
        items_bought = []
        queue = self.queues[order.ticker]

        if order.type == Transaction.Type.SELL:
            # we update the new order with the previous data
            item = self._pop(queue)
            items_bought.append(item)
            self.reverse_splits[order.ticker] = item.trade
        else:
            amount = order.amount
            original_order = self.reverse_splits.pop(order.ticker)
            order.fees = original_order.fees
            order.currency_rate = original_order.currency_rate

            # TODO: update that order with old fee and currency_rate
            self._put(self.queues[order.ticker], PartialOrder(amount, order))
