import re
from datetime import datetime
from models.sql import Base, CRUD, db_session
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Float, Date, DateTime
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
    __table_args__ = (UniqueConstraint('account_id', 'currency', name='_account_currency_unique'),)

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    currency = Column(String(10))
    balance = Column(Float)  # according to currency
    update_date = Column(DateTime, nullable=False, default=datetime.now)

    @classmethod
    def bulk_insert(cls, transactions: list):
        if len(transactions) == 0:
            return

        insert_statement = insert(cls).values(transactions)
        constraint_columns = set()
        for c in [c for c in cls.__table__.constraints]:
            for col in c.columns:
                constraint_columns.add(col.name)

        # Updated fields will get their specified value
        update_dict = {c.name: c for c in insert_statement.excluded if c.name not in constraint_columns}
        db_session.execute(insert_statement.on_conflict_do_update(
            constraint="_account_currency_unique",
            set_=update_dict,
        ))


class ExchangeOrder(Base, CRUD):

    __tablename__ = 'exchange_orders'

    class Type:
        BUY = 0
        SELL = 1

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70), unique=True)
    value_date = Column(DateTime, nullable=False, default=datetime.now)
    pair = Column(String(150))
    amount = Column(Float)
    type = Column(Integer)
    price = Column(Float)  # according to currency
    fee = Column(Float)  # according to currency

    @classmethod
    def bulk_insert(cls, orders: list):
        if len(orders) == 0:
            return

        q = db_session.execute(insert(cls).values(orders).on_conflict_do_nothing())

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
    value_date = Column(DateTime, nullable=False, default=datetime.now)
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

    @classmethod
    def get_type(cls, type):
        return {v: n for n, v in vars(ExchangeTransaction.Type).items() if n.isupper()}[type]


class ExchangeWallet(Base, CRUD):
    __tablename__ = 'exchange_wallet'

    id = Column(Integer, primary_key=True)
    currency = Column(String(10))
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)  # owned shares
    price = Column(Float)  # average price
    cost = Column(Float)  # total cost without fees in ticker currency
    break_even = Column(Float)  # in ticker currency with fees
    benefits = Column(Float)  # in €, in front we should sum fees
    fees = Column(Float)
    open_orders = relationship("ExchangeOpenOrder")

    @classmethod
    def bulk_insert(cls, items: list):
        if len(items) == 0:
            return

        q = db_session.execute(insert(cls).values(items).on_conflict_do_nothing())

    @classmethod
    def bulk_object(cls, objects: list):
        db_session.add_all(objects)
        db_session.flush()


class ExchangeProxyOrder(Base, CRUD):
    __tablename__ = 'exchange_proxy_orders'

    id = Column(Integer, primary_key=True)
    closed_order_id = Column(Integer, ForeignKey('exchange_closed_orders.id'))
    closed_order = relationship("ExchangeClosedOrder", back_populates="buy_order")

    order = relationship("ExchangeOrder")
    order_id = Column(Integer, ForeignKey('exchange_orders.id', ondelete="CASCADE"))
    amount = Column(Float)  # amount for each order
    partial_fee = Column(Float)


    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        db_session.bulk_save_objects(orders)
        db_session.flush()
        #db_session.add_all(tracked_orders)
        #db_session.flush()

class ExchangeClosedOrder(Base, CRUD):
    __tablename__ = 'exchange_closed_orders'

    id = Column(Integer, primary_key=True)
    sell_order = relationship("ExchangeOrder")
    sell_order_id = Column(Integer, ForeignKey('exchange_orders.id', ondelete="CASCADE"))
    # buy_order = relationship("ExchangeProxyOrder")
    buy_order = relationship("ExchangeProxyOrder", back_populates="closed_order")


    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        db_session.bulk_save_objects(orders)
        db_session.flush()
        #db_session.add_all(tracked_orders)
        #db_session.flush()


class ExchangeOpenOrder(Base, CRUD):
    __tablename__ = 'exchange_open_orders'

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('exchange_wallet.id'))

    order = relationship("ExchangeOrder")
    order_id = Column(Integer, ForeignKey('exchange_orders.id', ondelete="CASCADE"))
    amount = Column(Integer)  # pending amount
