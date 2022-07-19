import re
from datetime import datetime
from models.sql import Base, CRUD, db_session
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Float, Date
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import insert
from models.system import Account, User


EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')
USERNAME_REGEX = re.compile(r'^\S+$')


class Pair():
    __tablename__ = 'pair'
    __table_args__ = (UniqueConstraint('pair', 'status', name='_pair_status_unique'),)

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    id = Column(Integer, primary_key=True, autoincrement=True)
    pair = Column(String(8), nullable=False)
    name = Column(String(150))
    currency = Column(String(5))
    isin = Column(String(50))
    ticker_yahoo = Column(String(10))
    status = Column(Integer, default=Status.ACTIVE)


class ExchangeBalance(Base, CRUD):
    __tablename__ = 'exchange_balance'

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    currency = Column(String(10))
    balance = Column(Float)  # according to currency
    update_date = Column(Date, nullable=False, default=datetime.now)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())


class ExchangeOrder(Base, CRUD):

    __tablename__ = 'exchange_orders'

    class Type:
        BUY = 0
        SELL = 1

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70), unique=True)
    value_date = Column(Date, nullable=False, default=datetime.now)
    pair = Column(String(150))
    amount = Column(Float)
    type = Column(Integer)
    price = Column(Float)  # according to currency
    fee = Column(Float)  # according to currency

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())

    def to_dict(self):
        # TODO
        d = {
            "id": self.id,
            "external_id": self.external_id,
            "type": self.type,
            "account_id": self.account_id,
            "account": self.account.name,
            "value_date": self.value_date.strftime("%Y-%m-%d %H:%M:%S"),
            "pair": self.pair,
            "price": self.price,
            "amount": self.amount,
            "fee": self.fee,
            # "exchange_fee": self.exchange_fee,
            # "currency_rate": self.currency_rate
            }
        return d


class ExchangeTransaction(Base, CRUD):

    __tablename__ = 'exchange_transactions'

    class Type:
        DEPOSIT = 2
        WITHDRAWAL = 3
        CASH_IN = 4
        CASH_OUT = 5

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70), unique=True)
    value_date = Column(Date, nullable=False, default=datetime.now)
    currency = Column(String(10))
    amount = Column(Float)
    fee = Column(Float)  # according to currency
    status = Column(Integer)
    type = Column(Integer)
    tx_address = Column(String(200))
    rx_address = Column(String(200))

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())


class ExchangeWallet(Base, CRUD):
    __tablename__ = 'exchange_wallet'

    class Type:
        BANK = 0
        BROKER = 1
        CROWD = 2

    id = Column(Integer, primary_key=True)
    currency = Column(String(10))
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)  # owned shares
    price = Column(Float)  # average price
    cost = Column(Float)  # total cost without fees in ticker currency
    break_even = Column(Float)  # in ticker currency with fees
    benefits = Column(Float)  # in €, in front we should sum fees
    fees = Column(Float)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        q = db_session.execute(insert(cls).values(transactions).on_conflict_do_nothing())

    @classmethod
    def bulk_object(cls, objects: list):
        db_session.add_all(objects)
        db_session.flush()


class ExchangeProxyOrder(Base, CRUD):
    __tablename__ = 'exchange_proxy_orders'

    id = Column(Integer, primary_key=True)
    closed_order_id = Column(Integer, ForeignKey('exchange_closed_orders.id'))

    transaction = relationship("ExchangeOrder")
    transaction_id = Column(Integer, ForeignKey('exchange_orders.id', ondelete="CASCADE"))
    shares = Column(Float)  # shares for each transaction
    partial_fee = Column(Float)


class ExchangeClosedOrder(Base, CRUD):
    __tablename__ = 'exchange_closed_orders'

    id = Column(Integer, primary_key=True)
    sell_transaction = relationship("ExchangeOrder")
    sell_transaction_id = Column(Integer, ForeignKey('exchange_orders.id', ondelete="CASCADE"))
    buy_transaction = relationship("ExchangeProxyOrder")
