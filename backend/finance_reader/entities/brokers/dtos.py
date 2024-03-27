
class Ticker:

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    def __init__(self):
        self.isin = ''
        self.name = None
        self.active = True
        self.exchange = None

    def __str__(self):
        return f"{self.name}-{self.isin}-{'inactive' if self.active else 'active'}"


class BrokerAccount:
    def __init__(self):
        self.name = None
        self.account_id = ''
        self.currency = ''
        self.entity_id = ''
        self.balance = 0
        self.virtual_balance = 0


class Transaction:

    class Type:
        BUY = 0
        SELL = 1
        REVERSE_SPLIT_BUY = 2
        REVERSE_SPLIT_SELL = 3

    def __init__(self):
        self.name = ''
        self.value_date = None
        self.external_id = 0
        self.ticker = None
        self.shares = 0
        self.type = 0
        self.currency = 'EUR'
        self.price = 0
        self.fee = 0
        self.exchange_fee = 0
        self.currency_rate = 1

    def __str__(self):
        return f"{self.name}-{self.ticker.ticker}-{self.shares}-{self.price}"

    def to_dict(self):
        d = {
            "name": self.name,
            "value_date": self.value_date,
            "external_id": self.external_id,
            # "ticker": self.ticker,
            "shares": self.shares,
            "type": self.type,
            "price": self.price,
            "fee": self.fee,
            "exchange_fee": self.exchange_fee,
            "currency_rate": self.currency_rate,
            "currency": self.currency
            }
        return d
