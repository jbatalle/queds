
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
            "pair": self.pair,
            "value_date": self.value_date,
            "type": self.type,
            "price": self.price,
            "fee": self.fee,
            "amount": self.amount
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
        self.fee = 0

    def to_dict(self):
        d = {
            "account_id": self.account_id,
            "external_id": self.external_id,
            "currency": self.currency,
            "value_date": self.value_date,
            "type": self.type,
            "rx_address": self.rx_address,
            "fee": self.fee,
            "amount": self.amount
        }
        return d

