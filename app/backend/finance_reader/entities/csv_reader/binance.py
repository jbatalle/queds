from finance_reader.entities.csv_reader import ExchangeCSVProcessor
from models.dtos.exchange_dtos import Order, Transaction, OrderType
from datetime import datetime


class Binance(ExchangeCSVProcessor):

    def __init__(self):
        super(Binance, self).__init__()

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Binance CSV file for account {account.id}")
        lines = csv_data.splitlines()
        headers = lines[0].split(",")

        if 'TXID' in headers:
            return [], []

        orders = []
        transactions = []

        headers = [h.replace('"', "") for h in headers]
        from collections import defaultdict
        trades = defaultdict(lambda: {"buy": None, "sell": None, "fees": [], "order_type": None})
        for line in lines[1:]:
            row = dict(zip(headers, line.replace('"', "").split(",")))
            timestamp = row["UTC_Time"]
            operation = row["Operation"]
            coin = row["Coin"]
            amount = float(row["Change"])

            if operation in ['Deposit', 'Asset - Transfer', 'Airdrop Assets', 'Staking Rewards', 'Distribution']:
                transactions.append(self.process_transaction(account, row))
                continue

            if trades[timestamp]["order_type"] is None:
                trades[timestamp]["order_type"] = operation

            if operation == "Buy":
                trades[timestamp]["buy"] = {"coin": coin, "amount": amount}
            elif operation == "Sell":
                trades[timestamp]["sell"] = {"coin": coin, "amount": abs(amount)}
            elif operation == "Fee":
                trades[timestamp]["fees"].append(amount)
            else:
                print(f"Unhandled operation {operation} at {timestamp}")

        final_orders = []
        for timestamp, data in trades.items():
            if data["buy"] and data["sell"]:
                buy_coin = data["buy"]["coin"]
                sell_coin = data["sell"]["coin"]
                buy_amount = data["buy"]["amount"]
                sell_amount = data["sell"]["amount"]

                # Calculate price (Sell Amount / Buy Amount)
                # price = sell_amount / buy_amount
                price = buy_amount / sell_amount

                # Sum of all fees
                amount = float(sell_amount)
                total_fee = sum(data["fees"])
                # order_type = OrderType.BUY if data['order_type'] == "Buy" else OrderType.SELL
                order_type = OrderType.SELL
                #if order_type == OrderType.BUY:
                    #amount = amount + float(sell_amount)
                    #total_fee = 0

                order = Order()
                order.account_id = account.id
                external_id = f"{timestamp}_{buy_coin}_{sell_coin}_{buy_amount}"
                order.external_id = external_id
                order.value_date = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
                # order.pair = f"{buy_coin}/{sell_coin}"
                order.pair = f"{sell_coin}/{buy_coin}"
                order.amount = amount
                order.type = order_type
                order.price = price
                order.fee = total_fee
                # order.total_buy = order.amount*order.price
                orders.append(order)

            #order = self.create_order(account, data)
            #if order:
                #orders.append(order)

        return orders, transactions

    def create_order(self, account, data):
        type = None
        if data.get('Operation') == 'Asset - Transfer':
            type = OrderType.DEPOSIT
        elif data.get('Operation') == 'Distribution':
            return None
        elif data.get('Subtype') == 'Deposit':
            type = OrderType.DEPOSIT
        elif data.get('Subtype') == 'Buy':
            type = OrderType.BUY
        elif data.get('Subtype') == 'Buy':
            type = OrderType.BUY

        if type == None:
            self.log.error(f"Unknown order type: {data.get('Type')} - {data.get('Subtype')}")
            return None

        order = Order()
        order.account_id = account.id
        order.external_id = data.get("ID")
        order.value_date = datetime.strptime(data.get("UTC_Time"), "%Y-%m-%d %H:%M:%S")
        order.pair = data.get("Amount currency") + "/" + data.get("Value currency")
        order.amount = float(data.get("Change"))
        order.type = type
        order.price = float(data.get("Rate"))
        order.fee = float(data.get("Fee") or 0)
        return order

    def process_transaction(self, account, data):
        amount = float(data.get("Change"))
        if data['Operation'] in ['Distribution', 'Airdrop Assets']:
            type = OrderType.AIRDROP
        elif data['Operation'] in ['Staking Rewards', 'Asset - Transfer']:
            type = OrderType.STAKING
        elif amount > 0:
            type = OrderType.DEPOSIT
        else:
            type = OrderType.WITHDRAWAL
        # if data.get('Type') == 'Deposit':
        #                type = OrderType.DEPOSIT
        #            elif data.get('Type') == 'Withdrawal':
        #                type = OrderType.WITHDRAWAL

        #            if not type:
        #                self.log.error(f"Unknown transaction type: {data.get('Type')} - {data.get('Subtype')}")
        #                return None

        trans = Transaction()
        trans.account_id = account.id
        trans.external_id = f"{data.get('UTC_Time')}_{data['Coin']}_{data['Change']}"
        trans.value_date = datetime.strptime(data.get("UTC_Time"), "%Y-%m-%d %H:%M:%S")
        trans.amount = abs(amount)
        trans.currency = data.get("Coin")
        trans.type = type
        # trans.rx_address = data.get('Address')
        # trans.tx_address = data.get('SourceAddress')
        # trans.fee = float(data.get("TransactionFee") or 0)
        return trans
