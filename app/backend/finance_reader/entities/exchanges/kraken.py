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
        self._logger.info("Get Kraken Closed orders")
        ledgers = self.get_ledgers()

        orders = self.get_paginated_data("/0/private/TradesHistory", type='trades', params={"ofs": 0, "trades": True})

        #orders = self.fetch_with_retry("/0/private/TradesHistory", params={"ofs": 0, "trades": True})
        parsed_orders = self._convert_orders(ledgers, orders)

        # Pagination for additional orders
        #parsed_orders.extend(self.get_paginated_orders(orders['result']['count'], ledgers))
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
        # TODO: check ETH.F,ETHW, SGB... deposits
        transactions = self.ledgers.values()  # self.get_paginated_data("/0/private/Ledgers")
        arr_transactions = []
        for t in transactions:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.external_id = t['refid']
            trans.currency = self.clean_symbol(t['asset'])
            if trans.currency == 'BSV':
                print("CHeck")
            trans.value_date = datetime.fromtimestamp(t['time'])
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
                # THIS should be a sell - BSV as example
                pass
            trans.amount = abs(float(t['amount'])) + float(t['fee'])
            trans.fee = t['fee']
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

            new_order.type = OrderType.SELL if order['type'] == 'sell' else OrderType.BUY

            new_order.amount = float(order['vol'])
            for l in ledger_orders:
                if f"X{order['pair'].split('/')[0]}" == l['asset']:
                    new_order.amount -= l['fee']
                    # TODO: remove fee?

            new_order.price = float(order['price'])
            new_order.cost = float(order['cost'])
            new_order.fee = float(order['fee'])
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

    def get_transactions_old(self):
        self._logger.info("Get transactions...")
        total_transactions = []
        offset = 0
        i = 0
        while i < 5:
            try:
                transactions = self.query("/0/private/Ledgers", params={"ofs": 0}).json()
            except Exception as e:
                self._logger.error(e)
                return

            if 'result' in transactions:
                break

            self._logger.error(transactions)
            i += 1
            time.sleep(5)

        total_transactions.extend(transactions['result']['ledger'].values())
        max_count = transactions['result']['count']
        offset += 50
        while offset < max_count:
            time.sleep(5)
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
            trans.amount = abs(float(t['amount'])) + t['fee']
            trans.fee = t['fee']
            arr_transactions.append(trans)

        self._logger.info("Found {0} transactions".format(len(arr_transactions)))
        return arr_transactions

    def identifying_fees(self):
        a = {
  'aclass': 'forex',
  'cost': '22.12090',
  'fee': '0.05751',
  'leverage': '0','maker': False,'margin': '0.00000','misc': '','ordertxid': 'OUQT2M-M36RE-INY4ID','ordertype': 'market', 'pair': 'XETHZEUR',
  'price': '248.96000',
 'time': 1508704405.071527,'trade_id': 5980568,  'type': 'buy',
  'vol': '0.08885322'
}
        b = {
  'aclass': 'forex',
  'cost': '24.90000',
  'fee': '0.06474',
  'leverage': '0',   'maker': False,  'margin': '0.00000',  'misc': '','ordertxid': 'OYS4QF-NF4XC-OY3WYX','ordertype': 'market',   'pair': 'XETHZEUR',
    'price': '249.00000',
  'time': 1508704366.045528,   'trade_id': 5980567, 'type': 'buy',
  'vol': '0.10000000'
}
        total_cost = a['vol']*a['price']
        a_cost = round(float(a['vol'])*float(a['price']) + float(a['fee']), 5)
        b_cost = round(float(b['vol'])*float(b['price']) + float(b['fee']), 5)
        print(a_cost)
        print(b_cost)

        vol_a = float(a['cost'])/float(a['price'])
        vol_b = float(b['cost']) / float(b['price'])
        print(vol_a)
        print(vol_b)

        balance1 = self.calculate_final_eth(a)
        balance2 = self.calculate_final_eth(b)
        print("Order 1 ", balance1)
        print("Order 2 ", balance2)

        detect_fee_method(a)
        detect_fee_method(b)

    @staticmethod
    def calculate_final_eth(order):
        cost = float(order['cost'])  # Cost in EUR
        fee = float(order['fee'])  # Fee in EUR
        vol = float(order['vol'])  # Volume (ETH)
        price = float(order['price'])  # Price in EUR per ETH
        volume = float("{:0.8f}".format(cost/price))
        import math
        volume = math.floor((cost / price) * 10 ** 8) / 10 ** 8
        adjusted_vol = vol - (fee / price)

        if volume == vol:
            # fee is in target ETH
            eth_fee = fee / price
            balance = vol - eth_fee
        else:
            # fee is in EUR
            balance = vol

        return balance, cost

    def detect_fee_method(order):
        volume = float(order['vol'])
        cost = float(order['cost'])
        fee = float(order['fee'])
        price = float(order['price'])

        # Calculate theoretical cost based on volume and price
        expected_cost = volume * price

        # Calculate fee as percentage
        fee_percentage = fee / cost

        # If fee was applied to EUR:
        # The pretax cost would be (cost - fee)
        # And volume would be exactly as reported
        if_eur_fee_expected_volume = (cost - fee) / price
        eur_fee_volume_diff = abs(volume - if_eur_fee_expected_volume) / volume

        # If fee was applied to ETH:
        # The reported volume would be post-fee
        # And the original volume would be (volume + fee_in_eth)
        fee_in_eth = fee / price
        if_eth_fee_original_volume = volume + fee_in_eth
        if_eth_fee_expected_cost = if_eth_fee_original_volume * price
        eth_fee_cost_diff = abs(cost - if_eth_fee_expected_cost) / cost

        # Additional check: look at the roundness of volume
        # Volumes like 0.10000000 suggest EUR fee (user specified exact ETH amount)
        # Less round volumes suggest ETH fee
        volume_roundness = len(order['vol'].rstrip('0').split('.')[1]) if '.' in order['vol'] else 0

        print(volume_roundness)
        # Combine the evidence
        if volume_roundness == 0 or volume_roundness <= 5:
            # Round volume suggests EUR fee
            if eur_fee_volume_diff < 0.01:  # Within 1% margin of error
                print("Fee applied to EUR")
                return "Fee applied to EUR"

        # Compare differences - smaller difference indicates likely method
        print(eth_fee_cost_diff, eur_fee_volume_diff)
        if eth_fee_cost_diff < eur_fee_volume_diff:
            print("ETH")
            return "Fee applied to ETH"
        else:
            print("EUR")
            return "Fee applied to EUR"
