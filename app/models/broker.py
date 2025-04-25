from models.sql import Base, CRUD, db_session
from datetime import datetime
from models.system import Account, User
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Float, Date, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import insert


class StockTransaction(Base, CRUD):

    __tablename__ = 'stock_transactions'
    __table_args__ = (UniqueConstraint('account_id', 'external_id', name='_account_id_external_id'),)

    class Type:
        BUY = 0
        SELL = 1
        SPLIT_BUY = 2
        SPLIT_SELL = 3
        OTC_BUY = 4
        OTC_SELL = 5
        SPIN_OFF_BUY = 6
        SPIN_OFF_SELL = 7

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70))
    value_date = Column(TIMESTAMP, nullable=False, default=datetime.now)
    name = Column(String(150))
    ticker_id = Column(Integer, ForeignKey('tickers.id'))
    ticker = relationship("Ticker")
    shares = Column(Integer)
    type = Column(Integer)
    currency = Column(String(5))  # duplicated, should be extracted from ticker
    price = Column(Float)  # according to currency
    fee = Column(Float)  # in €
    exchange_fee = Column(Float)  # in €
    currency_rate = Column(Float)

    def __str__(self):
        return f"{self.ticker_id}-{self.ticker.name}-{self.shares}@{self.price}"

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())

    def to_dict(self):
        d = {
            "id": self.id,
            "external_id": self.external_id,
            "type": self.type,
            "account_id": self.account_id,
            "account": self.account.name,
            "value_date": self.value_date.strftime("%Y-%m-%d %H:%M:%S"),
            "name": self.name,
            "ticker": self.ticker,
            "currency": self.currency,
            "price": self.price,
            "shares": self.shares,
            "fee": self.fee,
            "exchange_fee": self.exchange_fee,
            "currency_rate": self.currency_rate
            }
        return d


class Wallet(Base, CRUD):
    __tablename__ = 'stock_wallet'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    ticker_id = Column(Integer, ForeignKey('tickers.id'))
    ticker = relationship('Ticker')
    shares = Column(Integer)  # owned shares
    price = Column(Float)  # average price
    cost = Column(Float)  # total cost without fees in ticker currency
    break_even = Column(Float)  # in ticker currency with fees
    benefits = Column(Float)  # in €, in front we should sum fees
    fees = Column(Float)
    open_orders = relationship("OpenOrder")
    # open_orders = relationship("OpenOrder", cascade="all,delete", backref="wallet")

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())

    @classmethod
    def bulk_object(cls, objects: list):
        db_session.add_all(objects)
        db_session.flush()


class Taxes():
    __tablename__ = 'stock_taxes'

    id = Column(Integer, primary_key=True)
    ticker = Column(Integer, ForeignKey('tickers.id'))
    benefits = Column(Float)


class OpenOrder(Base, CRUD):
    __tablename__ = 'stock_open_orders'

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('stock_wallet.id'))

    transaction = relationship("StockTransaction")
    transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    shares = Column(Integer)  # pending shares
    price = Column(Float)  # price at transaction currency
    currency_rate = Column(Float)


class ProxyOrder(Base, CRUD):
    __tablename__ = 'stock_proxy_orders'

    id = Column(Integer, primary_key=True)
    closed_order = relationship("ClosedOrder")
    closed_order_id = Column(Integer, ForeignKey('stock_closed_orders.id'))

    transaction = relationship("StockTransaction")
    transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    shares = Column(Integer)  # shares for each transaction
    price = Column(Float)
    partial_fee = Column(Float)

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        db_session.bulk_save_objects(orders)
        db_session.flush()


class ClosedOrder(Base, CRUD):
    __tablename__ = 'stock_closed_orders'

    id = Column(Integer, primary_key=True)
    sell_transaction = relationship("StockTransaction")
    sell_transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    buy_transaction = relationship("ProxyOrder", back_populates='closed_order')
    #shares = Column(Integer)  # in case of R/S, some shares can be sold depending on the ratio
    #price = Column(Float)
    #currency_rate = Column(Float)

    def __str__(self):
        return f"{self.sell_transaction.name}-{self.sell_transaction.shares}@{self.sell_transaction.price}"

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        a = db_session.bulk_save_objects(orders, return_defaults=True)
        db_session.flush()


class Ticker(Base, CRUD):
    __tablename__ = 'tickers'
    __table_args__ = (UniqueConstraint('ticker', 'isin', name='_ticker_isin_unique'),)

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(8), nullable=False)
    name = Column(String(150))
    currency = Column(String(5))
    isin = Column(String(50))
    ticker_yahoo = Column(String(10))
    # trading_view = Column(String(10))
    status = Column(Integer, default=Status.ACTIVE)
    market = Column(String(50))
    previous_ticker = Column(Integer, ForeignKey('tickers.id'), nullable=True)

    def __str__(self):
        return f"{self.id}-{self.ticker}-{self.name}"

    def get_currency(self):
        if self.currency == 'USD':
            return '$'
        elif self.currency == 'EUR':
            return '€'

        return self.currency

    def to_dict(self):
        d = {
            "id": self.id,
            "name": self.name,
            "ticker": self.ticker,
            "currency": self.currency,
            "isin": self.isin,
            "ticker_yahoo": self.ticker_yahoo,
            "status": self.status,
            "market": self.market
            }
        if not self.id:
            del d['id']
        return d

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        a = db_session.bulk_save_objects(transactions, return_defaults=True)
        db_session.flush()
        return

        not_registered_tickers = [t.to_dict() for t in transactions if not t.id]
        registered_tickers = [t.to_dict() for t in transactions if t.id]
        if not_registered_tickers:
            q = db_session.execute(insert(cls).values(not_registered_tickers).on_conflict_do_update(
                index_elements=['ticker', 'isin', 'status'],
                set_={
                    "status": cls.status
                }))

        if registered_tickers:
            stmt = insert(cls).values(registered_tickers)
            update_cols = ["status"]

            b = db_session.execute(stmt.on_conflict_do_update(
                constraint='tickers_pkey',
                set_={k: getattr(stmt.excluded, k) for k in update_cols}
            ))
            #
            # db_session.execute(insert(cls).values().on_conflict_do_update(
            #     constraint='tickers_pkey',
            #     set_={
            #         "status": cls.status
            #     }))

        db_session.flush()


class StockPrice(Base, CRUD):
    __tablename__ = 'stock_prices'
    # _name = _timestamp_ticker for mysql
    __table_args__ = (UniqueConstraint('timestamp', 'ticker', name='_timestamp_ticker_unique'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(TIMESTAMP, nullable=False)
    ticker = Column(Integer, ForeignKey('tickers.id'))
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    open = Column(Float)
    close = Column(Float)
    pre = Column(Float)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())


class Currency(Base, CRUD):
    __tablename__ = 'currency'
    __table_args__ = (UniqueConstraint('timestamp', 'pair', name='_timestamp_ticker'),)

    id = Column(Integer, primary_key=True)
    timestamp = Column(Integer)
    pair = Column(String(10))
    high = Column(Float)
    low = Column(Float)
    volume = Column(Float)
    open = Column(Float)
    close = Column(Float)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())


class CrowdTransaction(Base, CRUD):
    __tablename__ = 'crowd_transaction'

    class Type:
        FUND = 0
        INVEST = 1
        RETURN = 2
        FUTURE_RETURN = 3

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id'))
    account = relationship("Account")
    external_id = Column(String(70), unique=True)
    value_date = Column(Date, nullable=False, default=datetime.now)
    type = Column(Integer, nullable=False)
    amount = Column(Float)
    interest = Column(Float)
    project_id = Column(String(70))
    tax = Column(Float)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())


class Watchlists(Base, CRUD):
    __tablename__ = 'watchlists'
    __table_args__ = (UniqueConstraint('user_id', 'name', name='_watchlist_user_id_name_unique'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(150))
    # watchlist = Column(Integer, ForeignKey('watchlist.id'))


class Watchlist(Base, CRUD):
    __tablename__ = 'watchlist'
    # _name = _timestamp_ticker for mysql
    __table_args__ = (UniqueConstraint('watchlists', 'ticker', name='_watchlist_ticker_unique'),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    watchlists = Column(Integer, ForeignKey('watchlists.id'))
    ticker = Column(Integer, ForeignKey('tickers.id'))
    high = Column(Float)
    low = Column(Float)


class SplitOrder(Base, CRUD):
    __tablename__ = 'reverse_split_orders'

    id = Column(Integer, primary_key=True)
    buy_transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    sell_transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))

    buy_transaction = relationship("StockTransaction", foreign_keys=[buy_transaction_id])
    sell_transaction = relationship("StockTransaction", foreign_keys=[sell_transaction_id])

    ratio = Column(Integer)
    price = Column(Float)
    shares = Column(Integer)  # original shares
    new_shares = Column(Integer)  # new shares

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        db_session.bulk_save_objects(orders)
        db_session.flush()
