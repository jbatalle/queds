from finance_reader.entities.csv_reader import ExchangeCSVProcessor
from models.dtos.exchange_dtos import Order, Transaction, OrderType
from datetime import datetime


class Kucoin(ExchangeCSVProcessor):

    def __init__(self):
        super(Kucoin, self).__init__()

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Kucoin CSV file for account {account.id}")
        lines = csv_data.splitlines()
        headers = lines[0].split(",")
        if len(headers) == 9:
            return [], self._process_transaction_csv(lines, account)

        orders = []
        transactions = []
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))
            type = None
            if data.get('Side') == 'BUY':
                type = OrderType.BUY
            elif data.get('Side') == 'SELL':
                type = OrderType.SELL
            else:
                self.log.info(f"Unhandled type: {data.get('Remarks')}")

            order = Order()
            order.account_id = account.id
            order.external_id = data.get("Order ID")
            order.value_date = datetime.strptime(data.get("Filled Time(UTC)"), "%Y-%m-%d %H:%M:%S")
            order.pair = data.get("Symbol").replace("-", "/")
            order.amount = float(data.get("Order Amount"))
            order.type = type
            order.price = float(data.get("Order Price"))
            order.fee = float(data.get('Fee') or 0)
            orders.append(order)

        return orders, transactions

    def _process_transaction_csv(self, lines, account):
        transactions = []
        headers = lines[0].split(",")
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))

            if data.get('Status') != 'SUCCESS':
                continue

            type = None
            if data.get('Remarks') == 'Deposit':
                type = OrderType.DEPOSIT
            elif data.get('Type') == 'Transfer':
                type = OrderType.WITHDRAWAL
            else:
                self.log.info(f"Unhandled type: {data.get('Remarks')}")

            trans = Transaction()
            trans.account_id = account.id
            trans.value_date = datetime.strptime(data.get("Time(UTC)"), "%Y-%m-%d %H:%M:%S")
            trans.amount = abs(float(data.get("Amount")))
            trans.currency = data.get("Coin")
            trans.type = type
            trans.rx_address = ""
            trans.fee = float(data.get("Fee") or 0)
            trans.external_id = f"{trans.value_date}_{trans.currency}_{trans.amount}"
            transactions.append(trans)
        return transactions

    def _process_converted_orders(self, csv_data, account):
        lines = csv_data.splitlines()
        headers = lines[0].split(",")

        orders = []
        transactions = []
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))
            type = OrderType.BUY

            order = Order()
            order.account_id = account.id
            order.value_date = datetime.strptime(data.get("Time of Update(UTC)"), "%Y-%m-%d %H:%M:%S")
            order.pair = f'{data.get("Buy").split(" ")[1]}/{data.get("Sell").split(" ")[1]}'
            order.amount = float(data.get("Buy").split(" ")[0])
            order.type = type
            order.price = float(float(data.get("Sell").split(" ")[0])/order.amount)
            order.fee = 0
            order.external_id = f"{order.value_date}_{order.pair}_{order.amount}"
            orders.append(order)

        return orders, transactions