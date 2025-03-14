from finance_reader.entities.csv_reader import ExchangeCSVProcessor
from models.dtos.exchange_dtos import Order, Transaction, OrderType
from datetime import datetime


class Coinbase(ExchangeCSVProcessor):

    def __init__(self):
        super(Coinbase, self).__init__()

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Coinbase CSV file for account {account.id}")
        lines = csv_data.splitlines()
        headers = lines[0].split(",")

        orders = []
        transactions = []
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))
            type = None

            if data.get('Transaction Type') == 'Buy' and data.get('EUR Spot Price at Transaction') == '1':
                type = OrderType.DEPOSIT
            elif data.get('Transaction Type') == 'Buy':
                type = OrderType.BUY
            elif data.get('Transaction Type') == 'Sell':
                type = OrderType.SELL
            elif data.get('Transaction Type') == 'Send':
                type = OrderType.WITHDRAWAL

            amount = float(data.get("Quantity Transacted"))
            value_date = datetime.strptime(data.get('Timestamp'), "%Y-%m-%dT%H:%M:%SZ")
            currency = data.get("Asset")
            external_id = f"{value_date}_{currency}_{amount}"
            fees = float(data.get('EUR Fees') or 0)

            if type in [OrderType.WITHDRAWAL, OrderType.DEPOSIT]:
                trans = Transaction()
                trans.account_id = account.id
                trans.external_id = external_id
                trans.value_date = value_date
                trans.amount = abs(amount)
                trans.currency = data.get("Asset")
                trans.type = type
                try:
                    trans.rx_address = data.get('Notes').split(f'{trans.currency} to ')[1]
                except:
                    pass
                trans.fee = fees
                transactions.append(trans)
                continue

            order = Order()
            order.account_id = account.id
            order.external_id = external_id
            order.value_date = value_date
            order.pair = f"{data.get('Asset')}/EUR"
            order.amount = amount
            order.type = type
            order.price = float(data.get("EUR Subtotal"))/float(data.get('Quantity Transacted'))
            order.fee = fees
            orders.append(order)

        return orders, transactions
