from wallet_processor.entities import AbstractEntity
from models.system import Account, Entity
from models.broker import StockTransaction, Wallet, ClosedOrder, OpenOrder, Ticker, ProxyOrder
from wallet_processor.utils import BalanceQueue, Transaction


class BrokerProcessor(AbstractEntity):

    def __init__(self):
        super(BrokerProcessor, self).__init__()

    @staticmethod
    def clean(transactions):
        ProxyOrder.query.filter(ProxyOrder.transaction_id.in_([t.id for t in transactions])).delete()
        ClosedOrder.query.filter(ClosedOrder.sell_transaction_id.in_([t.id for t in transactions])).delete()

    @staticmethod
    def get_orders(user_id):
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.BROKER)).all()
        transactions = StockTransaction.query.filter(
            StockTransaction.account_id.in_([a.id for a in accounts])).order_by(
            StockTransaction.value_date.asc(), StockTransaction.type.asc()).all()
        return transactions

    def trade(self, queue, order):
        sell_items = None
        fees = order.fee + order.exchange_fee
        if order.shares == 0:
            return None
        if order.type == StockTransaction.Type.BUY:
            order = Transaction(order.id, Transaction.Type.BUY, order.value_date, order.ticker, order.shares, order.price, fees, order.currency_rate)
            queue.buy(order)
            # ticker_transactions[t.ticker]["open"].append(OpenOrder(t))
        else:
            order = Transaction(order.id, Transaction.Type.SELL, order.value_date, order.ticker, order.shares, order.price, fees, order.currency_rate)
            sell_items = queue.sell(order)
            # ticker_transactions[t.ticker]["closed"].extend(sell_items)

        return sell_items

    def calc_wallet(self, user_id, orders, queue, tracked_orders):
        self._logger.info("Cleaning closed/wallet/proxy orders")
        self.clean(orders)

        self._logger.info("Generating new closed/wallet/proxy orders")
        for sell_order in tracked_orders:
            closed_order = ClosedOrder(sell_transaction_id=sell_order.sell_trade.transaction_id)
            closed_order.save()
            for buy_order in sell_order.buy_items:
                if not buy_order.trade:
                    self._logger.warning("Some strange case!")
                    continue

                if sell_order.amount <= buy_order.amount:
                    partial_fee = buy_order.fee / (buy_order.trade.amount / sell_order.amount)
                else:
                    partial_fee = buy_order.fee / (sell_order.amount / buy_order.amount)
                ProxyOrder(
                    closed_order_id=closed_order.id,
                    transaction_id=buy_order.trade.transaction_id,
                    shares=buy_order.amount,
                    partial_fee=partial_fee
                ).save()

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
                    open_orders.append(
                        OpenOrder(
                            transaction_id=order.trade.transaction_id,
                            shares=shares))
                    continue
                avg_price = (shares * avg_price + order.amount * order.price) / (shares + order.amount)
                # TODO: calc average fee?
                shares += order.amount
                total_cost += order.price * order.amount  # * partial_order.trade.currency_rate
                fees += order.fee

                open_orders.append(
                    OpenOrder(
                        transaction_id=order.trade.transaction_id,
                        shares=order.amount))

            # Calculate current benefits taking into account sells
            current_benefits = 0
            current_benefits_eur = 0
            total_sell = 0
            for order in [w for w in tracked_orders if w.sell_trade.ticker == ticker]:
                current_benefits += order.benefits
                current_benefits_eur += order.benefits_in_eur
                total_sell += order.sell_trade.price * order.amount * order.sell_trade.currency_rate
                fees += order.sell_trade.fees
            #    opered_transactions.append(order.trade)
            #    opered_transactions.append(order.open_order)

            # current_benefits += 0  # fees??

            if shares == 0:
                self._logger.info(f"Shares is 0 for ticker {ticker}!")
                continue

            break_even = (total_cost - total_sell) / shares
            if not ticker:
                self._logger.error("Ticker not found!")
                continue
            w = Wallet(
                ticker_id=ticker.id,
                user_id=user_id,
                shares=shares,
                price=avg_price,  # in $
                cost=total_cost,  # in base currency without fees
                benefits=current_benefits_eur,  # in €, in front we should sum fees
                break_even=break_even if break_even > 0 else 0,  # in base_currency
                fees=fees)
            w.open_orders.extend(open_orders)
            to_insert.append(w)

        OpenOrder.query.filter(OpenOrder.transaction_id.in_([t.id for t in orders])).delete()

        Wallet.query.delete()
        Wallet.bulk_object(to_insert)
        self._logger.info("Wallet calculation done")

    @staticmethod
    def calc_balance_with_orders(self):
        return {}
