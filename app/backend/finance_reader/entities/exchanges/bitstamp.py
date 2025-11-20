from datetime import datetime, timezone
import hashlib
import hmac
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.exchanges import AbstractExchange
from models.dtos.exchange_dtos import ExchangeWallet, Order, Transaction, OrderType
import pytz


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
        # Transaction type: 0 - deposit; 1 - withdrawal; 2 - market trade; 14 - sub account transfer; 25 -
        # credited with staked assets; 26 - sent assets to staking; 27 - staking reward; 32 -
        # referral reward; 35 - inter account transfer; 33 - settlement transfer; 58 -
        # derivatives periodic settlement; 59 - insurance fund claim; 60 - insurance fund premium; 61 - collateral liquidation.

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
        return list(orders)

    def _convert_orders(self, orders):
        arr_orders = []
        transactions = []
        for order in orders:

            try:
                dt = datetime.strptime(order['datetime'], "%Y-%m-%d %H:%M:%S.%f")
            except:
                dt = datetime.strptime(order['datetime'], "%Y-%m-%d %H:%M:%S")

            if order['type'] == '0' or order['type'] == '1':
                # deposit -> 0 withdraw -> 1
                print("Deposit/Withdrawal", order)
                order['datetime'] = dt
                transactions.append(order)
                continue
            if order['type'] not in ['2', '27']:
                self._logger.error(f"Unknown order type: {order}")
                transactions.append(order)
                continue
            if order['type'] == '27':
                asset = None
                for key, value in order.items():
                    if key not in ['type', 'datetime', 'fee', 'id', 'order_id'] and float(value) != 0.0:
                        asset = key.upper()
                        break
                if not asset:
                    self._logger.error(f"Could not find asset in order: {order}")
                    continue
                self._logger.debug("Set staking order...")
                transactions.append(order)
                continue

            pair = next(p for p in order.keys() if p!='order_id' and '_' in p)
            new_order = Order()
            new_order.account_id = self.account_id
            new_order.external_id = order['id']
            split_pair = pair.split("_")
            new_order.pair = (split_pair[0] + '/' + split_pair[1]).upper()

            print(f"{pair} - {dt}")
            # new_order.value_date = self.convert_text_to_datetime(new_order.value_date)
            dt = dt.replace(tzinfo=pytz.UTC)
            new_order.value_date = dt.astimezone(pytz.timezone("Europe/Madrid"))
            print(f"{pair} final - {new_order.value_date}")
            amount = float(order[pair.split("_")[0]])
            if amount == 0:
                self._logger.debug("Analyze this")
            if 'xrp' in pair and abs(amount) > 18 and abs(amount)<19:
                print("asdad")
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
        transactions.extend(self._process_staking())

        self._logger.info("Found {0} transactions".format(len(transactions)))
        return transactions

    def _process_staking(self):
        staking_orders = []
        for t in self.transactions:
            if t['type'] != '27':
                continue
            trans = Transaction()
            trans.account_id = self.account_id
            trans.type = OrderType.STAKING
            trans.external_id = t['id']
            asset = None
            for key, value in t.items():
                if key not in ['type', 'datetime', 'fee', 'id', 'order_id'] and float(value) != 0.0:
                    asset = key.lower()
                    break

            try:
                dt = datetime.strptime(t['datetime'], "%Y-%m-%d %H:%M:%S.%f")
            except:
                dt = datetime.strptime(t['datetime'], "%Y-%m-%d %H:%M:%S")
            #date = datetime.fromtimestamp(t['datetime'])
            trans.value_date = dt  # - timedelta(hours=1)
            trans.currency = asset.upper()
            trans.amount = t[asset]
            trans.fee = t['fee']
            staking_orders.append(trans)
        return staking_orders

    def _convert_deposit_orders(self, orders):
        transactions = []
        for o in orders:
            trans = Transaction()
            trans.account_id = self.account_id
            trans.external_id = o['txid']
            if 'AIRDROP' in o['txid']:
                trans.type = OrderType.AIRDROP
            else:
                trans.type = OrderType.DEPOSIT
            trans.amount = o['amount']
            #date = datetime.fromtimestamp(o['datetime'])
            #trans.value_date = date # - timedelta(hours=1)
            # trans.value_date = trans.value_date.astimezone(pytz.timezone("Europe/Madrid"))
            trans.value_date = datetime.fromtimestamp(o['datetime'], timezone.utc)
            trans.currency = o['currency']
            trans.rx_address = o['destinationAddress']
            trans.fee = 0
            transactions.append(trans)
        return transactions

    def _convert_withdrawal_orders(self, orders):
        transactions = []
        for o in orders:
            trans = Transaction()
            # search transaction in self.transactions
            # trans.value_date = datetime.fromtimestamp(o['datetime'])
            fee = 0
            for t in self.transactions:
                if o['currency'].lower() not in t:
                    continue
                if t.get('used', None):
                    continue
                if t['type'] != '1':
                    continue
                if abs(float(t[o['currency'].lower()]) - float(t['fee'])) == float(o['amount']):
                    t['used'] = True
                    fee = float(t['fee'])
                    break

            trans.account_id = self.account_id
            trans.type = OrderType.WITHDRAWAL
            trans.external_id = o['txid']
            trans.amount = float(o['amount'])
            #trans.value_date = datetime.fromtimestamp(o['datetime'])
            # trans.value_date = trans.value_date.astimezone(pytz.timezone("Europe/Madrid"))
            # new_order.value_date = datetime.fromtimestamp(order['time'], timezone.utc)
            trans.value_date = datetime.fromtimestamp(o['datetime'], timezone.utc)
            trans.currency = o['currency']
            trans.rx_address = o['destinationAddress']
            trans.fee = fee
            transactions.append(trans)
        return transactions

    def convert_text_to_datetime(self, text_timestamp, timezone="UTC"):
        from datetime import datetime
        import pytz
        from dateutil import parser

        # Parse the text-based timestamp into a datetime object
        dt = parser.parse(text_timestamp)
        if dt.tzinfo is None:
            dt = pytz.UTC.localize(dt)  # If the timestamp is naive (no timezone), assume UTC
        return dt.astimezone(pytz.timezone(timezone))  # Convert to the desired timezone