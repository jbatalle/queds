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
        REVERSE_SPLIT = 2

    def __init__(self, type, order, ticker, amount, price, fees=None, original_currency_rate=None):
        self.order_type = order.__name__
        self.transaction_id = order.id
        self.type = type
        self.value_date = order.value_date
        self.ticker = ticker
        self.amount = amount
        self.price = price
        self.fees = round(fees, 8) if fees else 0.0
        # self.currency_rate = round(order.currency_rate, 4) if hasattr(order, 'currency_rate') else 1
        self.currency_rate = order.currency_rate if hasattr(order, 'currency_rate') else 1
        self.original_currency_rate = original_currency_rate or self.currency_rate

    @property
    def cost(self):
        return round(self.amount * self.price, 4)

    @property
    def cost_base_currency(self):
        return round(self.amount * self.price * self.currency_rate - self.fees, 4)

    def __str__(self):
        return f"Ticker: {self.ticker}-{self.amount}@{self.price}-Fees:{self.fees}-{self.value_date}"

    def create_reverse_split(self, ratio):
        """
        Creates a new transaction representing the position after a reverse split
        """
        new_amount = self.amount / ratio
        new_price = self.price * ratio
        # Preserve the original currency rate
        return Transaction(
            self.Type.REVERSE_SPLIT,
            self,  # Pass self as order to maintain reference
            self.ticker,
            new_amount,
            new_price,
            self.fees,
            self.original_currency_rate  # Preserve original currency rate
        )


class PartialOrder:
    """
    Represents a percentage of an amount bought in the past, and the corresponding trade.
    """

    def __init__(self, amount, order, original_trade=None):
        """
        :param order: corresponding trade or None if unaccounted
        :param original_trade: reference to the original buy trade before splits
        """
        self.amount = amount
        self.trade = order
        self.original_trade = original_trade or order

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

        return self.trade.price * self.amount  # + self.trade.fees

    @property
    def original_currency_rate(self):
        """
        Returns the currency rate from the original trade
        """
        if self.original_trade:
            return self.original_trade.original_currency_rate
        return self.trade.original_currency_rate if self.trade else 1


class SellInfo:
    """
    Information about a sell action, such as cost / proceeds, profit / loss, etc.
    """

    def __init__(self, sell_trade, buy_items):
        self.sell_trade = sell_trade  # the trade representing the sale
        if not buy_items:
            # TODO: include info here
            logger.warning(f"No buy items found for {sell_trade.ticker}!")
        for b in buy_items:
            if not isinstance(b, PartialOrder):
                logger.error("No PartialOrder found!")
        self.buy_items = buy_items  # list of buys from the past associated with the sale

    def __str__(self):
        return f"Sell: {self.sell_trade.ticker} {self.amount}@{self.sell_trade.price} - {self.cost_sell} - {self.cost_buy}"

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
    def average_price(self):
        """
        The average price of the sold items
        """
        if self.amount == 0:
            return 0
        return self.cost_buy / self.amount

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
        Summarize cost of all buy items, including proportional fees for partial sells.
        """
        total_cost = 0.0
        for buy_item in self.buy_items:
            if buy_item.amount == 0:
                continue
            # Calculate the base cost
            item_cost = buy_item.cost * (
                buy_item.trade.currency_rate if hasattr(buy_item.trade, 'currency_rate') else 1)
            # item_cost2 = buy_item.cost * buy_item.original_currency_rate
            # print(f"Item cost diff: {item_cost} vs {item_cost2}. {buy_item.trade.currency_rate} vs {buy_item.original_currency_rate}")

            # Calculate proportional fees for partial sells
            if self.sell_trade.fees != 0:
                if buy_item.trade:
                    try:
                        proportional_fees = (buy_item.amount / buy_item.trade.amount) * buy_item.trade.fees
                    except Exception as e:
                        logger.error(f"ERROR: {str(e)}")
                        proportional_fees = 0
                else:
                    proportional_fees = 0
                item_cost -= proportional_fees

            total_cost += item_cost

        return round(total_cost, 2)

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
        return round(self.cost_sell_eur - self.cost_buy_in_eur, 2)


class BalanceQueue:

    def __init__(self):
        self.queues = defaultdict(lambda: deque())
        self.withdrawals = defaultdict()
        self.reverse_splits = defaultdict()
        self.splits = []

    def current_amount(self, ticker):
        if ticker not in self.queues:
            return 0
        current_amount = round(sum([o.amount for o in self.queues[ticker]]), 8)
        if current_amount < 0:
            logger.warning(f"Current amount is negative! {current_amount} for {ticker}")
        return round(sum([o.amount for o in self.queues[ticker]]), 8)

    #def average_price(self, ticker):
    #    return round(([o.amount for o in self.queues[ticker]]), 8)

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
        if item.amount == 0:
            logger.debug(f"Put data with amount 0 for {item.trade.ticker}")
        queue.append(item)

    def withdrawal_old(self, order):
        queue = self.queues[order.ticker]
        items_bought = []
        remaining_sell_amount = order.amount - order.fees
        # if order.ticker not in self.withdrawals:
            # self.withdrawals[order.ticker] = []

        while remaining_sell_amount > 0:
            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                items_bought.append(PartialOrder(remaining_sell_amount, None))
                logger.warning(
                    f"ALERT - NO BOUGHT ITEM LEFT for withdrawal! Pair: {order.ticker}. Current amount is {self.current_amount(order.ticker)}")
                break

            item = self._pop(queue)
            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                items_bought.append(PartialOrder(remaining_sell_amount, item.trade))
                item.amount = float(
                    "{:0.8f}".format(item.amount - remaining_sell_amount - (order.fees if order.fees else 0)))
                self._put_back(queue, item)
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
            else:
                logger.error("Unhandled condition. Please check!")

        withdrawal_order = SellInfo(order, items_bought)
        # self.withdrawals[order.currency].append(withdrawal_order)
        return withdrawal_order

    def deposit(self, order, withdrawals, buy_order=None):
        # check here if DEPOSITED
        if hasattr(order, 'withdrawal') and order.withdrawal:
            # remove withdrawal fee from queue
            queue = self.queues[order.symbol]
            withdrawal = next(w for w in withdrawals[order.symbol] if w.id == order.withdrawal)
            if withdrawal.fee == 0 and withdrawal.amount != order.amount:
                withdrawal.fee = withdrawal.amount - order.amount
            queue[0].amount = float("{:0.8f}".format(queue[0].amount - withdrawal.fee))

            return

        # deposit without withdrawal detected, adding to the queue with buy at market price
        # logger.debug(f"Inserting transaction to the queue! {order.currency} - {order.amount}")
        self._put(self.queues[order.symbol], PartialOrder(order.amount, buy_order))

    def withdrawal(self, order, withdrawals):
        # check here if DEPOSITED
        if hasattr(order, 'deposit') and order.deposit:
            # do nothing
            return

        order = Transaction(Transaction.Type.SELL, order, order.symbol, order.amount, 0, order.fee)
        queue = self.queues[order.ticker]
        items_bought = []
        remaining_sell_amount = order.amount - order.fees
        # if order.ticker not in self.withdrawals:
            # self.withdrawals[order.ticker] = []

        while remaining_sell_amount > 0:
            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                items_bought.append(PartialOrder(remaining_sell_amount, None))
                logger.warning(
                    f"ALERT - NO BOUGHT ITEM LEFT for withdrawal! Pair: {order.ticker}. Current amount is {self.current_amount(order.ticker)}")
                break

            item = self._pop(queue)
            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                items_bought.append(PartialOrder(remaining_sell_amount, item.trade))
                item.amount = float(
                    "{:0.8f}".format(item.amount - remaining_sell_amount - (order.fees if order.fees else 0)))
                self._put_back(queue, item)
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
            else:
                logger.error("Unhandled condition. Please check!")

        withdrawal_order = SellInfo(order, items_bought)
        # self.withdrawals[order.currency].append(withdrawal_order)
        return withdrawal_order

    def deposit_old(self, order):
        """
            when deposit is detected, instead of adding to the queue, we change only the account_id of the order
        """
        if order.currency == 'EUR':
            self._put(self.queues[order.currency], PartialOrder(order.amount, None))
            return

        if order.currency not in self.withdrawals or len(self.withdrawals[order.currency]) == 0:
            logger.error(
                f"Unable to match withdrawal {order.currency} order with deposit order. Deposit amount: {order.amount}")
            self._put(self.queues[order.currency], PartialOrder(order.amount, None))
            return

        # search for the according withdrawal
        wth_order = None
        for o in [w for w in self.withdrawals[order.currency] if w.status != 'DEPOSITED']:
            # TODO: fee is required?
            # withdraw_amount = o.sell_trade.amount + o.sell_trade.fee
            withdraw_amount = o.amount + o.fee
            if withdraw_amount >= order.amount and withdraw_amount - order.amount < 1.0:
                wth_order = o
                break

        if wth_order:
            # TODO: change account of buy orders, and modify the queue order with the new account
            wth_order.status = 'DEPOSITED'
            wth_order.account_id = order.account_id
            # self.withdrawals[order.currency].remove(wth_order)
            # for o in wth_order.buy_items:
                # o.account_id = order.account_id
                # self._put(self.queues[order.currency], o)
        else:
            logger.warning(f"Unable to get withdrawal order for deposit of {order.amount}{order.currency}")
            # self._put(self.queues[order.currency], PartialOrder(order.amount, None))

        return

    def withdrawal_to_remove(self, order):
        # instead of remove from the queue, i keep the list of withdrawals in a separate list
        # why? withdrawal can take several hours, so we cannot confirm the diposit immediately
        # if we operate when the deposit is not confirmed, we can have a problem with the queue
        # queue remains equal
        #  TODO: fees should be considered

        # we consider the withdrawal without selling from the queue
        if order.currency not in self.withdrawals:
            self.withdrawals[order.currency] = []
        self.withdrawals[order.currency].append(order)

        # TODO: remove fees from the queue
        if order.fee > 0:
            queue = self.queues[order.currency]
            logger.warning(f"Fee detected for withdrawal: {order.fee}")
            order = Transaction(Transaction.Type.SELL, order, order.currency, order.fee, 0, 0)
            sell_order = self.sell(order)
        elif order.fee >= 0:
            queue = self.queues[order.currency]
            logger.warning(f"Fee detected for withdrawal of {order.amount}{order.currency}: {order.fee}")
            order = Transaction(Transaction.Type.SELL, order, order.currency, order.fee, 0, 0)
            sell_order = self.sell(order)

    def buy(self, order):
        if order.order_type == 'StockTransactionDTO':
            amount = order.amount
        else:
            amount = order.amount - order.fees
        if amount == 0:
            logger.warning(f"Buying amount 0 for {order.ticker}")
        self._put(self.queues[order.ticker], PartialOrder(amount, order))

    def sell(self, order):
        remaining_sell_amount = order.amount
        items_bought = []
        queue = self.queues[order.ticker]
        fees = order.fees if order.order_type != 'StockTransactionDTO' else 0

        if order.transaction_id == 12113:
            print("Check here, no items bought??!!!")
        while remaining_sell_amount > 0:

            if self._is_empty(queue):  # no bought items left but sell is not fully covered
                items_bought.append(PartialOrder(remaining_sell_amount, None))
                logger.warning(
                    f"ALERT - NO BOUGHT ITEM LEFT!! Pair: {order.ticker} Current amount is {self.current_amount(order.ticker)}")
                break

            item = self._pop(queue)
            if item.trade and item.trade.ticker != order.ticker:
                logger.warning("Different items: {} vs {}".format(item.trade.ticker, order.ticker))

            if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                items_bought.append(PartialOrder(remaining_sell_amount, item.trade))
                # item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - order.fee))
                if order.order_type != 'StockTransactionDTO':
                    item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - fees))
                else:
                    item.amount = item.amount - remaining_sell_amount

                if item.amount == 0:
                    # no put_back
                    logger.warning(f"Item amount is 0. {order.ticker}")
                    pass
                if item.amount > 0:
                    self._put_back(queue, item)
                else:
                    logger.warning(f"Item amount is negative! {item.amount}{order.ticker}")
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                # remaining_sell_amount -= item.amount

                if order.order_type != 'StockTransactionDTO':
                    remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
                else:
                    remaining_sell_amount = remaining_sell_amount - item.amount
            else:
                logger.error("Unhandled condition. Please check!")

        return SellInfo(order, items_bought)
