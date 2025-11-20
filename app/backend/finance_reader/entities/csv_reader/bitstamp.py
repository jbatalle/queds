from finance_reader.entities.csv_reader import ExchangeCSVProcessor
from models.dtos.exchange_dtos import Order, Transaction, OrderType
from datetime import datetime


class Bitstamp(ExchangeCSVProcessor):

    def __init__(self):
        super(Bitstamp, self).__init__()

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Bitstamp CSV file for account {account.id}")
        lines = csv_data.splitlines()
        headers = lines[0].split(",")

        orders = []
        transactions = []
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))
            if data.get('Type') in ('Deposit', 'Withdrawal'):
                trans = self.create_transaction(account, data)
                if trans:
                    transactions.append(trans)
            else:
                order = self.create_order(account, data)
                if order:
                    orders.append(order)

        return orders, transactions

    def create_order(self, account, data):
        type = None
        if data.get('Subtype') == 'Sell':
            type = OrderType.SELL
        elif data.get('Subtype') == 'Buy':
            type = OrderType.BUY

        if type == None:
            self.log.error(f"Unknown order type: {data.get('Type')} - {data.get('Subtype')}")
            return None

        order = Order()
        order.account_id = account.id
        order.external_id = data.get("ID")
        order.value_date = datetime.strptime(data.get("Datetime"), "%Y-%m-%dT%H:%M:%SZ")
        order.pair = data.get("Amount currency") + "/" + data.get("Value currency")
        order.amount = float(data.get("Amount"))
        order.type = type
        order.price = float(data.get("Rate"))
        order.fee = float(data.get("Fee") or 0)
        return order

    def create_transaction(self, account, data):
        type = None
        if data.get('Type') == 'Deposit':
            type = OrderType.DEPOSIT
        elif data.get('Type') == 'Withdrawal':
            type = OrderType.WITHDRAWAL

        if not type:
            self.log.error(f"Unknown transaction type: {data.get('Type')} - {data.get('Subtype')}")
            return None

        trans = Transaction()
        trans.account_id = account.id
        trans.external_id = data.get("ID")
        trans.value_date = datetime.strptime(data.get("Datetime"), "%Y-%m-%dT%H:%M:%SZ")
        trans.amount = float(data.get("Amount"))
        trans.currency = data.get("Amount currency")
        trans.type = type
        trans.rx_address = ""
        # TODO: check the fee!
        trans.fee = float(data.get("Fee") or 0)
        return trans
