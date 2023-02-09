from datetime import datetime, timedelta
import hashlib
import hmac
import time
import urllib
import requests
import concurrent.futures
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from finance_reader.entities.exchanges.dtos import ExchangeWallet, Order, Transaction, OrderType


class Binance(AbstractExchange):

    def __init__(self):
        super(Binance, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.binance.com/"

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

    def sign_request_kwargs(self, endpoint, method_verb=None, **kwargs):
        """Sign the request."""
        url = self.base_url + endpoint
        req_kwargs = {'url': url, 'headers': {'X-MBX-APIKEY': self.api_key.encode('utf-8')}}

        params = kwargs.pop('params', {})
        params['timestamp'] = str(int(time.time() * 1000))
        req_string = urllib.parse.urlencode(params)
        params['signature'] = hmac.new(self.api_secret.encode('utf-8'), req_string.encode('utf-8'),
                                       hashlib.sha256).hexdigest()

        req_kwargs['params'] = params
        return req_kwargs

    def get_balances(self):
        self._logger.info("Getting balances")
        try:
            r = self._private_query('GET', 'api/v3/account', authenticate=True, params={}).json()
        except Exception as e:
            self._logger.exception(e)
            return []

        if 'balances' not in r:
            self._logger.error(r)
            raise

        balances = []
        for bal in r['balances']:
            if float(bal['free']) + float(bal['locked']) == 0:
                continue
            balance = ExchangeWallet()
            balance.account_id = self.account_id
            balance.currency = bal['asset']
            balance.balance = float(bal['free']) + float(bal['locked'])
            balances.append(balance)
        return balances

    def get_orders_from_binance(self, idx, q):
        symbol = q['symbol']

        if idx % 10 == 0:
            self._logger.debug(idx)

        try:
            r = self._private_query('GET', 'api/v3/allOrders', authenticate=True, params={"symbol": symbol})
        except Exception as e:
            self._logger.exception(e)
            return []
        if r.status_code != 200:
            return []

        symbol_orders = r.json()
        for s in symbol_orders:
            s['pair'] = q['baseAsset'] + "/" + q['quoteAsset']

        return symbol_orders

    def get_orders(self):
        self._logger.info("Get Binance Closed orders")

        try:
            r = self._query('GET', **{'url': self.base_url + 'api/v3/exchangeInfo'}).json()
        except Exception as e:
            self._logger.exception(e)
            return []

        self._logger.info("Iterate over {} symbols".format(len(r['symbols'])))
        orders = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            task = {executor.submit(self.get_orders_from_binance, idx, q): q for idx, q in enumerate(r['symbols'])}
            for future in concurrent.futures.as_completed(task):
                url = task[future]
                try:
                    orders.extend(future.result())
                except Exception as exc:
                    self._logger.error('%r generated an exception: %s' % (url, exc))

        self._logger.info("Converting {0} orders".format(len(orders)))
        try:
            orders = self._convert_orders(orders)
        except Exception as e:
            self._logger.exception("ERROR getting orders: {}".format(e))
            return []

        self._logger.info("Read {0} orders".format(len(orders)))
        return orders

    def _convert_orders(self, orders):
        arr_orders = []
        for order in orders:
            if order['status'] != 'FILLED':
                continue
            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = order['orderId']
            new_order.pair = order['pair']
            new_order.value_date = datetime.fromtimestamp(order['time']/1000)
            if order['side'] == 'BUY':
                new_order.type = OrderType.BUY
            elif order['side'] == 'SELL':
                new_order.type = OrderType.SELL
            else:
                self._logger.warning("Not able to detect type: {}".format(order['side']))
                continue

            new_order.price = order['price']
            new_order.cost = order['cummulativeQuoteQty']
            new_order.fee = 0
            new_order.amount = float(order['origQty'])
            arr_orders.append(new_order)
        return arr_orders

    def get_transactions(self):
        self._logger.info("Get deposit/withdrawals!")
        transactions = []
        start = datetime(2017, 6, 1)
        end = start + timedelta(days=89)
        try:
            r = self._private_query('GET', 'sapi/v1/capital/deposit/hisrec', authenticate=True,
                                    params={
                                        "startTime": int(start.timestamp()*1000),
                                        "endTime": int(end.timestamp()*1000)
                                    }).json()
            q = self._private_query('GET', 'sapi/v1/capital/withdraw/history', authenticate=True,
                                    params={
                                        "startTime": int(start.timestamp()*1000),
                                        "endTime": int(end.timestamp()*1000)
                                    }).json()
        except Exception as e:
            self._logger.exception(e)
            return []
        transactions.extend(r)
        transactions.extend(q)
        while start < datetime.now():
            start = end
            end = start + timedelta(days=89)
            try:
                r = self._private_query('GET', 'sapi/v1/capital/deposit/hisrec', authenticate=True,
                                        params={"startTime": int(start.timestamp()*1000),
                                                "endTime": int(end.timestamp()*1000)}).json()

                q = self._private_query('GET', 'sapi/v1/capital/withdraw/history', authenticate=True,
                                        params={"startTime": int(start.timestamp() * 1000),
                                                "endTime": int(end.timestamp() * 1000)}).json()
            except Exception as e:
                self._logger.exception(e)
                return []
            transactions.extend(r)
            transactions.extend(q)

        self._logger.info("Converting {0} transactions".format(len(transactions)))
        try:
            arr_transactions = self._convert_transactions(transactions)
        except Exception as e:
            self._logger.exception("ERROR getting transactions: {}".format(e))
            return []

        self._logger.info("Read {0} orders".format(len(arr_transactions)))
        return arr_transactions

    def _convert_transactions(self, orders):
        arr_orders = []
        for order in orders:
            new_order = Transaction()
            new_order.account_id = self.account_id
            new_order.external_id = f"{order['txId']}"
            new_order.currency = order['coin']
            new_order.value_date = datetime.fromtimestamp(order['time'] / 1000)
            new_order.type = OrderType.DEPOSIT
            new_order.rx_address = order['address']
            new_order.amount = float(order['amount'])
            new_order.fee = 0
            arr_orders.append(new_order)
        return arr_orders
