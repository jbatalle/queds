from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.crypto import ExchangeWallet, ExchangeClosedOrder, ExchangeProxyOrder, \
    ExchangeOpenOrder, ExchangeBalance, CryptoEvent
from wallet_processor.utils import BalanceQueue, Transaction
from wallet_processor.utils.crypto_prices import get_price
from sqlalchemy.orm import joinedload


class CryptoProcessor(AbstractEntity):
    def __init__(self):
        super().__init__()
        self.withdrawals = {}

    @staticmethod
    def clean(orders):
        """Remove proxy and closed orders related to the provided orders."""
        ids = [o.id for o in orders]
        ExchangeProxyOrder.query.filter(ExchangeProxyOrder.order_id.in_(ids)).delete()
        ExchangeClosedOrder.query.filter(ExchangeClosedOrder.sell_order_id.in_(ids)).delete()

    @staticmethod
    def get_accounts(user_id):
        """Fetch all exchange-type account IDs for a given user."""
        return Account.query.with_entities(Account.id).filter(
            Account.user_id == user_id,
            Account.entity.has(type=Entity.Type.EXCHANGE)
        ).all()

    @staticmethod
    def get_orders(accounts):
        """Retrieve crypto orders for the given accounts ordered by value date."""
        events = CryptoEvent.query \
            .options(joinedload(CryptoEvent.account)) \
            .filter(CryptoEvent.account_id.in_([a.id for a in accounts])) \
            .order_by(CryptoEvent.value_date.asc()) \
            .all()

        return [o.dto for o in events]

    @staticmethod
    def get_transactions(accounts):
        """Currently returns no transactions (placeholder)."""
        return []

    def preprocess(self, orders):
        """
            Normalize tickers and pair withdrawals with matching deposits
            We match the withdrawals with the deposits
            If a withdrawal does not match, we create a sell order
            If a deposit does not match, we create a buy order
        """
        withdrawals = []
        deposits = []
        for o in orders:
            o.symbol = o.symbol.upper().replace("IOT", "IOTA").replace("IOTAA", "IOTA")\
                .replace("XRB", "NANO").replace("XBT", "BTC").replace("POE", "POET")

            o.deposit = None
            o.withdrawal = None
            if o.event_type != 'exchange_transaction' or o.symbol == 'EUR':
                continue

            if o.type == CryptoEvent.Type.WITHDRAWAL:
                withdrawals.append(o)
                self.withdrawals.setdefault(o.symbol, []).append(o)
            elif o.type == CryptoEvent.Type.DEPOSIT:
                deposits.append(o)

        for deposit in deposits:
            deposit.withdrawal = None

            if deposit.symbol not in self.withdrawals or len(self.withdrawals[deposit.symbol]) == 0:
                self._logger.error(f"{deposit.value_date.strftime('%Y-%m-%d %H:%M:%S')} - {deposit.symbol} - "
                                   f"No withdrawal detected for {deposit.symbol}. Amount: {deposit.amount} at {deposit.account.entity.name}")
                continue

            # search for the according withdrawal
            wth_order = None
            for withdrawal in [w for w in self.withdrawals[deposit.symbol] if w.status != 'DEPOSITED']:
                withdraw_amount = withdrawal.amount + withdrawal.fee
                if (withdraw_amount >= deposit.amount
                        and abs(withdraw_amount - deposit.amount) < 1.0
                        and withdrawal.account_id != deposit.account_id):
                    wth_order = withdrawal
                    wth_order.status = 'DEPOSITED'
                    wth_order.account_id = deposit.account_id
                    wth_order.deposit = deposit.id
                    deposit.withdrawal = wth_order.id

                    # change dates in case withdrawal is older than deposit
                    if deposit.value_date < wth_order.value_date:
                        # self._logger.warning(f"Deposit is previous than withdrawal. Changing dates {order.value_date} < {wth_order.value_date}")
                        wth_order.value_date = deposit.value_date
                    break

            if not wth_order:
                self._logger.error(f"{deposit.value_date.strftime('%Y-%m-%d %H:%M:%S')} - {deposit.symbol} - "
                                   f"Unable to match withdrawal with deposit. Amount: {deposit.amount} at {deposit.account.entity.name}")

        self._logger.debug(
            f"withdrawals deposited: {len([w for w in withdrawals if w.status == 'DEPOSITED'])}/{len(withdrawals)}. "
            f"Deposited withdrawals: {len([d for d in deposits if d.withdrawal is not None])}/{len(deposits)}."
        )
        return orders

    def print_operation(self, queue, order, operation):
        self._logger.debug(
            f"{order.value_date}-{order.ticker.isin}-{order.ticker.ticker} - "
            f"{operation}: {order.shares}@{order.price}. "
            f"Queue amount ({order.ticker.ticker}): {queue.current_amount(order.ticker.isin)}"
        )

    def trade(self, queue, order):
        """
        This function calculates the trade operations. Creates the queue and returns the sell orders
        """
        if order.amount == 0:
            return None, None

        if order.event_type == 'exchange_transaction':
            return self.process_transactions(queue, order)

        try:
            order.cost = round(order.amount * order.price, 8)
        except Exception:
            return None, None

        source, target = order.symbol.split("/")

        timestamp = order.value_date.strftime('%Y-%m-%d %H:%M:%S')
        current_eur = queue.current_amount('EUR')

        track_sell = True  # By default, assume we want to track the sell info
        if order.type == CryptoEvent.Type.BUY:
            if target == 'EUR':
                # Direct buy with EUR
                buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, order.price)
                order.cost = round(order.cost, 8) # TODO: return to 4?
                if order.cost == 0:
                    print("CHECK possible buy without items?")
                sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, order.price, order.fee)
                track_sell = False
            else:
                # Buy using non-EUR currency
                target_price = get_price(target, "EUR", order.value_date)
                source_price = order.price * target_price
                buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, source_price)
                sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, target_price,
                                               order.fee)

        elif order.type == CryptoEvent.Type.SELL:
            order.cost = round(order.cost, 8) # TODO: return to 4?
            if target == 'EUR':
                # Direct sell to EUR
                sell_transaction = Transaction(Transaction.Type.SELL, order, source, order.amount, order.price)
                buy_transaction = Transaction(Transaction.Type.BUY, order, target, order.cost, order.price, order.fee)
            else:
                # Sell to non-EUR currency
                target_price = get_price(target, "EUR", order.value_date)
                source_price = order.price * target_price
                sell_transaction = Transaction(Transaction.Type.SELL, order, source, order.amount, source_price)
                buy_transaction = Transaction(Transaction.Type.BUY, order, target, order.cost, target_price, order.fee)
        else:
            self._logger.debug("Unsupported transaction type encountered.")
            return None, None

        sell_info = queue.sell(sell_transaction)
        queue.buy(buy_transaction)

        self._logger.debug(
            f"{timestamp} - {'Buy' if order.type == CryptoEvent.Type.BUY else 'Sell'} {order.amount}{source}@{order.price} "
            f"{'from' if order.type == CryptoEvent.Type.BUY else 'to'} {target}. "
            f"{'Cost' if order.type == CryptoEvent.Type.BUY else 'Won'}: {order.cost}{target}. "
            f"{order.account.entity.name}. "
            f"Current EUR: {queue.current_amount('EUR')}. "
            f"Current {source}: {queue.current_amount(source)}. "
            f"Current {target}: {queue.current_amount(target)}"
        )
        if track_sell and sell_info:
            return sell_info, None
        return None, None


        if order.type == CryptoEvent.Type.BUY and target == 'EUR':
            buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, order.price)
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, order.price, order.fee)
            queue.buy(buy_transaction)
            queue.sell(sell_transaction)
            self._logger.debug(f"Current EUR: {queue.current_amount('EUR')}. Current {source}: {queue.current_amount(source)}")
            return None, None

        if order.type == CryptoEvent.Type.BUY:
            target_price = get_price(target, "EUR", order.value_date)
            source_price = order.price * target_price
            sell_transaction = Transaction(Transaction.Type.SELL, order, target, order.cost, target_price, order.fee)
            buy_transaction = Transaction(Transaction.Type.BUY, order, source, order.amount, source_price)
        elif order.type == CryptoEvent.Type.SELL and target == 'EUR':
            order.cost = round(order.cost, 4)
            sell_transaction = Transaction(Transaction.Type.SELL, order, source, order.amount, order.price)
            buy_transaction = Transaction(Transaction.Type.BUY, order, target, order.cost, order.price, order.fee)
        elif order.type == CryptoEvent.Type.SELL:
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

    def process_transactions(self, queue, order):
        if order.rx_address and 'MAINTENANCE' in order.rx_address:
            # TODO: review this? should be a sell?
            # or already defined when reading the CSVs
            return None, None

        buy_transaction = None
        # self._logger.debug(
        #    f"{value_date.strftime('%Y-%m-%d %H:%M:%S')} - {CryptoEvent.get_type(order.type)} - {order.amount}{order.symbol} to/from {order.account.entity.name}. "
        #    f"Current: {queue.current_amount(order.symbol)}{order.symbol}")

        if order.type == CryptoEvent.Type.DEPOSIT:
            if order.symbol != 'EUR':
                price = get_price(order.symbol, "EUR", order.value_date)
                cost = 0  # or order.cost
                buy_transaction = Transaction(Transaction.Type.BUY, order, order.symbol, cost, price, order.fee)
            queue.deposit(order, self.withdrawals, buy_transaction)

        elif order.type == CryptoEvent.Type.WITHDRAWAL:
            queue.withdrawal(order, self.withdrawals)

        elif order.type in [CryptoEvent.Type.STAKING, CryptoEvent.Type.AIRDROP]:
            price = get_price(order.symbol, "EUR", order.value_date)
            cost = 0  # or order.cost
            buy_transaction = Transaction(Transaction.Type.BUY, order, order.symbol, cost, price, order.fee)
            queue.deposit(order, self.withdrawals, buy_transaction)

        return None, None

    def create_closed_orders(self, orders, tracked_orders):
        """Insert closed orders and their proxy mappings."""
        self._logger.debug("Cleaning closed/wallet/proxy orders")
        self.clean(orders)

        self._logger.debug("Generating new closed/wallet/proxy orders")
        closed_orders, proxy_orders, stable_orders = [], [], []

        for sell_order in tracked_orders:
            if sell_order.sell_trade.order_type != 'CryptoEventDTO':
                continue

            if sell_order.sell_trade.ticker in ['EUR', 'USD', 'USDT']:
                # process this later
                stable_orders.append(sell_order)
                continue

            closed_order = ExchangeClosedOrder(
                sell_order_id=sell_order.sell_trade.transaction_id,
                user_price=sell_order.sell_trade.price
            )
            closed_orders.append(closed_order)

            for buy_order in sell_order.buy_items:
                if not buy_order.trade:
                    self._logger.warning(f"Sell order without buy! "
                                         f"{buy_order.amount}{sell_order.sell_trade.ticker} at {sell_order.sell_trade.value_date}")
                    continue

                if sell_order.amount <= buy_order.amount:
                    try:
                        partial_fee = buy_order.fee / (buy_order.trade.amount / sell_order.amount)
                    except:
                        self._logger.warning(f"Calc of partial fee fails for {sell_order.sell_trade.ticker}. Buy fee: {buy_order.fee}. BUy amount: {buy_order.trade.amount}. Sell amount: {sell_order.amount}")
                        partial_fee = 0
                else:
                    try:
                        partial_fee = buy_order.fee / (sell_order.amount / buy_order.amount)
                    except:
                        # self._logger.warning(f"Amount is 0! When checking order {buy_order.amount}{sell_order.sell_trade.ticker}")
                        partial_fee = 0

                proxy_orders.append(ExchangeProxyOrder(
                    closed_order=closed_order,
                    order_id=buy_order.trade.transaction_id,
                    amount=buy_order.amount,
                    partial_fee=partial_fee,
                    user_price=buy_order.price  # in user base currency (€)
                ))

        ExchangeClosedOrder.bulk_save_objects(closed_orders)
        for proxy_order in proxy_orders:
            proxy_order.closed_order_id = proxy_order.closed_order.id

        ExchangeProxyOrder.bulk_save_objects(proxy_orders)

        self._logger.debug("Closed and proxy orders inserted correctly!")

    def calc_wallet(self, user_id, orders, queue, tracked_orders):
        """Calculate and store current crypto wallet state."""
        wallets = []

        # TODO: if no order.trade, probably means an unhandled deposit/withdrawal
        for ticker, partial_orders in queue.queues.items():
            amount = 0
            avg_price = 0
            total_cost = 0
            fees = 0
            open_orders = []

            for order in partial_orders:
                # self._logger.debug(f"{ticker} - Original: {order.original_trade.price}. Trade: {order.trade.price if order.trade else 0}. Price: {order.price}")
                if not order.trade:
                    # staking orders or unhandled order?
                    # can we check if its a staking?
                    self._logger.error(f"Order {ticker} without trade!")
                    # continue
                if amount == 0:
                    if order.amount == 0 or order.price == 0:
                        self._logger.error(f"Order {ticker} with amount or price 0!")
                        continue

                    amount += order.amount
                    avg_price = order.price
                    total_cost = amount * avg_price
                    fees = order.fee
                    if order.trade:
                        open_orders.append(ExchangeOpenOrder(order_id=order.trade.transaction_id, amount=order.amount, user_price=order.price))
                    continue

                avg_price = (amount * avg_price + order.amount * order.price) / (amount + order.amount)
                # TODO: calc average fee?
                amount += order.amount
                total_cost += order.price * order.amount  # * partial_order.trade.currency_rate
                fees += order.fee
                if order.trade:
                    open_orders.append(ExchangeOpenOrder(order_id=order.trade.transaction_id, amount=order.amount, user_price=order.price))

            if amount == 0:
                self._logger.info(f"Ticker {ticker} has 0 total amount, skipping.")
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
                price=avg_price,  # in $ # TODO: check if this is target currency or user base_currency €
                cost=total_cost,  # in base currency without fees
                benefits=current_benefits_eur,  # in €, in front we should sum fees
                break_even=break_even if break_even > 0 else 0,  # in base_currency
                fees=fees)
            w.open_orders.extend(open_orders)
            wallets.append(w)

        ExchangeOpenOrder.query.filter(ExchangeOpenOrder.order_id.in_([o.id for o in orders])).delete()
        ExchangeWallet.query.filter(ExchangeWallet.user_id == user_id).delete()
        ExchangeWallet.bulk_object(wallets)

        self._logger.info("Wallet calculation done")

    @staticmethod
    def calc_balance_with_orders(orders):
        """Return token balances from a set of orders."""
        balance = {}
        for order in sorted(orders, key=lambda x: x.value_date):
            if order.event_type == 'exchange_transaction':
                balance.setdefault(order.symbol, 0)
                if order.type in [CryptoEvent.Type.DEPOSIT, CryptoEvent.Type.STAKING, CryptoEvent.Type.AIRDROP]:
                    balance[order.symbol] += order.amount
                else:
                    balance[order.symbol] -= order.amount
                continue

            source, target = order.symbol.split("/")
            order.cost = getattr(order, "cost", round(order.amount * order.price, 8))

            for symbol in [source, target]:
                balance.setdefault(symbol, 0)

            if order.type == CryptoEvent.Type.BUY:
                balance[source] += order.amount
                balance[target] -= order.cost + order.fee
            else:
                balance[source] -= order.amount
                balance[target] += order.cost - order.fee

        return balance

    def check_benefits(self, queue, orders, tracked_orders):
        """Placeholder for calculating benefits."""
        pass

    def process_pending_transactions(self, queue, orders, tracked_orders):
        """(Optional) Debugging helper for unmatched withdrawals."""
        self._logger.warning("Testing deposits/withdrawals..")
        return
        withdrawals = queue.withdrawals
        for symbol, withdrawal in withdrawals.items():
            for wth in withdrawal:
                if wth.status == 'DEPOSITED':
                    self._logger.info(f"Deposit: {wth.amount}{wth.symbol} at {wth.value_date} to {wth.account.entity.name}. Fees: {wth.fee}")
                    continue

                self._logger.info(f"Pending withdrawal: {wth.amount}{wth.symbol} at {wth.value_date} from {wth.account.entity.name}")
                order = Transaction(Transaction.Type.SELL, wth, wth.symbol, wth.amount, 0, wth.fee)
                sell_order = queue.withdrawal_old(order)
                tracked_orders.append(sell_order)

    def get_balances(self, accounts):
        """Returns total balances for a user across all accounts."""
        balances = ExchangeBalance.query.options(joinedload(ExchangeBalance.account)).filter(
            ExchangeBalance.account_id.in_([a.id for a in accounts])
        ).all()

        currency_balances = {}
        for b in balances:
            currency_balances[b.currency] = currency_balances.get(b.currency, 0) + b.balance

        self._logger.info("Currency balances: ", currency_balances)
        return currency_balances
