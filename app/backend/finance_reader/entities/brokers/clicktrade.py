from datetime import datetime
import re
import time
from bs4 import BeautifulSoup
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.brokers import AbstractBroker
from models.dtos.broker_dtos import BrokerAccount, Transaction, Ticker


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
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        }
        self.account_id = None
        self.session_id = None
        self.client_key = None
        self.is_tradeable = {}

    def login(self, data):
        url = "https://www.clicktrade.es/Broker//Account/Login"
        data = {
            "username": data.get('username'),
            "password": data.get('password'),
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

    def get_bookings(self, trade_id, retry=0):
        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        url = "https://fssoclicktrader.clicktrade.es/openapi/cs/v1/reports/bookings/{}?fromDate=2021-01-27&toDate={}&FilterType=RelatedTradeId&FilterValue={}".format(
            self.client_key, to_date, trade_id)
        response4 = self._client.get(url)
        if response4.status_code == 200:
            return response4.json()

        self._logger.error("Error reading bookings from clicktrade trade {}!!!".format(trade_id))
        if response4.status_code == 401:
            return {}
        elif response4.status_code != 209 and retry < 5:
            self._logger.warning(f"Waiting... server overloaded. Code: {response4.status_code}. Retry {retry}")
            time.sleep(35)
            return self.get_bookings(trade_id, retry+1)

        return response4.json()

    def check_if_tradeable(self, isin):
        if isin in self.is_tradeable:
            return self.is_tradeable[isin]
        url = "https://fssoclicktrader.clicktrade.es/openapi/ref/v1/instruments/?$top=201&$skip=0&includeNonTradable=true&AssetTypes=Stock%2CEtf%2CEtc%2CEtn%2CFund%2CRights%2CCompanyWarrant%2CStockIndex&keywords={}&OrderBy=Popularity&ClientKey={}"
        response = self._client.get(url.format(isin, self.client_key))
        if response.status_code != 200:
            self._logger.error("Error, unable to search isin {}!!!".format(isin))
        self.is_tradeable[isin] = response.json()['Data']
        return response.json()['Data']

    def read_transactions(self, start_date):
        url = "https://fssoclicktrader.clicktrade.es/openapi/hist/v1/transactions?ClientKey={}&FromDate={}&ToDate={}"#&AccountKeys={}"
        start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        response4 = self._client.get(url.format(self.client_key, start_date, to_date))
        if response4.status_code != 200:
            self._logger.error(f"Error reading transactions:  {response4.text}")
        data = response4.json()

        self._logger.info(f"Start processing orders. Total to process: {len(data.get('Data'))}")
        to_insert = []

        events = {}
        for d in data.get("Data"):
            if d['Event'] not in events:
                events[d['Event']] = []
            events[d['Event']].append(d)

        # types: [{'Intermediate Securities Distribution', 'Sell', 'Transfer Out', 'Worthless', 'Reverse Stock Split', 'Exchange', 'Cash Dividend', 'Odd Lot Sale Purchase\t', 'Dividend Option', 'Deposit', 'Buy', 'Transfer In'}]
        for d in data.get("Data"):
            if d['TransactionType'] in ["CashTransfer"]:
                continue

            if not d['Instrument']['Symbol']:
                continue

            isin = d['Instrument']['ISINCode']
            currency = d['Instrument']['Currency']
            trade_id = None
            shares = 0
            price = 0
            date = None
            fee = 0
            exchange_fee = 0
            currency_rate = 1
            trans_type = None

            if isin != "US9344231041":
                pass
                # continue

            if isin == 'US92343V1044':
                print("Verizon")
            if isin == 'VGG1890L1076':
                print("Check exchange fee; -9.20, -3.97, total_cost: -13.12€")
            if isin == 'US8116994042':
                print("Check exchange fee; -")

            symbol, exchange_mic = d['Instrument']['Symbol'].upper().split(":")
            if ':' in symbol:
                self._logger.warning("Unknown market: {}".format(d['InstrumentSymbol']))

            status = Ticker.Status.ACTIVE

            ticker = Ticker()
            ticker.isin = isin
            ticker.ticker = symbol
            ticker.name = d['Instrument']['Description']
            ticker.active = status
            ticker.currency = currency
            ticker.exchange = exchange_mic

            self._logger.info(f"Processing {isin} - {symbol} - {d['Event']}")

            for q in d.get('Bookings', []):
                currency_rate = q['ConversionRate']
                if q['AmountType'] in ["Exchange Fee"]:
                # if q['CostClass'] == 'TransactionCosts':
                    exchange_fee += -abs(q['BookedAmount'])
                    fee += -abs(q['ConversionCost'])
                    continue
                if q['AmountType'] == 'Share Amount':
                    fee += -abs(q['ConversionCost'])
                    continue

                if q['CostClass'] != 'TransactionCosts':
                    self._logger.warning(f"Amount type: {q['AmountType']} - {q['BookedAmount']}")
                    continue

                fee += -abs(q['BookedAmount'])
                fee += -abs(q['ConversionCost'])

            self._logger.debug(f"{symbol}. Fee: {fee} - Rate: {currency_rate}")
            if d['Event'] == 'Exchange':
                # stock dividend, like IBE
                if d['Bookings'] and d['Bookings'][0]['AmountType'] in ['Corporate Actions', 'Corporate Actions - Fractions']:
                    self._logger.info("Stock dividend, not required to track, not taxed")
                    continue
                for t in d['Trades']:
                    if t['TradeEventType'] == 'Sold' and t['TradedValue'] > 0:
                        # create sell order
                        shares = abs(int(t['TradedValue']))
                        price = t['Price']
                        date = t['TradeExecutionTime']
                        trans_type = Transaction.Type.SELL
                    elif t['TradeEventType'] == 'Bought' and t['TradedQuantity'] > 0:
                        # create buy order, no price
                        symbol, exchange_mic = t['Instrument']['Symbol'].upper().split(":")
                        ticker = Ticker()
                        ticker.isin = t['Instrument']['ISINCode']
                        ticker.ticker = symbol
                        ticker.currency = t['Instrument']['Currency']
                        ticker.active = Ticker.Status.ACTIVE
                        ticker.name = t['Instrument']['Description']
                        ticker.exchange = exchange_mic

                        shares = abs(int(t['TradedQuantity']))
                        price = 1
                        trans_type = Transaction.Type.BUY
                        trade_id = t['TradeId']
                        date = t['TradeExecutionTime']

            elif d['Event'] in ['Cash Dividend', 'Dividend Option']:
                continue
                for b in d['Bookings']:
                    # TODO: calculate taxes and set sell order
                    pass
            elif d['Event'] in ['Worthless', 'Spin-Off']:
                continue
            elif d['Event'] == 'Buy':
                trans_type = Transaction.Type.BUY
                if len(d['Trades']) > 1:
                    print("asdsa")
                for t in d['Trades']:
                    trade_id = t['TradeId']
                    date = t['TradeExecutionTime']
                    shares += abs(int(t['TradedQuantity']))
                    price = t['Price']
            elif d['Event'] == 'Sell' and d.get('OriginalTradeId', 0) == 0:
                if len(d['Trades']) > 1:
                    print("asdsa")
                trans_type = Transaction.Type.SELL
                for t in d['Trades']:
                    trade_id = t['TradeId']
                    date = t['TradeExecutionTime']
                    shares += abs(int(t['TradedQuantity']))
                    price = t['Price']
            elif d['Event'] == 'Reverse Stock Split':
                to_insert.extend(self.generate_split_orders(ticker, d['Trades']))
                continue
            elif d['Event'].strip() == 'Odd Lot Sale Purchase':
                trans_type = Transaction.Type.SELL
                for t in d['Trades']:
                    trade_id = t['TradeId']
                    date = t['TradeExecutionTime']
                    shares += abs(int(t['TradedQuantity']))
                    price = t['Price']
                pass
            elif d['Event'] in ['Transfer In', 'Transfer Out']:
                continue
            else:
                self._logger.warning(f"Type not recognized: {d.get('Event')}")
                continue

            # TODO: is tradeable?
            # products = self.check_if_tradeable(isin)
            status = Ticker.Status.ACTIVE
            # if not len(products):
            #     status = Ticker.Status.INACTIVE
            #
            # if len(products) > 1:
            #     self._logger.warning(f"Check multiple tradeable products for {isin}")
            #     products = [p for p in products if p['Identifier'] == d.get('Uic')]
            #     if not len(products):
            #         self._logger.warning(f"No products found for {isin}")
            #         continue
            # if not products:
            #     self._logger.warning(f"Product {d['InstrumentSymbol']} not found. Probably delisted")
            #     product = {
            #         "Symbol": d['InstrumentSymbol'],
            #         "Description": d['InstrumentDescription'],
            #         "CurrencyCode": currency
            #     }
            # else:
            #     product = products[0]
            #
            # new_symbol, new_exchange_mic = product['Symbol'].upper().split(":")
            # if new_symbol != symbol:
            #     self._logger.warning(f"Different symbol: {new_symbol} vs {symbol}. Saving {new_symbol}")
            #
            # if d['InstrumentDescription'] != product['Description']:
            #     self._logger.warning(
            #         f"Different description: {d['InstrumentDescription']} vs {product['Description']}")

            if trans_type is None:
                self._logger.warning(f"Type not recognized: {d.get('Event')}")
                continue

            t = Transaction()
            t.name = d['Instrument']['Description']  # 14578496
            t.ticker = ticker
            t.value_date = date
            t.external_id = trade_id
            t.shares = shares
            t.type = trans_type
            t.price = price
            t.fee = fee
            t.exchange_fee = exchange_fee
            t.currency_rate = currency_rate
            t.currency = currency if currency else ticker.currency

            to_insert.append(t)

        return to_insert

    def generate_split_orders(self, ticker, trades):
        orders = []
        for trade in trades:
            if trade['TradeEventType'] == 'Sold':
                trans_type = Transaction.Type.SPLIT_SELL
            else:
                trans_type = Transaction.Type.SPLIT_BUY

            t = Transaction()
            t.name = ticker.name  # 14578496
            t.ticker = ticker
            t.value_date = trade['TradeExecutionTime']
            t.external_id = trade['TradeId']
            t.shares = abs(int(trade['TradedQuantity']))
            t.type = trans_type
            t.price = trade['Price']
            t.fee = 0
            t.exchange_fee = 0
            t.currency_rate = 1
            t.currency = ticker.currency

            orders.append(t)
        return orders

    @staticmethod
    def get_fees(self, bookings):
        fee = 0
        currency_rate = 1
        currency = None
        exchange_fee = 0
        for q in bookings:
            if q['BkAmountType'] == "Exchange Fee":
                exchange_fee = q['Amount']
                continue
            if q['BkAmountType'] != 'Commission':
                self._logger.warning(f"Amount type: {q['BkAmountType']} - {q['Amount']}")
                continue
            fee = q['Amount'] * q['ConversionRate']
            currency_rate = q['ConversionRate']
            currency = q['Currency']
            break
        return fee, currency_rate, exchange_fee

    def read_transactions2(self, start_date):
        url = "https://fssoclicktrader.clicktrade.es/openapi/cs/v1/reports/trades/{}?fromDate={}&toDate={}"
        start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")
        to_date = datetime.now().strftime("%Y-%m-%d")  # 2021-01-27
        response4 = self._client.get(url.format(self.client_key, start_date, to_date))
        if response4.status_code != 200:
            self._logger.error(f"Error reading transactions:  {response4.text}")
        data = response4.json()

        self._logger.info(f"Start processing orders. Total to process: {len(data.get('Data'))}")
        to_insert = []
        for d in data.get("Data"):
            isin = d['ISINCode']
            if isin == 'CA0079755017':
                print("Check")
            if isin == 'US92343V1044':
                print("Verizon")
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
                self._logger.error(f"NO DATA detail for isin: {isin} - {d.get('AssetType')} - Trade: {d['TradeId']}")
                # continue

            fee = 0
            currency_rate = 1
            currency = None
            exchange_fee = 0
            for q in detail.get('Data', []):
                if q['BkAmountType'] == "Exchange Fee":
                    exchange_fee = q['Amount']
                    continue
                if q['BkAmountType'] != 'Commission':
                    self._logger.warning(f"amount type: {q['BkAmountType']} - {q['Amount']}")
                    continue
                fee = q['Amount'] * q['ConversionRate']
                currency_rate = q['ConversionRate']
                currency = q['Currency']
                break

            products = self.check_if_tradeable(isin)
            status = Ticker.Status.ACTIVE
            if not len(products):
                status = Ticker.Status.INACTIVE

            if len(products) > 1:
                self._logger.warning(f"Check multiple tradeable products for {isin}")
                products = [p for p in products if p['Identifier'] == d.get('Uic')]
                if not len(products):
                    self._logger.warning(f"No products found for {isin}")
                    continue
            if not products:
                self._logger.warning(f"Product {d['InstrumentSymbol']} not found. Probably delisted")
                product = {
                    "Symbol": d['InstrumentSymbol'],
                    "Description": d['InstrumentDescription'],
                    "CurrencyCode": currency
                }
            else:
                product = products[0]

            new_symbol, new_exchange_mic = product['Symbol'].upper().split(":")
            if new_symbol != symbol:
                self._logger.warning(f"Different symbol: {new_symbol} vs {symbol}. Saving {new_symbol}")

            if d['InstrumentDescription'] != product['Description']:
                self._logger.warning(f"Different description: {d['InstrumentDescription']} vs {product['Description']}")

            ticker = Ticker()
            ticker.isin = isin
            ticker.ticker = new_symbol
            ticker.name = product['Description']
            ticker.active = status
            ticker.currency = product['CurrencyCode']
            ticker.exchange = exchange_mic

            if d.get('CaEventTypeName', '') == 'Reverse Stock Split':
                if d['TradeEventType'] == 'Sold':
                    trans_type = Transaction.Type.SPLIT_SELL
                else:
                    trans_type = Transaction.Type.SPLIT_BUY
#            elif d.get('CaEventTypeName', '').strip() == 'Odd Lot Sale Purchase':
            elif d.get('TradeEventType') == 'Bought':
                trans_type = Transaction.Type.BUY
            elif d.get('TradeEventType') == 'Sold':
                trans_type = Transaction.Type.SELL
            elif d.get('TradeEventType') == 'Worthless':
                continue
            elif d.get('TradeEventType') == 'Spin-Off':
                continue
            else:
                self._logger.warning(f"Type not recognized: {d.get('TradeEventType')}")
                continue

            t = Transaction()
            t.name = d['InstrumentDescription'],  # 14578496
            t.ticker = ticker
            t.value_date = d['TradeDate']
            t.external_id = d['OrderId']
            t.shares = abs(int(d['Amount']))
            t.type = trans_type
            t.price = d['Price']
            t.fee = fee
            t.exchange_fee = exchange_fee
            t.currency_rate = currency_rate
            t.currency = currency if currency else ticker.currency

            to_insert.append(t)

        return to_insert
