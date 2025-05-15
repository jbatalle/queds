
class ExchangeWallet:
    def __init__(self):
        self.account_id = None
        self.currency = None
        self.balance = None

    def to_dict(self):
        d = {
            "account_id": self.account_id,
            "currency": self.currency,
            "balance": self.balance
        }
        return d


class OrderType:
    BUY = 0
    SELL = 1
    DEPOSIT = 2
    WITHDRAWAL = 3
    CASH_IN = 4
    CASH_OUT = 5
    STAKING = 6
    AIRDROP = 7


class Order:
    def __init__(self):
        self.account_id = None
        self.external_id = None
        self.pair = None
        self.value_date = None
        self.type = None
        self.price = None
        self.amount = None
        self.fee = None

    def to_dict(self):
        d = {
            "account_id": self.account_id,
            "external_id": self.external_id,
            "symbol": self.pair,
            "value_date": self.value_date,
            "type": self.type,
            "price": self.price,
            "fee": self.fee,
            "amount": self.amount,
            "event_type": "exchange_order"
        }
        return d


class Transaction:
    def __init__(self):
        self.account_id = None
        self.external_id = 0
        self.value_date = None
        self.amount = 0
        self.type = 0
        self.currency = None
        self.rx_address = 0
        self.tx_address = 0
        self.fee = 0

    def to_dict(self):
        d = {
            "account_id": self.account_id,
            "external_id": self.external_id,
            "symbol": self.currency,
            "value_date": self.value_date,
            "type": self.type,
            "rx_address": self.rx_address,
            "tx_address": self.tx_address,
            "fee": self.fee,
            "amount": self.amount,
            "event_type": "exchange_transaction",
            "price": 0
        }
        return d

class CryptoEventDTO:
    def __init__(self):
        self.account_id = None
        self.external_id = None
        self.value_date = None
        self.symbol = None
        self.amount = None
        self.price = None
        self.fee = None

        self.event_type = None
        self.type = None
        
        self.status = None
        self.rx_address = None
        self.tx_address = None

    def to_dict(self):
        d = {
            "account_id": self.account_id,
            "external_id": self.external_id,
            "value_date": self.value_date,
            "symbol": self.symbol,
            "amount": self.amount,
            "price": self.price,
            "fee": self.fee,
            "event_type": self.event_type,
            "type": self.type,
            "rx_address": self.rx_address,
            "tx_address": self.tx_address
        }
        return d