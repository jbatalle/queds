from finance_reader.entities.csv_reader import ExchangeCSVProcessor
from models.dtos.exchange_dtos import Order, Transaction, OrderType
from datetime import datetime


class Bittrex(ExchangeCSVProcessor):

    def __init__(self):
        super(Bittrex, self).__init__()

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Bittrex CSV file for account {account.id}")
        lines = csv_data.splitlines()
        if 'Date' in lines[0]:
            transactions = self._process_transaction_csv(lines, account)
            orders = []
            to_remove = []
            for t in transactions:
                if 'MAINTENANCE' not in t.rx_address and 'LIQUIDATION' not in t.rx_address:
                    continue

                order = Order()
                order.account_id = account.id
                order.external_id = t.external_id
                order.value_date = t.value_date
                order.pair = f"{t.currency}/EUR"
                order.amount = t.amount
                order.type = OrderType.SELL
                order.price = 0
                order.fee = 0
                orders.append(order)
                to_remove.append(t)

            for t in to_remove:
                transactions.remove(t)
            return orders, transactions
        try:
            headers = lines[4].split(",")
        except:
            return [], []

        orders = []
        transactions = []
        for line in lines[5:]:
            data = dict(zip(headers, line.split(",")))
            type = None
            if data.get('Transaction') == 'Sold':
                type = OrderType.SELL
            elif data.get('Transaction') == 'Bought':
                type = OrderType.BUY
            elif data.get('Transaction') == 'Converted':
                type = OrderType.SELL

            if type == None:
                self.log.error(f"Unknown order type: {data.get('Type')} - {data.get('Subtype')}")
                continue

            order = Order()
            order.account_id = account.id
            order.external_id = data.get("TXID")
            order.value_date = datetime.strptime(data.get("Time (UTC)"), "%Y-%m-%dT%H:%M:%S")
            order.pair = data.get("Market").replace("-->", "/")
            order.amount = float(data.get("Quantity (Base)"))
            order.type = type
            order.price = float(data.get("Price"))
            order.fee = float(data.get('Fees (Quote)') or 0)
            orders.append(order)

        return orders, transactions

    def _process_transaction_csv(self, lines, account):
        transactions = []
        headers = lines[0].split(",")
        for line in lines[1:]:
            data = dict(zip(headers, line.split(",")))

            op_type = None
            if data.get('Type') == 'DEPOSIT':
                op_type = OrderType.DEPOSIT
            elif data.get('Type') == 'WITHDRAWAL':
                op_type = OrderType.WITHDRAWAL

            if op_type == OrderType.DEPOSIT and data.get('Address') == "":
                op_type = OrderType.AIRDROP

            trans = Transaction()
            trans.account_id = account.id
            # account=account,
            trans.external_id = data.get("TxId").replace('"', '')
            trans.value_date = datetime.strptime(data.get("Date"), "%Y-%m-%d %H:%M:%S.%f")
            #if trans.value_date > datetime(2024,1,1):
                #continue
            trans.amount = abs(float(data.get("Amount")))
            trans.currency = data.get("Currency")
            trans.type = op_type
            trans.rx_address = data.get('Address').replace('"', '')
            trans.fee = float(data.get("Fee") or 0)
            transactions.append(trans)
        return transactions
