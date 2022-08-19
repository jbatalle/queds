from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import urllib
import urllib.parse
import base64
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from finance_reader.entities.exchanges.dtos import ExchangeWallet, Order, Transaction, OrderType


class Kraken(AbstractExchange):

    def __init__(self):
        super(Kraken, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.kraken.com"

    def login(self, data):
        self.account_id = data.get('account_id')
        self.api_key = data.get('api_key')
        self.api_secret = data.get('api_secret')
        self._client.headers.update({
            'API-Key': self.api_key
        })

    def query(self, endpoint_path, **kwargs):
        url = self.base_url + endpoint_path
        try:
            req = kwargs['params']
        except KeyError:
            req = {}

        req['nonce'] = self.nonce()
        postdata = urllib.parse.urlencode(req)

        # Unicode-objects must be encoded before hashing
        encoded = (str(req['nonce']) + postdata).encode('utf-8')
        message = (endpoint_path.encode('utf-8') + hashlib.sha256(encoded).digest())

        signature = hmac.new(base64.b64decode(self.api_secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        self._client.headers.update({
            'API-Sign': sigdigest.decode('utf-8')
        })

        return self._client.post(url, req)

    def get_balances(self):
        try:
            r = self.query("/0/private/Balance").json()
        except Exception as e:
            self._logger.error(e)
            return []

        if 'result' not in r:
            self._logger.error(r)
            raise

        balances = []
        for currency, amount in r['result'].items():
            balance = ExchangeWallet()
            balance.account_id = self.account_id
            if len(currency) > 3:
                balance.currency = currency[1:].upper()
            else:
                balance.currency = currency.upper()
            balance.balance = amount
            balances.append(balance)

        return balances

    def get_orders(self):
        self._logger.info("Get Kraken Closed orders")
        parsed_orders = []
        d = datetime(2014, 11, 22, 14, 42, 21, 34435, tzinfo=timezone.utc)
        offset = 0
        try:
            orders = self.query("/0/private/TradesHistory", params={"ofs": 0}).json()
        except Exception as e:
            self._logger.exception(e)
            return

        parsed_orders.extend(self._convert_orders(orders))
        max_count = orders['result']['count']
        offset += 50
        while offset < max_count:
            try:
                orders = self.query("/0/private/TradesHistory", params={"ofs": offset}).json()
            except Exception as e:
                self._logger.exception(e)
                return
            parsed_orders.extend(self._convert_orders(orders))
            if len(orders['result']['trades'].items()) == 50:
                offset += 50
            else:
                offset += len(orders['result']['trades'].items())

        self._logger.info("Read {0} closed orders".format(len(parsed_orders)))
        return parsed_orders

    def _convert_orders(self, orders):
        arr_orders = []
        for orderid, order in orders['result']['trades'].items():
            # if order['status'] != 'closed':
                # continue
            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = orderid
            if len(order['pair']) > 6:
                new_order.pair = order['pair'][1:4] + '/' + order['pair'][5:]
            else:
                new_order.pair = order['pair'][:3] + '/' + order['pair'][3:]
            new_order.value_date = datetime.fromtimestamp(order['time'])
            # new_order.time = int((date - timedelta(hours=1)).strftime("%s"))
            if order['type'] == 'sell':
                new_order.type = OrderType.SELL
            elif order['type'] == 'buy':
                new_order.type = OrderType.BUY
            new_order.price = float(order['price'])
            new_order.cost = float(order['cost'])
            new_order.fee = float(order['fee'])
            new_order.amount = float(order['vol'])
            arr_orders.append(new_order)
        return arr_orders

    def get_transactions(self):
        total_transactions = []
        offset = 0
        try:
            transactions = self.query("/0/private/Ledgers", params={"ofs": 0}).json()
        except Exception as e:
            self._logger.error(e)
            return

        total_transactions.extend(transactions['result']['ledger'].values())
        max_count = transactions['result']['count']
        offset += 50
        while offset < max_count:
            try:
                transactions = self.query("/0/private/Ledgers", params={"ofs": offset}).json()
            except Exception as e:
                self._logger.exception(e)
                return
            total_transactions.extend(transactions['result']['ledger'].values())
            if len(transactions['result']['ledger'].items()) == 50:
                offset += 50
            else:
                offset += len(transactions['result']['ledger'].items())

        arr_transactions = []
        for t in total_transactions:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.external_id = t['refid']
            if len(t['asset']) > 3:
                trans.currency = t['asset'][1:]
            else:
                trans.currency = t['asset']

            trans.value_date = datetime.fromtimestamp(t['time'])
            # trans.time = int((date - timedelta(hours=1)).strftime("%s"))
            if t['type'] == 'withdrawal':
                trans.type = OrderType.WITHDRAWAL
            elif t['type'] == 'deposit':
                trans.type = OrderType.DEPOSIT
            else:
                continue
            trans.amount = abs(float(t['amount']))
            trans.fee = t['fee']
            arr_transactions.append(trans)

        self._logger.info("Found {0} transactions".format(len(arr_transactions)))
        return arr_transactions
