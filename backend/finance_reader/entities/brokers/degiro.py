from datetime import datetime
import pytz as tz
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.brokers import AbstractBroker
from finance_reader.entities.brokers.dtos import BrokerAccount, Transaction, Ticker


class Degiro(AbstractBroker):

    def __init__(self):
        super(Degiro, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {
            "cache-control": "no-cache",
            "origin": "https://trader.degiro.nl",
            "pragma": "no-cache",
            "referer": "https://trader.degiro.nl/login/es",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        }
        self.account_id = None
        self.session_id = None

    def login(self, username, password):
        url = "https://trader.degiro.nl/login/secure/login"
        data = {
            "username": username,
            "password": password,
            "queryParams": {}
        }
        r = self._client.post(url, json=data)
        data = r.json()
        if data['status'] != 0 or data['statusText'] != "success":
            self._logger.error(data)
            raise Exception("Invalid credentials!")

        self.session_id = data['sessionId']
        self.account_id = self.get_account_id()
        url = "https://trader.degiro.nl/trading/secure/v5/update/{};jsessionid={}"
        payload = {
            'intAccount': self.account_id,
            'sessionId': self.session_id,
            'cashFunds': 0,
            'orders': 0,
            'portfolio': 0,
            'totalPortfolio': 0,
            'historicalOrders': 0,
            'transactions': 0,
            'alerts': 0
        }
        r = self._client.get(url.format(self.account_id, self.session_id), params=payload)
        data = r.json()
        cashfund = {}
        for currency in data["cashFunds"]["value"]:
            for parameter in currency["value"]:
                if parameter["name"] == "currencyCode":
                    code = parameter["value"]
                if parameter["name"] == "value":
                    value = parameter["value"]
            cashfund[code] = value

        sum = 0
        for currency in data["portfolio"]["value"]:
            for parameter in currency["value"]:
                if 'value' not in parameter:
                    continue
                if parameter["name"] == "value":
                    sum += parameter["value"]

        entity_account = BrokerAccount()
        entity_account.entity_id = ''
        entity_account.balance = cashfund["EUR"]
        entity_account.virtual_balance = sum + cashfund["EUR"]
        return entity_account

    def get_account_id(self):
        url = 'https://trader.degiro.nl/pa/secure/client'
        payload = {'sessionId': self.session_id}

        r = self._client.get(url, params=payload)
        data = r.json()
        acc_id = data['data']['intAccount']
        return acc_id

    def _get_product(self, product_ids):
        url = "https://trader.degiro.nl/product_search/secure/v5/products/info?intAccount={}&sessionId={}"
        response = self._client.post(url.format(self.account_id, self.session_id), json=list(set(product_ids)))
        if response.status_code != 200:
            self._logger.error(response.text)

        return response.json().get('data')

    def read_transactions(self, start_date):
        url = "https://trader.degiro.nl/reporting/secure/v4/transactions?fromDate={}&toDate={}&groupTransactionsByOrder=true&intAccount={}&sessionId={}"
        end_date = datetime.now().strftime("%d/%m/%Y")  # "12/01/2019"
        r = self._client.get(url.format(start_date, end_date, self.account_id, self.session_id))
        data = r.json()

        products = self._get_product([str(p['productId']) for p in data.get('data')])

        to_insert = []
        for d in data.get('data'):
            product = products[str(d.get('productId'))]
            product_name = product.get('name')
            product_isin = product.get('isin')
            symbol = product.get('symbol')
            active = Ticker.Status.ACTIVE if product.get('tradable') else Ticker.Status.INACTIVE

            ticker = Ticker()
            ticker.ticker = symbol
            ticker.name = product_name
            ticker.isin = product_isin
            ticker.active = active

            value_date = datetime.fromisoformat(d.get('date')).replace(hour=0, minute=0)
            value_date = value_date.replace(tzinfo=tz.timezone("America/Los_Angeles"))
            fee = d.get('feeInBaseCurrency', 0)  # in €
            rate = 1
            exchange_fee = 0
            if 'fxRate' in d and d.get('fxRate') and d['quantity'] != 0 and d['price'] > 0:
                raw_eur_price = d['quantity'] * d['price'] / d.get('fxRate', 1)
                # exchange_fee = round(d['totalInBaseCurrency'] * 0.001, 4)  # AutoFX
                if raw_eur_price > 0:
                    exchange_fee = -1 * round(raw_eur_price * 0.001, 4)  # AutoFX
                else:
                    exchange_fee = round(raw_eur_price * 0.001, 4)  # AutoFX
                rate = (raw_eur_price + exchange_fee) / (
                            d['quantity'] * d['price'])  # eur_price with rate_fee / price_usd

            t = Transaction()
            t.name = product_name
            t.ticker = ticker
            t.value_date = value_date
            t.external_id = d['id']
            t.shares = abs(d['quantity'])
            t.type = Transaction.Type.BUY if d.get('buysell') == 'B' else Transaction.Type.SELL,  # B/S
            t.price = d['price']
            t.fee = fee
            t.exchange_fee = exchange_fee
            t.currency_rate = rate
            t.currency = product.get('currency')

            to_insert.append(t)

        return to_insert
