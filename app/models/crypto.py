import re
from datetime import datetime
from models.sql import Base, CRUD, db_session
from sqlalchemy import Column, Integer, String, UniqueConstraint, ForeignKey, Float, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import insert
from models.system import Account, User

# Regular expressions for validation
EMAIL_REGEX = re.compile(r'^\S+@\S+\.\S+$')
USERNAME_REGEX = re.compile(r'^\S+$')


class ExchangeBalance(Base, CRUD):
    """
    Represents the balances extracted directly from the exchange.
    """
    __tablename__ = 'exchange_balance'
    __table_args__ = (UniqueConstraint('account_id', 'currency', name='_account_currency_unique'),)

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    currency = Column(String(10))
    balance = Column(Float)  # Balance in the specified currency
    update_date = Column(DateTime, nullable=False, default=datetime.now)

    @classmethod
    def bulk_insert(cls, transactions: list):
        """
        Bulk insert or update exchange balances.

        :param transactions: List of balance transactions to insert or update.
        """
        if not transactions:
            return

        insert_statement = insert(cls).values(transactions)
        constraint_columns = {col.name for c in cls.__table__.constraints for col in c.columns}

        update_dict = {c.name: c for c in insert_statement.excluded if c.name not in constraint_columns}
        db_session.execute(insert_statement.on_conflict_do_update(
            constraint="_account_currency_unique",
            set_=update_dict,
        ))


class CryptoEvent(Base, CRUD):
    """
    Stores all crypto events as defined by each exchange.
    """
    __tablename__ = 'crypto_events'
    __table_args__ = (UniqueConstraint('account_id', 'external_id', name='_crypto_event_account_id_external_id'),)

    class Type:
        BUY = 0
        SELL = 1
        DEPOSIT = 2
        WITHDRAWAL = 3
        CASH_IN = 4
        CASH_OUT = 5
        STAKING = 6
        AIRDROP = 7

    id = Column(Integer, primary_key=True)
    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account = relationship("Account")
    external_id = Column(String(70))
    value_date = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    symbol = Column(String(150))
    amount = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    event_type = Column(String(50))  # Discriminator column
    type = Column(Integer)
    status = Column(String(150))
    tx_address = Column(String(200))
    rx_address = Column(String(200))

    @classmethod
    def bulk_insert(cls, orders: list):
        """
        Bulk insert crypto events.

        :param orders: List of crypto events to insert.
        """
        if not orders:
            return

        db_session.execute(insert(cls).values(orders).on_conflict_do_nothing())

    def to_dict(self):
        """
        Convert the crypto event to a dictionary representation.

        :return: Dictionary representation of the event.
        """
        return {
            "id": self.id,
            "external_id": self.external_id,
            "type": self.type,
            "account_id": self.account_id,
            "account": self.account.name,
            "value_date": self.value_date.strftime("%Y-%m-%d %H:%M:%S"),
            "symbol": self.symbol,
            "price": self.price,
            "amount": self.amount,
            "fee": self.fee
        }


class ExchangeWallet(Base, CRUD):
    """
    Represents real-time balance of users by currency. Its calculated using FIFO
    Ideally these entries should be equal than ExchangeBalance
    """
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

        db_session.execute(insert(cls).values(items).on_conflict_do_nothing())

    @classmethod
    def bulk_object(cls, objects: list):
        db_session.add_all(objects)
        db_session.flush()


class ExchangeProxyOrder(Base, CRUD):
    """
    Links a sell order to multiple buy orders (proportional matching).
    """
    __tablename__ = 'exchange_proxy_orders'

    id = Column(Integer, primary_key=True)
    closed_order_id = Column(Integer, ForeignKey('exchange_closed_orders.id'))
    closed_order = relationship("ExchangeClosedOrder", back_populates="buy_order")

    order = relationship("CryptoEvent")
    order_id = Column(Integer, ForeignKey('crypto_events.id', ondelete="CASCADE"))
    amount = Column(Float)  # amount for each order
    partial_fee = Column(Float)
    user_price = Column(Float) # sell price at user currency

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        db_session.bulk_save_objects(orders)
        db_session.flush()


class ExchangeClosedOrder(Base, CRUD):
    """
    Represents completed sell orders, including matched buys.
    """
    __tablename__ = 'exchange_closed_orders'

    id = Column(Integer, primary_key=True)
    sell_order = relationship("CryptoEvent")
    sell_order_id = Column(Integer, ForeignKey('crypto_events.id', ondelete="CASCADE"))
    user_price = Column(Float)  # price of the sell at user currency - €/$
    buy_order = relationship("ExchangeProxyOrder", back_populates="closed_order")

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        a = db_session.bulk_save_objects(orders, return_defaults=True)
        db_session.flush()


class ExchangeOpenOrder(Base, CRUD):
    """
    Represents the buy orders that are still open.
    """
    __tablename__ = 'exchange_open_orders'

    id = Column(Integer, primary_key=True)
    wallet_id = Column(Integer, ForeignKey('exchange_wallet.id'))

    order = relationship("CryptoEvent")
    order_id = Column(Integer, ForeignKey('crypto_events.id', ondelete="CASCADE"))
    amount = Column(Float)  # pending amount
    user_price = Column(Float)  # price at user currency - €/$

    exchange_id = Column(Integer, ForeignKey('accounts.id'))
    exchange = relationship("Account")  # optional


class ExchangeTaxSummary(Base, CRUD):
    __tablename__ = 'exchange_tax_summaries'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    currency = Column(String(20))
    year = Column(Integer)
    total_proceeds = Column(Float)  # EUR
    total_cost_basis = Column(Float)  # EUR
    total_gain_loss = Column(Float)  # EUR
    total_fees = Column(Float)  # EUR
    num_trades = Column(Integer)
    generated_at = Column(DateTime, default=datetime.now)


class CryptoPrice(Base, CRUD):
    """
    Represents the price of a cryptocurrency at a specific timestamp.
    """
    __tablename__ = 'crypto_price'

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    source = Column(String(150))  # Source currency (e.g., BTC)
    target = Column(String(150))  # Target currency (e.g., USD)
    price = Column(Float)  # Price of the source currency in terms of the target currency


class TransactionLog(Base, CRUD):
    """
    Logs various transaction-related events and errors.
    """
    __tablename__ = 'transaction_logs'

    LOG_TYPES = {
        'unmatched_sell': "Unmatched Sell",
        'partial_fee_error': "Fee Calculation Error",
        'negative_balance': "Negative Balance Detected",
        'deposit_without_withdrawal': "Deposit Without Matching Withdrawal",
        'withdrawal_without_deposit': "Withdrawal Not Matched",
        'invalid_order': "Invalid Order Data",
        'rate_lookup_failure': "Failed to Find Price Rate"
    }

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    account_id = Column(Integer, ForeignKey('accounts.id'), nullable=True)
    sell_event_id = Column(Integer, ForeignKey('crypto_events.id'), nullable=True)
    buy_event_id = Column(Integer, ForeignKey('crypto_events.id'), nullable=True)
    log_type = Column(String(50))  # Type of log (e.g., 'unmatched_sell')
    message = Column(Text)
    comment = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    # relationship("ExchangeProxyOrder", back_populates="closed_order")
    #user = relationship("User", foreign_keys=[user_id])
    #account = relationship("Account", foreign_keys=[account_id])
    account = relationship("Account")
    # sell_event = relationship("CryptoEvent")
    # buy_event = relationship("CryptoEvent", back_populates=buy_event_id)
    sell_event = relationship("CryptoEvent", foreign_keys=[sell_event_id])
    buy_event = relationship("CryptoEvent", foreign_keys=[buy_event_id])

    @classmethod
    def bulk_save_objects(cls, orders):
        if len(orders) == 0:
            return

        a = db_session.bulk_save_objects(orders, return_defaults=True)
        db_session.flush()

    @classmethod
    def log(cls, user_id, message, log_type, account_id=None, sell_event_id=None, buy_event_id=None):
        """
        Create a new transaction log entry.

        :param user_id: ID of the user associated with the log.
        :param message: Log message.
        :param log_type: Type of log.
        :param account_id: (Optional) Account ID associated with the log.
        :param sell_event_id: (Optional) Sell event ID associated with the log.
        :param buy_event_id: (Optional) Buy event ID associated with the log.
        :return: The created log entry.
        """
        log_entry = cls(
            user_id=user_id,
            account_id=account_id,
            sell_event_id=sell_event_id,
            buy_event_id=buy_event_id,
            log_type=log_type,
            message=message
        )
        db_session.add(log_entry)
        db_session.flush()
        return log_entry

