import time
import hashlib
import hmac
import urllib
import urllib.parse
import base64
from datetime import datetime, timezone
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from models.dtos.exchange_dtos import ExchangeWallet, Order, Transaction, OrderType


class Kraken(AbstractExchange):

    def __init__(self):
        super(Kraken, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {}
        self.account_id = None
        self.api_key = None
        self.api_secret = None
        self.base_url = "https://api.kraken.com"
        self.ledgers = {}

    def login(self, data):
        self.account_id = data.get('account_id')
        self.api_key = data.get('api_key')
        self.api_secret = data.get('api_secret')
        self._client.headers.update({
            'API-Key': self.api_key
        })

    def query(self, endpoint_path, **kwargs):
        """Performs a query to Kraken API with the correct authentication and signing."""
        url = self.base_url + endpoint_path
        req = kwargs.get('params', {})
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

    def fetch_with_retry(self, endpoint, retries=5, retry_delay=5, params={}):
        """Handles API calls with retry logic when 'result' is not present in the response."""
        for attempt in range(retries):
            try:
                response = self.query(endpoint, params=params).json()
                if 'result' in response:
                    return response
                else:
                    self._logger.error(f"Attempt {attempt+1}/{retries}: 'result' not in response, retrying...")
            except Exception as e:
                self._logger.error(f"Attempt {attempt+1}/{retries}: Exception occurred - {e}, retrying...")
            time.sleep(retry_delay * (attempt + 1)*2)
            attempt += 1
        raise Exception(f"Failed to fetch 'result' after {retries} retries.")

    def get_paginated_data(self, endpoint, type, params={}):
        """Handles fetching paginated data."""
        data = {}
        offset = 0
        count = 0
        while offset == 0 or offset < count:
            self._logger.debug(f"Fetching {endpoint} with offset {offset}/{count}")
            params = params or {}
            params['ofs'] = offset
            response = self.fetch_with_retry(endpoint, params=params)
            # data.extend(response['result'][type].values())
            data.update(response['result'][type])
            count = response['result']['count']
            if len(response['result'][type].items()) < 50:
                break
            offset += 50
        return data

    def get_balances(self):
        """Fetches balances from Kraken API."""
        try:
            response = self.fetch_with_retry("/0/private/Balance", params={})
        except Exception as e:
            self._logger.error(f"Failed to get balances: {e}")
            return []

        balances = []
        for currency, amount in response['result'].items():
            balance = ExchangeWallet()
            balance.account_id = self.account_id
            balance.currency = currency[1:].upper() if len(currency) > 3 else currency.upper()
            balance.balance = amount
            balances.append(balance)
        return balances

    def get_orders(self):
        """Fetches and parses Kraken orders."""
        self._logger.info("Get Kraken Ledger orders...")
        ledgers = self.get_ledgers()

        self._logger.info("Get Kraken Trading orders...")
        orders = self.get_paginated_data("/0/private/TradesHistory", type='trades', params={"ofs": 0, "trades": True})

        self._logger.info("Converting Kraken orders...")
        parsed_orders = self._convert_orders(ledgers, orders)

        self._logger.info(f"Read {len(parsed_orders)} closed orders")
        return parsed_orders

    def get_paginated_orders(self, max_count, ledgers):
        """Handles pagination for Kraken orders."""
        offset = 50
        parsed_orders = []
        while offset < max_count:
            time.sleep(5)
            orders = self.fetch_with_retry("/0/private/TradesHistory", params={"ofs": offset})
            parsed_orders.extend(self._convert_orders(ledgers, orders))
            offset += len(orders['result']['trades'].items())
        return parsed_orders

    def get_ledgers(self):
        """Fetches and returns ledger entries."""
        self.ledgers = self.get_paginated_data("/0/private/Ledgers", type='ledger', params={"trades": True})
        return self.ledgers

    def get_transactions(self):
        """Fetches transactions (ledgers) from Kraken API."""

        transactions = self.ledgers.values()  # self.get_paginated_data("/0/private/Ledgers")
        arr_transactions = []
        for t in transactions:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.external_id = t['refid']
            trans.currency = self.clean_symbol(t['asset'])
            trans.value_date = datetime.fromtimestamp(t['time'], timezone.utc)
            if t['type'] == 'withdrawal':
                trans.type = OrderType.WITHDRAWAL
            elif t['type'] == 'deposit':
                trans.type = OrderType.DEPOSIT
            elif t['type'] == 'transfer':
                # not always correct, but it will work
                trans.type = OrderType.AIRDROP
            elif t['type'] == 'staking':
                trans.type = OrderType.STAKING
            elif t['type'] == 'trade':
                continue
            else:
                self._logger.error(f"Undetected type: {t['type']}")
                trans.type = OrderType.DEPOSIT

            if trans.type == OrderType.AIRDROP and float(t['amount']) < 0:
                # This should be a sell - BSV as example
                pass
            trans.amount = round(abs(float(t['amount'])) + float(t['fee']), 8)
            trans.fee = float(t['fee'])
            arr_transactions.append(trans)

        self._logger.info(f"Found {len(arr_transactions)} transactions")
        return arr_transactions

    def _convert_orders(self, ledgers, orders):
        """Converts raw Kraken order data to Order objects."""
        arr_orders = []
        for orderid, order in orders.items():
            # search ledger
            ledger_orders = [o for o in ledgers.values() if o['refid'] == orderid]
            if not ledger_orders:
                self._logger.error(f"NO ledger orders for {orderid}!")
                continue

            new_order = Order()
            new_order.account_id = self.account_id

            new_order.external_id = orderid
            if len(order['pair']) > 6:
                new_order.pair = order['pair'][1:4] + '/' + order['pair'][5:]
            else:
                new_order.pair = order['pair'][:3] + '/' + order['pair'][3:]
            new_order.value_date = datetime.fromtimestamp(order['time'], timezone.utc)
            new_order.type = OrderType.SELL if order['type'] == 'sell' else OrderType.BUY
            new_order.amount = float(order['vol'])
            new_order.fee = 0

            # instead of read the fee from order, we get the fee from ledger because sometimes the fee is applied to the buy item
            # so in that case we decrease the amount bought with the fee
            # if everything looks normal, we get the fee from the sell item as usual
            for l in ledger_orders:
                if f"X{new_order.pair.split('/')[0]}" == l['asset']:
                    new_order.amount -= float(l['fee'])
                elif f"Z{new_order.pair.split('/')[1]}" == l['asset']:
                    new_order.fee += float(l['fee'])

            new_order.price = float(order['price'])
            new_order.cost = float(order['cost'])
            arr_orders.append(new_order)
        return arr_orders

    @staticmethod
    def clean_symbol(kraken_symbol):
        symbol = kraken_symbol
        if len(kraken_symbol) > 3 and (kraken_symbol[0] == 'X' or kraken_symbol[0] == 'Z'):
            symbol = kraken_symbol[1:]

        if symbol.endswith(".F"):
            symbol = symbol.split(".")[0]
        return symbol
