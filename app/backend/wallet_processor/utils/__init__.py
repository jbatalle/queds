from collections import deque, defaultdict
from functools import reduce
import logging
import traceback

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
        self.account_id = order.account_id
        self.fees = round(fees, 8) if fees else 0.0
        # self.currency_rate = round(order.currency_rate, 4) if hasattr(order, 'currency_rate') else 1
        self.currency_rate = order.currency_rate if hasattr(order, 'currency_rate') else 1
        self.original_currency_rate = original_currency_rate or self.currency_rate

    @property
    def cost(self):
        """Cost in base currency."""
        return self.amount * self.price

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
    Represents a partial portion of a buy order.
    """

    def __init__(self, amount, order, original_trade=None, exchange_id=None):
        """
        :param order: corresponding trade or None if unaccounted
        :param original_trade: reference to the original buy trade before splits
        """
        self.amount = amount
        self.trade = order
        self.original_trade = original_trade or order
        self.exchange_id = exchange_id or getattr(order, 'account_id', None)

    @property
    def fee(self):
        return self.trade.fees if self.trade else 0

    @property
    def price(self):
        return self.trade.price if self.trade else 0

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
    Info related to a sell transaction.
    """

    def __init__(self, sell_trade, buy_items):
        self.sell_trade = sell_trade  # the trade representing the sale
        self.buy_items = buy_items or [] # list of buys from the past associated with the sale

        if not self.buy_items:
            logger.warning(f"No buy items found for {self.sell_trade.ticker}")

    def __str__(self):
        return f"Sell: {self.sell_trade.ticker} {self.amount}@{self.sell_trade.price} - {self.cost_sell} - {self.cost_buy}"

    @property
    def amount(self):
        """
        The amount sold (in original currency).
        """
        return sum(buy_item.amount for buy_item in self.buy_items)

    @property
    def average_price(self):
        """
        The average price of the sold items
        """
        return self.cost_buy / self.amount if self.amount != 0 else 0

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
        currency_rate = self.sell_trade.currency_rate or 1
        return self.sell_trade.amount * self.sell_trade.price * currency_rate + self.sell_trade.fees

    @property
    def cost_buy(self):
        """
        Cost when buying (in tax currency).
        """

        a = sum(buy_item.cost for buy_item in self.buy_items)
        # b = reduce(lambda a, b: a + b.cost, self.buy_items, 0.0)  # summarize cost of all buy items
        return a

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
            item_cost = buy_item.cost * getattr(buy_item.trade, 'currency_rate', 1)

            # Calculate proportional fees for partial sells
            if self.sell_trade.fees != 0 and buy_item.trade:
            # if self.sell_trade.fees != 0:
                #if buy_item.trade:
                    try:
                        proportional_fees = (buy_item.amount / buy_item.trade.amount) * buy_item.trade.fees
                        item_cost -= proportional_fees
                    except Exception as e:
                        logger.error(f"ERROR: {str(e)}")
                        # proportional_fees = 0
                #else:
                    #proportional_fees = 0

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
        if self.sell_trade.currency_rate is None:
            currency_rate = 0
        else:
            currency_rate = self.sell_trade.currency_rate
        return round(self.cost_sell_eur - self.cost_buy_in_eur, 2)


class BalanceQueue:

    def __init__(self):
        self.queues = defaultdict(lambda: deque())
        self.withdrawals = defaultdict()

    def current_amount(self, ticker):
        if ticker not in self.queues:
            return 0
        total = round(sum([o.amount for o in self.queues[ticker]]), 8)
        if total < 0:
            logger.warning(f"Negative balance detected for {ticker}: {total}")
        return round(sum([o.amount for o in self.queues[ticker]]), 8)

    def current_amount_by_exchange(self):
        pass

    @staticmethod
    def _is_empty(queue):
        return len(queue) == 0

    @staticmethod
    def _pop(queue):
        return queue.popleft()

    @staticmethod
    def _put_back(queue, item):
        queue.appendleft(item)

    @staticmethod
    def _put(queue, item):
        queue.append(item)

    def deposit(self, order, withdrawals, buy_order=None):
        # check here if DEPOSITED
        if hasattr(order, 'withdrawal') and order.withdrawal:
            logger.debug(f"Queue amount before deposit for {order.symbol}: {self.current_amount(order.symbol)}")
            # remove withdrawal fee from queue
            if order.symbol == 'FLR':
                print(f"CHECK WITHDRAWAL OF {order.symbol}. REVIEW THE SECOND DEPOSIT. Current amount is {self.current_amount(order.symbol)}. Order: {order.amount}")

            queue = self.queues[order.symbol]
            withdrawal = next(w for w in withdrawals[order.symbol] if w.id == order.withdrawal)
            if withdrawal.fee == 0 and withdrawal.amount != order.amount:
                withdrawal.fee = withdrawal.amount - order.amount

            remaining_sell_amount = order.amount + withdrawal.fee  # deposit_amount
            put_back_orders = []
            while remaining_sell_amount > 0:
                if self._is_empty(queue):  # no bought items left but sell is not fully covered
                    # items_bought.append(PartialOrder(remaining_sell_amount, None))
                    logger.warning(
                        f"ALERT - NO BOUGHT ITEM LEFT for deposit! Pair: {order.symbol}. Current amount is {self.current_amount(order.symbol)}")
                    break

                item = self._pop(queue)
                if item.exchange_id == order.account_id:
                    put_back_orders.append(item)
                    continue

                logger.debug(f"POP item for deposit: {item.amount}@{order.symbol}. Remaining: {remaining_sell_amount}@{order.symbol}")
                if remaining_sell_amount < item.amount:  # sell amount is entirely covered by bought items
                    # two items, the first continue belongs to first exchange, the second to the target exchange

                    # reinsert to source exchange the rest of the amount
                    item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount))
                    put_back_orders.append(PartialOrder(item.amount, item.trade))
                    put_back_orders.append(PartialOrder(remaining_sell_amount, item.trade, exchange_id=order.account_id)) # , order.account))
                    logger.debug(f"Insert {remaining_sell_amount} to target exchange and reinsert {item.amount} to source exchange")
                    break
                elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                    # items_bought.append(item)
                    logger.debug(f"Reinsert {item.amount} to target exchange")
                    remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
                    put_back_orders.append(PartialOrder(item.amount, item.trade, exchange_id=order.account_id))
                    # self._put_back(queue, )

            total_fee = withdrawal.fee
            if total_fee > 0:
                print("CHECK, we need to remove the fee from the source? item.exchange_id == order.account_id")
            for p in reversed(put_back_orders):
                if total_fee >= p.amount:
                    total_fee = total_fee - p.amount
                    continue
                elif p.amount > total_fee > 0 and p.exchange_id == order.account_id:
                    p.amount -= total_fee
                    total_fee = 0
                self._put_back(queue, p)

            logger.debug(f"Queue amount after deposit for {order.symbol}: {self.current_amount(order.symbol)}")
            return

        # Deposit without matching withdrawal → treat as new buy
        self._put(self.queues[order.symbol], PartialOrder(order.amount, buy_order))

    def withdrawal(self, order, withdrawals):
        if hasattr(order, 'deposit') and order.deposit:
            # do nothing
            return None

        order = Transaction(Transaction.Type.SELL, order, order.symbol, order.amount, 0, order.fee)
        remaining_sell_amount = order.amount - order.fees
        items_bought = []
        queue = self.queues[order.ticker]
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

        # TODO: what to do with this sell?
        return SellInfo(order, items_bought)

    def buy(self, order):
        if order.order_type == 'StockTransactionDTO':
            amount = order.amount
        else:
            amount = order.amount - order.fees
        if amount == 0:
            # logger.warning(f"Buying amount is 0 for {order.ticker}")
            return
        self._put(self.queues[order.ticker], PartialOrder(amount, order))

    def sell(self, order):
        remaining_sell_amount = order.amount
        items_bought = []
        queue = self.queues[order.ticker]
        fees = order.fees if order.order_type != 'StockTransactionDTO' else 0

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
                #if order.order_type != 'CryptoEventDTO':
#                    item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - fees))
#                else:
#                    item.amount = item.amount - remaining_sell_amount
                #if item.amount - remaining_sell_amount - fees < 0:
#                    print("ANALYZE THIS")
                item.amount = float("{:0.8f}".format(item.amount - remaining_sell_amount - fees))

                #if item.amount == 0:
                    # no put_back
                    #logger.warning(f"Item amount is 0. {order.ticker}")
                    #pass
                if item.amount > 0:
                    self._put_back(queue, item)
                else:
                    logger.warning(f"Item amount is negative! {item.amount}{order.ticker}")
                break
            elif remaining_sell_amount >= item.amount:  # bought item is fully consumed by sell
                items_bought.append(item)
                # remaining_sell_amount -= item.amount

                if order.order_type == 'CryptoEventDTO':
                    remaining_sell_amount = float("{:0.8f}".format(remaining_sell_amount - item.amount))
                else:
                    remaining_sell_amount = remaining_sell_amount - item.amount
            else:
                logger.error("Unhandled condition:\n" + traceback.format_exc())

        return SellInfo(order, items_bought)
