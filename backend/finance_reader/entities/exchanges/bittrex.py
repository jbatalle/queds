from datetime import datetime, timedelta
import time
import hmac
import hashlib
import requests
import codecs
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from finance_reader.entities.exchanges.dtos import ExchangeWallet, Order, Transaction, OrderType


class Bittrex(AbstractExchange):

    def __init__(self):
        super(Bittrex, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.bittrex.com/v3/"

    def login(self, data):
        self.account_id = data.get('account_id')
        self.api_key = data.get('api_key')
        self.api_secret = data.get('api_secret')

    @staticmethod
    def _query(method_verb, **request_kwargs):
        """
        Send the request to the API via requests.
        :param method_verb: valid HTTP Verb (GET, PUT, DELETE, etc.)
        :param request_kwargs: kwargs for request.Request()
        :return: request.Response() object
        """
        if 'method' not in request_kwargs:
            resp = requests.request(method_verb, **request_kwargs)
        else:
            resp = requests.request(**request_kwargs)
        return resp

    def _private_query(self, method_verb, endpoint, **request_kwargs):
        if any(attr is None for attr in (self.api_key, self.api_secret)):
            raise Exception("Key and secret not defined")
        request_kwargs = self.sign_request_kwargs(endpoint, method_verb, **request_kwargs)
        return self._query(method_verb, **request_kwargs)

    @staticmethod
    def generate_hash(message):
        """Function to generate a hash of a message"""
        return hashlib.sha512(str(message).encode("utf-8")).hexdigest()

    def sign_message(self, message):
        """Function to sign an API call"""
        signature = hmac.new(codecs.encode(self.api_secret), codecs.encode(message), hashlib.sha512).hexdigest()
        return signature

    def sign_request_kwargs(self, endpoint, method_verb=None, **kwargs):
        """Sign the request."""
        url = self.base_url + endpoint
        sub_account_id = ""
        timestamp = str(int(time.time() * 1000))
        pre_sign = timestamp + url + method_verb + self.generate_hash("") + sub_account_id
        signature = self.sign_message(pre_sign)
        headers = {
            'content-type': 'application/json',
            'Api-Key': self.api_key,
            'Api-Timestamp': timestamp,
            'Api-Content-Hash': self.generate_hash(""),
            'Api-Signature': signature
        }
        req_kwargs = {'url': url, 'headers': headers}

        return req_kwargs

    def get_balances(self):
        self._logger.info("Getting balances")
        try:
            r = self._private_query('GET', 'balances', authenticate=True, params={}).json()
        except Exception as e:
            self._logger.exception(e)
            return []

        balances = []
        for bal in r:
            balance = ExchangeWallet()
            balance.account_id = self.account_id
            balance.currency = bal['currencySymbol']
            balance.balance = float(bal['total'])
            balances.append(balance)

        return balances

    def get_orders(self):
        self._logger.info("Getting bittrex orders")

        orders_to_process = []
        url = "orders/closed"
        while True:
            try:
                r = self._private_query('GET', url, authenticate=True, params={}).json()
            except Exception as e:
                self._logger.exception(e)
                return []

            orders_to_process.extend(r)
            if len(r) < 100:
                break
            url = "orders/closed?nextPageToken={}".format(r[-1]['id'])

        try:
            orders = self._convert_orders(orders_to_process)
        except Exception as e:
            self._logger.error("ERROR getting orders: {}".format(e))
            return "ERROR"

        self._logger.info("Read {0} orders".format(len(orders)))
        return orders

    def _convert_orders(self, orders):
        arr_orders = []
        for order in orders:
            # self._logger.debug(order)
            if order['status'] != 'CLOSED':
                continue

            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = order['id']
            pair = order['marketSymbol']
            try:
                date = datetime.strptime(order['closedAt'], "%Y-%m-%dT%H:%M:%S.%fZ")
            except:
                date = datetime.strptime(order['closedAt'], "%Y-%m-%dT%H:%M:%SZ")
            new_order.value_date = date
            # new_order.time = int((date + timedelta(hours=2)).strftime("%s"))

            if order['direction'] == 'SELL':
                new_order.pair = "{}/{}".format(pair.split("-")[0], pair.split("-")[1])
                new_order.type= OrderType.SELL
            else:
                new_order.pair = "{}/{}".format(pair.split("-")[0], pair.split("-")[1])
                new_order.type = OrderType.BUY
            if order['type'] != 'LIMIT':
                self._logger.warning("Other type!")
            new_order.price = order['limit']
            new_order.cost = order['proceeds']
            new_order.fee = order['commission']
            new_order.amount = order['quantity']
            arr_orders.append(new_order)
        return arr_orders

    def get_transactions(self):
        self._logger.info("Getting bittrex transactions")

        orders_to_process = []
        url = "deposits/closed"
        while True:
            try:
                r = self._private_query('GET', url, authenticate=True, params={}).json()
            except Exception as e:
                self._logger.exception(e)
                return []

            orders_to_process.extend(r)
            if len(r) < 100:
                break
            url = "deposits/closed?nextPageToken={}".format(r[-1]['id'])

        url = "withdrawals/closed"
        while True:
            try:
                r = self._private_query('GET', url, authenticate=True, params={}).json()
            except Exception as e:
                self._logger.exception(e)
                return []

            orders_to_process.extend(r)
            if len(r) < 100:
                break
            url = "withdrawals/closed?nextPageToken={}".format(r[-1]['id'])
        try:
            transactions = self._convert_transactions(orders_to_process, self.account_id)
        except Exception as e:
            self._logger.error("ERROR getting transactions: {}".format(e))
            return "ERROR"

        self._logger.info("Read {0} transactions".format(len(transactions)))
        return transactions

    @staticmethod
    def _convert_transactions(transactions, account_id):
        arr_transactions = []
        for o in transactions:
            trans = Transaction()
            trans.external_id = account_id
            if o['status'] != 'COMPLETED':
                continue
            if 'source' in o:
                trans.type = OrderType.DEPOSIT
            else:
                trans.type = OrderType.WITHDRAWAL
            trans.transaction_id = o['txId']
            trans.amount = o['quantity']
            date = datetime.strptime(o['completedAt'].split(".")[0], "%Y-%m-%dT%H:%M:%S")
            trans.value_date = date
            # trans.time = int((date + timedelta(hours=2)).strftime("%s"))
            trans.currency = o['currencySymbol']
            trans.rx_address = o['cryptoAddress']
            if 'txCost' in o:
                trans.fee = o['txCost']
            arr_transactions.append(trans)
        return arr_transactions
