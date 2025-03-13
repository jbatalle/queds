from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import base64
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from models.dtos.exchange_dtos import ExchangeWallet, Order, Transaction, OrderType
import time
import requests
import json
from urllib.parse import urljoin
from urllib.parse import urlencode


class Kucoin(AbstractExchange):

    def __init__(self):
        super(Kucoin, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.kucoin.com"

    def login(self, data):
        key = "67c0791102d39e00012a8bf7"
        secret = "7835b83c-17db-4c27-9d3c-c49d70080c7d"
        self.account_id = data.get('account_id')
        self.api_key = data.get('api_key')
        self.api_secret = data.get('api_secret')
        self.api_key = "67c0791102d39e00012a8bf7"
        self.api_secret = "7835b83c-17db-4c27-9d3c-c49d70080c7d"
        self.api_passphrase = "2czy9Ffv2aGS"
        self.api_passphrase = self.sign(self.api_passphrase.encode('utf-8'), self.api_secret.encode('utf-8'))

    def sign(self, plain: bytes, key: bytes) -> str:
        hm = hmac.new(key, plain, hashlib.sha256)
        return base64.b64encode(hm.digest()).decode()

    def headers(self, plain: str) -> dict:
        """
        Headers method generates and returns a map of signature headers needed for API authorization
        It takes a plain string as an argument to help form the signature. The outputs are a set of API headers.
        """
        timestamp = str(int(time.time() * 1000))
        signature = self.sign((timestamp + plain).encode('utf-8'), self.api_secret.encode('utf-8'))

        return {
            "KC-API-KEY": self.api_key,
            "KC-API-PASSPHRASE": self.api_passphrase,
            "KC-API-TIMESTAMP": timestamp,
            "KC-API-SIGN": signature,
            "KC-API-KEY-VERSION": "2"
        }

    def process_headers(self, body: bytes, raw_url: str, request: requests.PreparedRequest, method: str):
        request.headers["Content-Type"] = "application/json"

        # Create the payload by combining method, raw URL, and body
        payload = method + raw_url + body.decode()
        headers = self.headers(payload)

        # Add headers to the request
        request.headers.update(headers)

    def get_balances(self):
        endpoint = "https://api.kucoin.com"
        path = "/api/v1/trade-fees"
        method = "GET"
        query_params = {"symbols": "BTC-USDT"}

        # Build full URL and raw URL
        full_path = f"{endpoint}{path}?{urlencode(query_params)}"
        raw_url = f"{path}?{urlencode(query_params)}"

        req = requests.Request(method=method, url=full_path).prepare()
        self.process_headers( b"", raw_url, req, method)

        resp = self._client.send(req)
        resp_obj = json.loads(resp.content)
        print(resp_obj)

    def query(self, method, uri, params=None):
        uri_path = uri
        data_json = ''
        if method in ['GET', 'DELETE']:
            if params:
                strl = []
                for key in sorted(params):
                    strl.append("{}={}".format(key, params[key]))
                data_json += '&'.join(strl)
                uri += '?' + data_json
                uri_path = uri
        else:
            if params:
                data_json = json.dumps(params)

                uri_path = uri + data_json

        now_time = int(time.time()) * 1000
        str_to_sign = str(now_time) + method + uri_path
        sign = base64.b64encode(hmac.new(self.api_secret.encode('utf-8'), str_to_sign.encode('utf-8'), hashlib.sha256).digest())

        passphrase = base64.b64encode(hmac.new(self.api_secret.encode('utf-8'), self.passphrase.encode('utf-8'), hashlib.sha256).digest())
        headers = {
            "KC-API-SIGN": sign,
            "KC-API-TIMESTAMP": str(now_time),
            "KC-API-KEY": self.api_key,
            "KC-API-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "KC-API-KEY-VERSION": "2"
        }
        url = urljoin(self.base_url, uri_path)

        if method in ['GET', 'DELETE']:
            response_data = requests.request(method, url, headers=headers, timeout=5)
        else:
            response_data = requests.request(method, url, headers=headers, data="", timeout=5)

        return response_data

    def get_balances_old(self):
        try:
            r = self.query("GET", "/api/v1/accounts").json()
        except Exception as e:
            self._logger.error(e)
            return []

        if 'data' not in r:
            self._logger.error(r)
            raise

        balances = []
        for d in r['data']:
            balance = ExchangeWallet()
            balance.account_id = self.account_id
            balance.currency = d['currency']
            balance.balance = float(d['balance'])
            balances.append(balance)

        return balances

    def get_orders(self):
        self._logger.info("Get Kucoin Closed orders")
        parsed_orders = []
        orders = self.query("GET", "/api/v1/orders").json()

        d = datetime(2014, 11, 22, 14, 42, 21, 34435, tzinfo=timezone.utc)
        offset = 0
        parsed_orders.extend(self._convert_orders(orders))
        max_count = orders['data']['count']
        offset += 50
        while offset < max_count:
            # TODO
            try:
                orders = self.query("GET", "/api/v1/orders", params={"page": offset}).json()
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
        for order in orders['data']['items']:
            # if order['status'] != 'closed':
                # continue
            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = order['id']
            new_order.pair = order['symbol'].replace("-", "/")
            new_order.value_date = datetime.fromtimestamp(order['createdAt'])
            # new_order.time = int((date - timedelta(hours=1)).strftime("%s"))
            if order['side'] == 'sell':
                new_order.type = OrderType.SELL
            elif order['side'] == 'buy':
                new_order.type = OrderType.BUY
            new_order.price = float(order['price'])
            new_order.cost = float(order['price']) * float(order['size'])
            new_order.fee = float(order['fee'])
            new_order.amount = float(order['size'])
            arr_orders.append(new_order)
        return arr_orders

    def get_transactions(self):
        total_transactions = []
        offset = 0

        transactions = self.query("GET", "/api/v1/withdrawals").json()
        try:
            transactions = self.query("GET", "/api/v1/deposits").json()
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

    def others(self):
        orders = self.query("GET", "/api/v1/orders").json()
        ledgers = self.query("GET", "/api/v1/accounts/ledgers").json()
        deposits = self.query("GET", "/api/v1/deposits").json()
