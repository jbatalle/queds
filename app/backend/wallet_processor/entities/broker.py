from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.broker import StockTransaction, Wallet, ClosedOrder, OpenOrder, Ticker, ProxyOrder, SplitOrder
from wallet_processor.utils import BalanceQueue, Transaction

from sqlalchemy.orm import joinedload


class BrokerProcessor(AbstractEntity):

    def __init__(self):
        super(BrokerProcessor, self).__init__()
        self.otc_orders = []
        self.split_orders = []

        self.orders = []
        self.wallet = {}  # Open positions by ticker_id
        self.closed_orders = []

        self.isin_ticker = {}

    @staticmethod
    def preprocess(orders):
        return orders

    @staticmethod
    def clean(transactions):
        # Remove all closed orders and proxy orders
        ids = [o.id for o in transactions]
        ProxyOrder.query.filter(ProxyOrder.transaction_id.in_(ids)).delete()
        ClosedOrder.query.filter(ClosedOrder.sell_transaction_id.in_(ids)).delete()

    @staticmethod
    def get_accounts(user_id):
        return Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                              Account.entity.has(type=Entity.Type.BROKER)).all()

    @staticmethod
    def get_orders(accounts):
        """
        Get all stock orders of user user_id in ASC order
        """
        # .options(joinedload('account.entity')) \
        orders = StockTransaction.query\
            .options(joinedload(StockTransaction.account)) \
            .options(joinedload(StockTransaction.ticker)) \
            .filter(StockTransaction.account_id.in_([a.id for a in accounts]))\
            .order_by(StockTransaction.value_date.asc(), StockTransaction.type.asc())\
            .all()
        return [o.dto for o in orders]

    @staticmethod
    def get_transactions(accounts):
        return []

    def trade(self, queue, order):
        """
        Processes stock orders, handling buys, sells, OTC, and splits.

        Parameters:
        queue : Queue
            The order queue to process transactions.
        order : StockTransaction
            The order to be processed.

        Returns:
        tuple
            (sell_items, queue_result) or (None, order)
        """
        if order.ticker.isin not in self.isin_ticker:
            self.isin_ticker[order.ticker.isin] = []
        self.isin_ticker[order.ticker.isin].append(order.ticker.isin)

        sell_items = None
        queue_result = None
        fees = order.fee + order.exchange_fee
        if order.shares == 0:
            self._logger.warning(f"Shares is 0 for {order.ticker.isin}!")
            pass
            # return None

        if order.shares == 0 and order.type == StockTransaction.Type.SPLIT_SELL:
            # convert split to buy
            order.type = StockTransaction.Type.SPLIT_BUY
            pass

        # Get original currency rate if this is part of an existing position
        original_currency_rate = None
        if order.ticker.isin in queue.queues and queue.queues[order.ticker.isin]:
            original_currency_rate = queue.queues[order.ticker.isin][0].original_currency_rate

        if order.type in [StockTransaction.Type.BUY]:
            order = Transaction(Transaction.Type.BUY, order, order.ticker.isin, order.shares, order.price, fees)
            queue.buy(order)
        elif order.type == StockTransaction.Type.SELL:
            order = Transaction(Transaction.Type.SELL, order, order.ticker.isin, order.shares, order.price, fees)
            sell_items = queue.sell(order)
        elif order.type == StockTransaction.Type.OTC_SELL:
            self.otc_orders.append(order)
        elif order.type in [StockTransaction.Type.OTC_BUY]:
            self._logger.debug(f"{order.ticker.isin} - {order.ticker.ticker} TO OTC. {order.shares}@{order.price}")

            if order.ticker.isin not in queue.queues:
                # search the OLD isin and replace by the new one
                otc_order = [o for o in self.otc_orders if o.shares == order.shares]
                if not otc_order:
                    self._logger.error(f"OTC order not found for {order.ticker.isin} - {order.ticker.ticker}!")
                    return None, order
                self._logger.info(f"Changing ISIN for OTC order. {order.ticker.ticker} - OLD: {otc_order[0].ticker.isin} - NEW: {order.ticker.isin}")
                self.otc_orders.remove(otc_order[0])
                queue.queues[order.ticker.isin] = queue.queues.pop(otc_order[0].ticker.isin)

        elif order.type == StockTransaction.Type.SPLIT_BUY:
            self._logger.info(f"Split buy: {order.ticker.ticker} - {order.ticker.isin} - {order.shares}@{order.price}")
            new_order = Transaction(Transaction.Type.BUY, order, order.ticker.isin, order.shares, order.price, fees)
            sell_items, queue_result = self.parse_split(order, new_order, queue)

        elif order.type == StockTransaction.Type.SPLIT_SELL:
            self._logger.info(f"Split sell: {order.ticker.ticker} - {order.ticker.isin} - {order.shares}@{order.price}")
            sell_order = Transaction(Transaction.Type.SELL, order, order.ticker.isin, order.shares, order.price, fees)
            self.split_orders.append(sell_order)
        else:
            self._logger.warning(f"Unknown transaction type: {order.type}")
            return None, queue_result

        return sell_items, queue_result

    def parse_split(self, order_trs, order, queue):
        """
        Handles stock splits while preserving original currency rates
        """
        if order.ticker in queue.queues:
            split_order = next((o for o in self.split_orders if o.ticker == order.ticker), None)
        else:
            self._logger.warning(f"Split with ISIN change {order.ticker}")
            split_order = next((o for o in self.split_orders if o.currency_rate == order.currency_rate
                                and o.time == order.time), None)
        if not split_order:
            self._logger.warning(f"Requeue split order with ISIN {order.ticker} - {order.amount}@{order.price}")
            return None, order_trs

        total_shares_before_split = queue.current_amount(split_order.ticker)

        # Calculate split ratio
        if split_order.price != 0:
            ratio = round(order.price/split_order.price)
            self._logger.info(f"Split buy: {order.ticker} - {split_order.ticker} - Ratio: {ratio}")
            fractional_shares = total_shares_before_split % ratio
        else:
            ratio = 1
            fractional_shares = total_shares_before_split

        sell_order = None
        # Handle fractional shares
        if fractional_shares > 0:
            # original_orders = queue.queues.get(split_order.ticker, deque())
            # original_currency_rate = original_orders[0].currency_rate if original_orders else order.currency_rate
            self._logger.info(f"Selling off {fractional_shares} fractional shares due to split")
            # TODO: check if include order_trs or other
            #fractional_sell_order = Transaction(Transaction.Type.SELL, order_trs, split_order.ticker,
                                                #fractional_shares, split_order.price, order.fees)
            # fractional_sell_info = queue.sell(fractional_sell_order)
            split_order.amount = fractional_shares
            fractional_sell_info = queue.sell(split_order)
            sell_order = fractional_sell_info

        # Sell all remaining old shares
        remaining_shares = total_shares_before_split - fractional_shares
        old_sell_order = Transaction(Transaction.Type.SELL, order_trs, split_order.ticker,
                                     remaining_shares, split_order.price, 0)  # No fees for this internal operation
        old_sell_info = queue.sell(old_sell_order)

        # Calculate the new buy price based on the original purchase prices, keep buy currency_rate

        if remaining_shares > 0:
            total_cost = sum(item.cost for item in old_sell_info.buy_items)
            new_shares = remaining_shares // ratio
            if new_shares == 0:
                # no order should be queued
                pass
            else:
                new_price = total_cost / new_shares

                # Create and process the new buy order
                # TODO: order_trs should contain info from the original order, like the currency rate
                currency_rate = old_sell_info.buy_items[0].original_currency_rate
                new_buy_order = Transaction(Transaction.Type.BUY, order_trs, order.ticker, new_shares, new_price, order.fees, original_currency_rate=currency_rate)
                queue.buy(new_buy_order)

        if order.ticker not in self.isin_ticker:
            self.isin_ticker[order.ticker] = []
        self.isin_ticker[order.ticker].append(split_order.ticker)

        return sell_order, None

    def create_split_order(self, sell_order, buy_order, ratio):
        new_shares = 0
        remain_shares = 0
        split_order = SplitOrder(buy_transaction_id=buy_order.id,
                                 sell_transaction_id=sell_order.id,
                                 ratio=ratio,
                                 price=sell_order.price,
                                 shares=buy_order.shares,
                                 new_shares=sell_order.shares)

        SplitOrder.bulk_save_objects([split_order])

    def create_closed_orders(self, orders, tracked_orders):
        """
        Insert closed orders to database
        """
        self._logger.debug("Cleaning closed/wallet/proxy orders")
        self.clean(orders)
        # TODO: ignore reverse split transactions... in some way

        self._logger.debug("Generating new closed/wallet/proxy orders")
        closed_orders = []
        proxy_orders = []
        for sell_order in tracked_orders:
            # TODO: check if include shares and price of the sell instead the transaction_id
            closed_order = ClosedOrder(sell_transaction_id=sell_order.sell_trade.transaction_id)
            closed_orders.append(closed_order)

            for buy_order in sell_order.buy_items:
                if not buy_order.trade:
                    self._logger.warning(f"Some strange case! Order: {sell_order} - Buy_order: {buy_order}")
                    continue

                if sell_order.amount <= buy_order.amount:
                    try:
                        partial_fee = buy_order.fee / (buy_order.trade.amount / sell_order.amount)
                    except:
                        partial_fee = 0
                else:
                    partial_fee = buy_order.fee / (sell_order.amount / buy_order.amount)

                proxy_order = ProxyOrder(
                    closed_order=closed_order,
                    transaction_id=buy_order.trade.transaction_id,
                    shares=buy_order.amount,
                    price=buy_order.price,
                    partial_fee=partial_fee
                )
                proxy_orders.append(proxy_order)

        # Save the objects in a single database query
        ClosedOrder.bulk_save_objects(closed_orders)
        for proxy_order in proxy_orders:
            proxy_order.closed_order_id = proxy_order.closed_order.id

        ProxyOrder.bulk_save_objects(proxy_orders)
        self._logger.debug("Closed and proxy orders inserted correctly!")

    def calc_wallet(self, user_id, orders, queue, tracked_orders):
        """
        Calculate current open orders
        """
        to_insert = []
        tickers = {t.isin: t.id for t in Ticker.query.all()}
        for ticker, partial_orders in queue.queues.items():
            if not ticker:
                self._logger.error("Ticker not found!")
                continue

            shares = 0
            avg_price = 0
            fees = 0
            total_cost = 0
            total_cost_eur = 0
            open_orders = []

            for order in partial_orders:
                if shares == 0:
                    shares += order.amount
                    avg_price = order.price
                    total_cost = shares * avg_price
                    total_cost_eur += shares * avg_price * order.trade.currency_rate
                    fees = order.fee
                    open_orders.append(OpenOrder(transaction_id=order.trade.transaction_id, shares=shares))
                    continue

                avg_price = (shares * avg_price + order.amount * order.price) / (shares + order.amount)
                # TODO: calc average fee?
                shares += order.amount
                total_cost += order.price * order.amount
                total_cost_eur += order.price * order.amount * order.trade.currency_rate
                fees += order.fee
                open_orders.append(OpenOrder(transaction_id=order.trade.transaction_id, shares=order.amount))

            if shares == 0:
                # self._logger.info(f"Shares is 0 for ticker {ticker}!")
                continue

            # Calculate current benefits taking into account sells
            current_benefits_eur = 0
            total_sell = 0
            total_sell_eur = 0
            for order in [w for w in tracked_orders if w.sell_trade.ticker == ticker]:
                current_benefits_eur += order.benefits_in_eur
                # total_sell += order.sell_trade.price * order.amount
                # total_sell_eur += order.sell_trade.price * order.amount * order.sell_trade.currency_rate
                fees += order.sell_trade.fees

            # self._logger.debug(f"Benefits: {current_benefits}. Fees: {fees}")
            break_even = (total_cost_eur - current_benefits_eur - fees) / shares

            w = Wallet(
                ticker_id=tickers[ticker],
                user_id=user_id,
                shares=shares,
                price=avg_price,  # in $, ticker currency
                cost=total_cost,  # in ticker currency without fees
                benefits=current_benefits_eur,  # in €, in front we should sum fees
                break_even=break_even if break_even > 0 else 0,  # in €, in front we apply the current fx_rate
                fees=fees  # in €
            )
            w.open_orders.extend(open_orders)
            to_insert.append(w)

        self._logger.debug("Removing open orders!")
        OpenOrder.query.filter(OpenOrder.transaction_id.in_([t.id for t in orders])).delete()

        Wallet.query.filter(Wallet.user_id == user_id).delete()
        Wallet.bulk_object(to_insert)
        self._logger.info("Wallet calculation done")

    @staticmethod
    def calc_balance_with_orders(orders):
        balance = {}
        for order in orders:
            if order.ticker.isin not in balance:
                balance[order.ticker.isin] = 0

            if order.shares == 0 and order.type == StockTransaction.Type.SPLIT_SELL:
                # convert split to buy
                order.type = StockTransaction.Type.SPLIT_BUY

            if order.type in [StockTransaction.Type.BUY, StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.OTC_BUY]:
                balance[order.ticker.isin] += order.shares
            else:
                balance[order.ticker.isin] -= order.shares

        return balance

    def check_benefits(self, queue, orders, closed_orders):
        # Calculate benefits from all orders
        # ignore orders that are in the queue, this calc should process only completed orders
        # unify ISIN-Ticker

        # New dictionary to store the full relations
        full_relation_dict = {}

        # Iterate through the original dictionary
        for key, values in self.isin_ticker.items():
            for value in values:
                # If the value is already a key in the original dictionary
                if value in self.isin_ticker:
                    # Add the key to the list of values for that key in the new dictionary
                    if value not in full_relation_dict:
                        full_relation_dict[value] = []
                    full_relation_dict[value].append(key)
                else:
                    # If the key is not already in the new dictionary, add it
                    if key not in full_relation_dict:
                        full_relation_dict[key] = []
                    full_relation_dict[key].extend(values)

        # Remove duplicates
        for key in full_relation_dict:
            full_relation_dict[key] = list(set(full_relation_dict[key]))

        benefits = {}
        for order in orders:
            #if order.ticker.isin != 'US75955K1025':
                #continue
            if order.ticker.isin in queue.queues and len(queue.queues[order.ticker.isin]) > 0:
                continue

            cost = round(order.shares * order.price * order.currency_rate, 2)
            print(f"Cost: {cost} - {order.fee} - {order.exchange_fee}: {- order.fee - order.exchange_fee} - {cost - order.fee - order.exchange_fee}")
            if order.ticker.isin not in benefits:
                benefits[order.ticker.isin] = 0
            if order.type in [StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.SPLIT_SELL]:
                continue
            if order.type in [StockTransaction.Type.BUY, StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.OTC_BUY]:
                benefits[order.ticker.isin] -= round(cost - order.fee - order.exchange_fee, 2)
            else:
                benefits[order.ticker.isin] += round(cost + order.fee + order.exchange_fee, 2)
            print(benefits[order.ticker.isin])

        benefits_orders = {}
        for order in closed_orders:
            ticker = order.sell_trade.ticker
            if ticker not in benefits_orders:
                benefits_orders[ticker] = order.benefits_in_eur
            else:
                benefits_orders[ticker] += order.benefits_in_eur

        for ticker, benefits_in_eur in benefits_orders.items():
            # ticker = order.sell_trade.ticker
            if ticker not in benefits:
                continue
            if abs(benefits_in_eur - benefits[ticker]) > 0.019 and (benefits[ticker] != 0 and benefits_in_eur > 0):
                self._logger.warning(f"Different benefits {ticker}. Orders: {benefits_in_eur} vs {benefits[ticker]}")
        return benefits
