from models.sql import Base, CRUD, db_session
from datetime import datetime
from models.system import Account, User
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Float, Date, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import insert


class StockTransaction(Base, CRUD):

    __tablename__ = 'stock_transactions'

    class Type:
        BUY = 0
        SELL = 1

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70), unique=True)
    value_date = Column(Date, nullable=False, default=datetime.now)
    name = Column(String(150))
    ticker_id = Column(Integer, ForeignKey('tickers.id'))
    ticker = relationship("Ticker")
    shares = Column(Integer)
    type = Column(Integer)
    currency = Column(String(5))
    price = Column(Float)  # according to currency
    fee = Column(Float)  # according to currency
    exchange_fee = Column(Float)  # in €
    currency_rate = Column(Float)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        # insert_command = cls.__table__.insert().prefix_with(' IGNORE').values(transactions)
        # db_session.execute(insert_command)
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


class ProxyOrder(Base, CRUD):
    __tablename__ = 'stock_proxy_orders'

    id = Column(Integer, primary_key=True)
    closed_order_id = Column(Integer, ForeignKey('stock_closed_orders.id'))

    transaction = relationship("StockTransaction")
    transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    shares = Column(Integer)  # shares for each transaction
    partial_fee = Column(Float)


class ClosedOrder(Base, CRUD):
    __tablename__ = 'stock_closed_orders'

    id = Column(Integer, primary_key=True)
    sell_transaction = relationship("StockTransaction")
    sell_transaction_id = Column(Integer, ForeignKey('stock_transactions.id', ondelete="CASCADE"))
    buy_transaction = relationship("ProxyOrder")

    def __str__(self):
        return f"{self.sell_transaction.name}-{self.sell_transaction.shares}@{self.sell_transaction.price}"


class Ticker(Base, CRUD):
    __tablename__ = 'tickers'
    __table_args__ = (UniqueConstraint('ticker', 'isin', 'status', name='_ticker_isin_status_unique'),)

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    ticker = Column(String(8), nullable=False)
    name = Column(String(150))
    currency = Column(String(5))
    isin = Column(String(50))
    ticker_yahoo = Column(String(10))
    status = Column(Integer, default=Status.ACTIVE)

    def __str__(self):
        return self.name

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
            "currency": self.get_currency(),
            "isin": self.isin,
            "ticker_yahoo": self.ticker_yahoo,
            "status": self.status
            }
        return d


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

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    name = Column(String(150), unique=True)
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
