
class Ticker:

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    def __init__(self):
        self.isin = ''
        self.ticker = None
        self.name = None
        self.active = True
        self.exchange = None

    def __str__(self):
        return f"{self.ticker}-{self.isin}-{self.name}-{'inactive' if self.active else 'active'}"


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
        SPLIT_BUY = 2
        SPLIT_SELL = 3
        OTC_BUY = 4
        OTC_SELL = 5
        SPIN_OFF_BUY = 6
        SPIN_OFF_SELL = 7
        SCRIPT_DIVIDEND = 8

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
        return f"{self.value_date}-{self.ticker.ticker}-{self.shares}@{self.price}-{self.name}"

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
