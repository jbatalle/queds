from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.broker import StockTransaction, Wallet, ClosedOrder, OpenOrder, Ticker, ProxyOrder, SplitOrder
from wallet_processor.utils import BalanceQueue, Transaction
from typing import List, Tuple, Dict
from sqlalchemy.orm import joinedload


class BrokerProcessor(AbstractEntity):

    def __init__(self):
        super(BrokerProcessor, self).__init__()
        self.otc_orders = []
        self.split_orders = []
        self.spinoff_orders = []
        self.fractional_orders = []
        self.closed_orders = []

        self.isin_ticker = {}

    def generate_transaction_logs(self):
        # TransactionLog.bulk_save_objects(self.logs)
        pass

    @staticmethod
    def preprocess(orders):
        return orders

    @staticmethod
    def clean(transactions) -> None:
        """
        Removes all closed and proxy orders from the database.
        """
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
        Retrieve all stock orders for the provided accounts in ascending order.
        """
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

    def trade(self, queue, order) -> Tuple:
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

        sell_items, queue_result = None, None
        fees = order.fee + order.exchange_fee
        if (order.shares == 0 or order.price == 0) and order.type == StockTransaction.Type.SELL:
            self.print_operation(queue, order, f"Sell Shares or price is 0. Shares: {order.shares}. Price: {order.price}. Type: {order.type}!")
            # TODO: analyze if return here when transaction is SELL
            pass
            # return None, None
        if (order.shares == 0 or order.price == 0) and order.type == StockTransaction.Type.BUY:
            # self._logger.warning(f"{order.value_date}-{order.ticker.isin} - Buy Shares or price is 0. Shares: {order.shares}. Price: {order.price}. Type: {order.type}!")
            pass
            # return None, None

        if order.shares == 0 and order.type == StockTransaction.Type.SPLIT_SELL:
            # convert split to buy
            order.type = StockTransaction.Type.SPLIT_BUY
            pass

        # Get original currency rate if this is part of an existing position
        original_currency_rate = None
        if order.ticker.isin in queue.queues and queue.queues[order.ticker.isin]:
            original_currency_rate = queue.queues[order.ticker.isin][0].original_currency_rate

        if order.type in [StockTransaction.Type.BUY]:
            self.print_operation(queue, order, 'Buy')
            order = Transaction(Transaction.Type.BUY, order, order.ticker.isin, order.shares, order.price, fees)
            queue.buy(order)
        elif order.type == StockTransaction.Type.SELL:
            self.print_operation(queue, order, 'Sell')
            order = Transaction(Transaction.Type.SELL, order, order.ticker.isin, order.shares, order.price, fees)
            sell_items = queue.sell(order)
        elif order.type == StockTransaction.Type.SPIN_OFF_SELL:
            # check if order exists in spin_off list and match the buy spin_off and execute an ISIN change
            # if not, do nothing
            self.print_operation(queue, order, 'Sell Spinoff')
            spinoff_order = next((o for o in self.spinoff_orders if o.shares == order.shares), None)

            if not spinoff_order:
                self.print_operation(queue, order, 'Spinoff without sell!')
                # TODO: check if we have previous fractional orders in self.fractional_orders
                fractional_order = next((o for o in self.fractional_orders if o.amount == order.shares and o.sell_trade.ticker == order.ticker.isin), None)
                if order.ticker.isin in queue.queues and not fractional_order:
                    self.print_operation(queue, order, 'Selling Spinoff')
                    order = Transaction(Transaction.Type.SELL, order, order.ticker.isin, order.shares, order.price, fees)
                    sell_items = queue.sell(order)
                    return sell_items, None
                return None, None

            if order.ticker.isin != spinoff_order.ticker.isin:
                # queue.queues[order.ticker.isin] = queue.queues.pop(spinoff_order.ticker.isin)
                queue.queues[spinoff_order.ticker.isin] = queue.queues.pop(order.ticker.isin)
            #if order.ticker.isin not in queue.queues:
                #self._logger.debug(
#                    f"{order.value_date}-{order.ticker.isin}-{order.ticker.ticker}-Changing ISIN for SpinOff order. OLD: {spinoff_order.ticker.isin} - NEW: {order.ticker.isin}")
#                queue.queues[order.ticker.isin] = queue.queues.pop(spinoff_order.ticker.isin)
            else:
                self._logger.info("Ticker already in queue! What to do here?")
            self.spinoff_orders.remove(spinoff_order)
        elif order.type == StockTransaction.Type.SPIN_OFF_BUY:
            self.print_operation(queue, order, 'Buy SpinOff')
            self.spinoff_orders.append(order)
            order = Transaction(Transaction.Type.BUY, order, order.ticker.isin, order.shares, order.price, fees)
            queue.buy(order)
        elif order.type == StockTransaction.Type.OTC_SELL:
            self.print_operation(queue, order, 'FROM OTC')
            self.otc_orders.append(order)
        elif order.type in [StockTransaction.Type.OTC_BUY]:
            # moving to otc
            self.print_operation(queue, order, 'TO OTC')

            otc_order = next((o for o in self.otc_orders if o.shares == order.shares), None)
            if not otc_order:
                self.print_operation(queue, order, 'OTC order not found for')
                return None, order

            if order.ticker.isin != otc_order.ticker.isin:
                if otc_order.ticker.isin in queue.queues and queue.current_amount(otc_order.ticker.isin):
                    queue.queues[order.ticker.isin] = queue.queues.pop(otc_order.ticker.isin)
                elif order.ticker.isin in queue.queues and queue.current_amount(order.ticker.isin):
                    queue.queues[otc_order.ticker.isin] = queue.queues.pop(order.ticker.isin)
                else:
                    self._logger.debug(f"Ticker found {order.ticker.isin} in queue. Check for {otc_order.ticker.isin}")
            else:
                self._logger.debug(f"Do nothing for Ticker {order.ticker.isin} not in queue. Check for {otc_order.ticker.isin}")

            self.otc_orders.remove(otc_order)
            return None, None

        elif order.type == StockTransaction.Type.SPLIT_BUY:
            self.print_operation(queue, order, 'Split buy')
            new_order = Transaction(Transaction.Type.BUY, order, order.ticker.isin, order.shares, order.price, fees)
            sell_items, queue_result = self.parse_split(order, new_order, queue)

        elif order.type == StockTransaction.Type.SPLIT_SELL:
            self.print_operation(queue, order, 'Split sell')
            sell_order = Transaction(Transaction.Type.SELL, order, order.ticker.isin, order.shares, order.price, fees)
            self.split_orders.append(sell_order)
        else:
            self._logger.warning(f"Unknown transaction type: {order.type}")
            return None, queue_result

        return sell_items, queue_result

    def print_operation(self, queue, order, operation):
        # TODO: transaction log
        self._logger.debug(f"{order.value_date}-{order.ticker.isin}-{order.ticker.ticker} - "
                           f"{operation}: {order.shares}@{order.price}. "
                           f"Queue amount ({order.ticker.ticker}): {queue.current_amount(order.ticker.isin)}")

    def parse_split(self, order_trs, order, queue):
        """
        Handles stock splits while preserving original currency rates
        """
        if order.ticker in queue.queues and len(queue.queues[order.ticker]) > 0:
            split_order = next((o for o in self.split_orders if o.ticker == order.ticker), None)
        else:
            split_order = next((o for o in self.split_orders if o.currency_rate == order.currency_rate
                                and o.value_date == order.value_date), None)
        if not split_order:
            self._logger.debug(f"{order.value_date}-{order.ticker} - Requeue split order {order.amount}@{order.price}")
            return None, order_trs

        self.split_orders.remove(split_order)
        return self._handle_split_order(order_trs, order, split_order, queue)

    def _handle_split_order(self, order_trs, order, split_order, queue):
        """
        Handle the logic of processing a split order.
        """
        total_shares_before_split = queue.current_amount(split_order.ticker)

        # Calculate split ratio
        if split_order.price != 0:
            ratio = round(order.price/split_order.price)
            if ratio == 0:
                self._logger.warning(f"Ratio is 0: {ratio}")
                ratio = 1
            fractional_shares = total_shares_before_split % ratio
        elif split_order.amount != 0 and order.amount > 0:
            ratio = round(split_order.amount/order.amount)
            fractional_shares = total_shares_before_split % ratio
        else:
            ratio = 1
            fractional_shares = total_shares_before_split

        self._logger.debug(f"{order.value_date}-{order.ticker} - Split old ISIN {split_order.ticker} - New: {order.ticker}. Ratio: {ratio}. Order price vs split price: {order.price} vs {split_order.price}")
        sell_order = None

        # Handling fractional shares
        if fractional_shares > 0:
            # original_orders = queue.queues.get(split_order.ticker, deque())
            # original_currency_rate = original_orders[0].currency_rate if original_orders else order.currency_rate
            self._logger.debug(f"{order.value_date}-{order.ticker} - Selling off {fractional_shares} fractional shares due to split")
            # TODO: check if include order_trs or other
            #fractional_sell_order = Transaction(Transaction.Type.SELL, order_trs, split_order.ticker,
                                                #fractional_shares, split_order.price, order.fees)
            # fractional_sell_info = queue.sell(fractional_sell_order)
            split_order.amount = fractional_shares
            sell_order = queue.sell(split_order)
            self.fractional_orders.append(sell_order)

        # Sell all remaining old shares
        remaining_shares = total_shares_before_split - fractional_shares
        if remaining_shares > 0:
            old_sell_order = Transaction(Transaction.Type.SELL, order_trs, split_order.ticker,
                                         remaining_shares, split_order.price, 0)  # No fees for this internal operation
            old_sell_info = queue.sell(old_sell_order)

            # Calculate the new buy price based on the original purchase prices, keep buy currency_rate
        # if remaining_shares > 0:
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
                # TODO: currency rate should be consider the splits
                if shares == 0:
                    shares += order.amount
                    avg_price = order.price
                    total_cost = shares * avg_price
                    total_cost_eur += shares * avg_price * order.original_currency_rate
                    fees = order.fee
                    open_orders.append(OpenOrder(transaction_id=order.trade.transaction_id, shares=shares, price=avg_price, currency_rate=order.original_currency_rate))
                    continue

                avg_price = (shares * avg_price + order.amount * order.price) / (shares + order.amount)
                # TODO: calc average fee?
                shares += order.amount
                total_cost += order.price * order.amount
                total_cost_eur += order.price * order.amount * order.original_currency_rate
                fees += order.fee
                open_orders.append(OpenOrder(transaction_id=order.trade.transaction_id, shares=order.amount, price=avg_price, currency_rate=order.original_currency_rate))

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
        orders_to_delete = OpenOrder.query.filter(OpenOrder.transaction_id.in_([t.id for t in orders])).all()
        wallet_ids = [order.wallet_id for order in orders_to_delete]

        # Delete the OpenOrders
        OpenOrder.query.filter(OpenOrder.transaction_id.in_([t.id for t in orders])).delete()

        # Delete only the order_id associated to Wallets
        # Wallet.query.filter(Wallet.id.in_(wallet_ids)).delete()

        # Delete all wallet realted to the user because if the user removes the account this is not cleaned
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

            if order.type in [StockTransaction.Type.BUY, StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.OTC_BUY, StockTransaction.Type.SPIN_OFF_BUY]:
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
        # TODO: we are not able to detect an ISIN change, so after a split we count separate benefits for same ticker but different isin
        for order in orders:
            if order.ticker.isin in queue.queues and len(queue.queues[order.ticker.isin]) > 0:
                continue

            cost = round(order.shares * order.price * order.currency_rate, 2)
            if order.ticker.isin not in benefits:
                benefits[order.ticker.isin] = 0
            if order.type in [StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.SPLIT_SELL]:
                continue
            if order.type in [StockTransaction.Type.BUY, StockTransaction.Type.SPLIT_BUY, StockTransaction.Type.OTC_BUY]:
                benefits[order.ticker.isin] -= round(cost - order.fee - order.exchange_fee, 2)
            else:
                benefits[order.ticker.isin] += round(cost + order.fee + order.exchange_fee, 2)

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

    def get_balances(self, accounts):
        pass
