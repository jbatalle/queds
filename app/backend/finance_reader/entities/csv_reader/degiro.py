from finance_reader.entities.csv_reader import BrokerCSVProcessor
from models.dtos.broker_dtos import Transaction, Ticker
from datetime import datetime
import requests
import json


class Degiro(BrokerCSVProcessor):

    def __init__(self):
        super(Degiro, self).__init__()

    def _get_exchanges(self):
        headers = {
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
        url = "https://trader.degiro.nl/product_search/config/dictionary/"
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            self.log.error(response.text)

        exchanges = {str(e['id']): e for e in response.json().get('exchanges')}
        return exchanges

    def process_csv(self, csv_data, account):
        self.log.info(f"Processing Degiro CSV file for account {account.id}")
        lines = csv_data.splitlines()
        headers = lines[0].split(",")

        isins = list(set([line.split(",")[3] for line in lines[1:]]))
        #tickers = {t.isin: t for t in Ticker.query.all()}
        #missing_tickers = [isin for isin in isins if isin not in tickers]

        exchanges = self._get_exchanges()
        exchanges2 = {e['hiqAbbr']: e for e in exchanges.values()}

        # if missing_tickers:
        #     isin_tickers = self.online_lookup(missing_tickers)
        #     # TODO: create missing tickers
        #     for isin, ticker in isin_tickers.items():
        #         t = Ticker()
        #         t.isin = isin
        #         t.ticker = ticker
        #         tickers[isin] = t

        orders = []
        transactions = []
        split_order = []
        for line in reversed(lines[1:]):
            data = dict(zip(headers, line.split(",")))
            positions = line.split(",")

            t = Transaction()
            shares = int(data['Número'])
            if shares > 0:
                t.type = Transaction.Type.BUY
            else:
                t.type = Transaction.Type.SELL

            t.shares = abs(shares)
            t.price = float(data['Precio'])
            t.name = data['Producto']

            t.ticker = Ticker()
            t.ticker.name = t.name
            t.ticker.ticker = None
            t.ticker.isin = data['ISIN']
            t.ticker.currency = positions[8]
            t.ticker.exchange = data['Bolsa de']

            # t.ticker = tickers[data['ISIN']]
            # TODO: get correct exchange
            # t.ticker.exchange = data['Centro de ejecución']
            try:
                t.ticker.exchange = exchanges2[data['Bolsa de']]['micCode']
            except:
                self.log.warning(f"Unable to detect the exchange for ticker {t.name} - {data['ISIN']}. {data['Bolsa de']} - {data['Centro de ejecución']}")

            # TODO: deactivate ticker when delisted
            t.ticker.active = Ticker.Status.ACTIVE
            date = datetime.strptime(data['Fecha'] + "T" + data['Hora'], "%d-%m-%YT%H:%M")
            # hour = datetime.strptime(data['Fecha'], "%d-%m-%YT%H:%M:%SZ")
            t.value_date = date
            if not data['ID Orden']:
                t.external_id = f"{t.value_date}_{t.ticker.isin}_{t.shares}_{t.price}"
            else:
                t.external_id = data['ID Orden']

            # TODO: missing exchange_fee, we need the Account.csv
            # t.exchange_fee = data['Tipo de cambio']
            t.fee = float(data['Costes de transacción']) if data['Costes de transacción'] else 0
            t.currency_rate = 1 / float(data['Tipo de cambio'] if data['Tipo de cambio'] else 1)
            t.currency = positions[8]

            # check HOUR in order to identify split
            if t.type == Transaction.Type.BUY and not data['ID Orden']:
                t.type = Transaction.Type.SPLIT_BUY
            elif t.type == Transaction.Type.SPLIT_BUY and not data['ID Orden']:
                t.type = Transaction.Type.SPLIT_SELL

            if data['Bolsa de'] == 'OTC':
                t.type = Transaction.Type.OTC_BUY
            orders.append(t)

        return orders, transactions

    def get_ticker_from_isin(self):
        pass

    def online_lookup(self, isins):
        self.log.info("Try to fetch symbol for: {}".format(isins))
        url = 'https://api.openfigi.com/v3/mapping'
        headers = {'Content-Type': 'text/json'}
        batch_size = 10

        payload = []
        results = []
        for isin in isins:
            payload.append({"idType":"ID_ISIN", "idValue": isin})

        for i in range(0, len(isins), batch_size):
            batch = isins[i:i + batch_size]
            payload = [{"idType": "ID_ISIN", "idValue": isin} for isin in batch]

            try:
                rsp = requests.post(url, headers=headers, data=json.dumps(payload))

                if rsp.ok:
                    results.extend(rsp.json())
                else:
                    print(f"Failed to send batch starting at {i}. Status code: {rsp.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Request failed: {e}")

        print(f"Found {len(results)} symbols")
        i = 0
        isin_ticker = {}
        for k in results:
            if 'error' not in k and k['data']:
                if k['data'][0]['ticker'] in ['LITBUSD', 'LITB', 'HOTHUSD', 'DNREUR', 'BIOCEUR', 'TTOOEUR', 'AYTUUSD']:
                    pass
                isin_ticker[isins[i]] = k['data'][0]['ticker']
            else:
                isin_ticker[isins[i]] = self.get_ticker(isins[i])
            i += 1
        return isin_ticker

    def get_ticker(self, isin):
        self.log.info(f"Try to fetch symbol for: {isin}")
        r = requests.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={isin}", headers={
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8,es;q=0.6,ca;q=0.4',
                'Accept-Encoding': 'deflate'
            })
        d = r.json()['quotes']
        if not d:
            print(f"Unable to get symbol for: {isin}")
            return None
        return d[0]['symbol']