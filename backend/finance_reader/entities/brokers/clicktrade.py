from datetime import datetime
import re
from bs4 import BeautifulSoup
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.brokers import AbstractBroker
from finance_reader.entities.brokers.dtos import BrokerAccount, Transaction, Ticker


class Clicktrade(AbstractBroker):

    def __init__(self):
        super(Clicktrade, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {
            "cache-control": "no-cache",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.clicktrade.es",
            "pragma": "no-cache",
            "referer": "https://www.clicktrade.es/",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "sec-fetch-site": "same-origin",
            "sec-fetch-user": "?1",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        }
        self.account_id = None
        self.session_id = None
        self.client_key = None

    def login(self, username, password):
        url = "https://www.clicktrade.es/Broker//Account/Login"
        data = {
            "username": username,
            "password": password,
            "sourceUrl": "https://www.clicktrade.es/"
        }
        response = self._client.post(url, data)
        html = BeautifulSoup(response.text, 'html.parser')
        form = html.find('form', id='saxoSamlForm')
        saml_response = form.find('input', attrs={'name': 'SAMLResponse'}).get('value')

        url = "https://fssoclicktrader.clicktrade.es/login.sso.ashx"
        data = {
            "SAMLResponse": saml_response,
            "PageLoadInfo": ""
        }
        response1 = self._client.post(url, data)
        html = BeautifulSoup(response1.text, 'html.parser')
        form = html.find('form', id='form')
        saml_request = form.find('input', attrs={'name': 'SAMLRequest'}).get('value')
        data = {
            "SAMLRequest": saml_request,
            "PageLoadInfo": ""
        }
        url = "https://live.logonvalidation.net/AuthnRequest"
        response2 = self._client.post(url, data)

        html = BeautifulSoup(response2.text, 'html.parser')
        form = html.find('form', id='form')
        saml_response = form.find('input', attrs={'name': 'SAMLResponse'}).get('value')

        url = "https://fssoclicktrader.clicktrade.es/login.sso.ashx"
        data = {
            "SAMLResponse": saml_response,
            "PageLoadInfo": ""
        }
        response3 = self._client.post(url, data)
        token = re.search('sso\/oapi\/BEARER (.*?)\/', response3.text).group(1)

        b = self._client.get("https://fssoclicktrader.clicktrade.es/api/localization/all?locale=es&v=11.143.4")
        self._client.headers.update({
            "origin": "https://fssoclicktrader.clicktrade.es",
            "referer": "https://fssoclicktrader.clicktrade.es/d",
            "authorization": "BEARER {}".format(token)
        })

        b = self._client.get("https://fssoclicktrader.clicktrade.es/openapi/port/v1/users/me")
        me = b.json()
        self.client_key = me.get('ClientKey')

        self._client.headers.update({
            "origin": "https://fssoclicktrader.clicktrade.es",
            "referer": "https://fssoclicktrader.clicktrade.es/d"
        })
        self._logger.info("Get trades:")

        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        url = "https://fssoclicktrader.clicktrade.es/openapi/hist/v1/reports/balancesandequities/{}/{}/{}/?CurrencyType=Account"
        response5 = self._client.get(url.format(self.client_key, to_date, to_date))
        d = response5.json()

        entity_account = BrokerAccount()
        entity_account.balance = d.get('Data')[0]['EndBalance']
        entity_account.virtual_balance = d.get('Data')[0]['EndEquity']
        return entity_account

    def get_bookings(self, trade_id):
        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        url = "https://fssoclicktrader.clicktrade.es/openapi/cs/v1/reports/bookings/{}?fromDate=2021-01-27&toDate={}&FilterType=RelatedTradeId&FilterValue={}".format(
            self.client_key, to_date, trade_id)
        response4 = self._client.get(url)
        if response4.status_code != 200:
            self._logger.error("Error reading bookings from clicktrade trade {}!!!".format(trade_id))
        return response4.json()

    def check_if_tradeable(self, isin):
        url = "https://fssoclicktrader.clicktrade.es/openapi/ref/v1/instruments/?$top=201&$skip=0&includeNonTradable=true&AssetTypes=Stock%2CEtf%2CEtc%2CEtn%2CFund%2CRights%2CCompanyWarrant%2CStockIndex&keywords={}&OrderBy=Popularity&ClientKey={}"
        response4 = self._client.get(url.format(isin, self.client_key))
        if response4.status_code != 200:
            self._logger.error("Error, unable to search isin {}!!!".format(isin))
        return response4.json()

    def read_transactions(self, start_date):
        url = "https://fssoclicktrader.clicktrade.es/openapi/cs/v1/reports/trades/{}?fromDate={}&toDate={}"
        start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        response4 = self._client.get(url.format(self.client_key, start_date, to_date))
        if response4.status_code != 200:
            self._logger.error(f"Error reading transactions:  {response4.text}")
        data = response4.json()

        to_insert = []
        for d in data.get("Data"):
            isin = d['ISINCode']
            symbol, exchange_mic = d['InstrumentSymbol'].upper().split(":")
            if ':' in symbol:
                self._logger.warning("Unknown market: {}".format(d['InstrumentSymbol']))

            detail = self.get_bookings(d['TradeId'])

            if d.get('AssetType') == 'Rights':
                continue

            if not detail:
                self._logger.warning(f"NO detail for isin: {isin}")
                continue

            if not detail.get('Data'):
                self._logger.error(f"NO DATA detail for isin: {isin} - {d.get('AssetType')}")
                # continue

            fee = 0
            currency_rate = 0
            currency = 0
            exchange_fee = 0
            for q in detail.get('Data', []):
                if q['BkAmountType'] == "Exchange Fee":
                    exchange_fee = q['Amount']
                    continue
                if q['BkAmountType'] != 'Commission':
                    self._logger.warning(q['BkAmountType'])
                    continue
                fee = q['Amount'] * q['ConversionRate']
                currency_rate = q['ConversionRate']
                currency = q['Currency']
                break

            products = self.check_if_tradeable(isin)
            status = Ticker.Status.ACTIVE
            if not len(products['Data']):
                status = Ticker.Status.INACTIVE

            ticker = Ticker()
            ticker.isin = isin
            ticker.ticker = symbol
            ticker.name = d['InstrumentDescription']
            ticker.active = status
            ticker.exchange = exchange_mic

            t = Transaction()
            t.name = d['InstrumentDescription'],  # 14578496
            t.ticker = ticker
            t.value_date = d['TradeDate']
            t.external_id = d['OrderId']
            t.shares = abs(int(d['Amount']))
            t.type = Transaction.Type.BUY if d.get('TradeEventType') == 'Bought' else Transaction.Type.SELL,  # B/S
            t.price = d['Price']
            t.fee = fee
            t.exchange_fee = exchange_fee
            t.currency_rate = currency_rate
            t.currency = currency if currency else None

            to_insert.append(t)

        return to_insert
