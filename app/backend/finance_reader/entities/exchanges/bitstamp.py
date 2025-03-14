from datetime import datetime, timedelta
import hashlib
import hmac
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from models.dtos.exchange_dtos import ExchangeWallet, Order, Transaction, OrderType


class Bitstamp(AbstractExchange):

    def __init__(self):
        super(Bitstamp, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.user_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://www.bitstamp.net/api"
        self.transactions = []

    def sign(self, **kwargs):
        nonce = self.nonce()
        message = nonce + self.user_id + self.api_key

        signature = hmac.new(self.api_secret.encode(), message.encode(), hashlib.sha256)
        signature = signature.hexdigest().upper()

        try:
            req = kwargs['params']
        except KeyError:
            req = {}
        req['key'] = self.api_key
        req['nonce'] = nonce
        req['signature'] = signature
        return req

    def login(self, data):
        self.account_id = data.get('account_id')
        self.user_id = data.get('user_id')
        self.api_key = data.get('api_key')
        self.api_secret = data.get('api_secret')

    def get_balances(self):
        self._logger.info("Getting balances")
        data = self.sign(params={})
        try:
            r = self._client.post(self.base_url + "/v2/balance/", data=data).json()
        except Exception as e:
            self._logger.error(e)
            return []

        if 'status' in r and r['status'] == 'error':
            self._logger.error("Error reading balances")
            raise

        balances = []
        currencies = ["btc_balance", "xrp_balance", "ltc_balance", "eth_balance", "eur_balance", "ada_balance"]
        for currency in r:
            if '_balance' not in currency:
                continue
            if float(r[currency]) == 0:
                continue

            balance = ExchangeWallet()
            balance.account_id = self.account_id
            balance.currency = currency.replace("_balance", "").upper()
            balance.balance = r[currency]
            balances.append(balance)

        return balances

    def get_orders(self):
        self._logger.info("Get Bitstamp Closed orders")

        data = self.sign(params={'limit': 1000})
        orders = self._client.post(self.base_url + "/v2/user_transactions/", data=data).json()
        self._logger.info("Converting {0} orders".format(len(orders)))
        try:
            orders, self.transactions = self._convert_orders(orders)
        except Exception as e:
            self._logger.error("ERROR getting orders: {}".format(e))
            return "ERROR"
        # if order_id duplicate, join values
        t = {}
        for i in orders:
            if i.external_id in t:
                t[i.external_id].vol = float(t[i.external_id].ammount) + float(str(i.ammount))
                # t[i.order_id].cost = float(t[i.order_id].price) * t[i.order_id].ammount
            else:
                t[i.external_id] = i
        orders = t.values()

        self._logger.info("Read {0} orders".format(len(orders)))
        return orders

    def _convert_orders(self, orders):
        arr_orders = []
        transactions = []
        for order in orders:
            if order['type'] == '0' or order['type'] == '1':
                # deposit -> 0 withdraw -> 1
                print("Deposit/Withdrawal", order)
                transactions.append(order)
                continue

            pair = next(p for p in order.keys() if p!='order_id' and '_' in p)
            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = order['id']
            split_pair = pair.split("_")
            new_order.pair = (split_pair[0] + '/' + split_pair[1]).upper()
            try:
                new_order.value_date = datetime.strptime(order['datetime'], "%Y-%m-%d %H:%M:%S.%f")
            except:
                new_order.value_date = datetime.strptime(order['datetime'], "%Y-%m-%d %H:%M:%S")
            amount = float(order[pair.split("_")[0]])
            new_order.amount = abs(amount)
            new_order.price = order[pair]
            new_order.fee = order['fee']
            new_order.type = OrderType.SELL if amount < 0 else OrderType.BUY
            arr_orders.append(new_order)
        return arr_orders, transactions

    def get_transactions(self):
        self._logger.info("Get deposit/withdrawals!")
        data = self.sign(params={'limit': 1000})
        orders = self._client.post(self.base_url + "/v2/crypto-transactions/", data=data).json()
        self._logger.info("Converting {0} orders".format(len(orders)))
        transactions = self._convert_deposit_orders(orders['deposits'])
        transactions.extend(self._convert_withdrawal_orders(orders['withdrawals']))

        self._logger.info("Found {0} transactions".format(len(transactions)))
        return transactions

    def _convert_deposit_orders(self, orders):
        transactions = []
        for o in orders:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.type = OrderType.DEPOSIT
            trans.external_id = o['txid']
            trans.amount = o['amount']
            date = datetime.fromtimestamp(o['datetime'])
            trans.value_date = date # - timedelta(hours=1)
            trans.currency = o['currency']
            trans.rx_address = o['destinationAddress']
            trans.fee = 0
            transactions.append(trans)
        return transactions

    def _convert_withdrawal_orders(self, orders):
        transactions = []
        for o in orders:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.type = OrderType.WITHDRAWAL
            trans.external_id = o['txid']
            trans.amount = o['amount']
            trans.value_date = datetime.fromtimestamp(o['datetime'])
            trans.currency = o['currency']
            trans.rx_address = o['destinationAddress']
            # TODO: check the fee!
            trans.fee = 0
            transactions.append(trans)
        return transactions
