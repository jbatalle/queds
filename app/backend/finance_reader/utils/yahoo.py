import requests
import csv
import requests.utils
import logging
import json
import os


logger = logging.getLogger(__name__)


class YahooClient:

    def __init__(self):
        self.client = requests.Session()
        self.client.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.110 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8,es;q=0.6,ca;q=0.4',
                'Accept-Encoding': 'deflate'
            }
        )

        self.exchange_mic = {}
        self._get_iso_codes()

    def _get_iso_codes(self):
        iso_file = "finance_reader/utils/ISO10383_MIC_NewFormat.csv"
        if not os.path.exists(iso_file):
            iso_file = "backend/finance_reader/utils/ISO10383_MIC_NewFormat.csv"
        with open(iso_file) as f:
            reader = csv.reader(f, delimiter=',')
            for idx, row in enumerate(reader):
                if idx == 0:
                    continue
                self.exchange_mic[row[0]] = {
                    "mic": row[1],
                    "name": row[3],
                    "acronym": row[7],
                    "deleted": True if row[11] == 'DELETED' else False
                }

    def get_ticker(self, ticker):
        # logger.debug(f"Trying to fetch symbol from yahoo for isin {ticker.isin}")
        search_by = ticker.isin if not ticker.ticker else ticker.ticker
        r = self.client.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={search_by}&newsCount=0")
        d = r.json()['quotes']
        items = [c for c in d if c['typeDisp'] == 'Equity']
        yahoo_symbol = None
        if not ticker.ticker:
            # search ticker by ISIN
            pass

        # search yahoo symbol
        for item in items:
            if item['symbol'] == ticker.ticker:
                if item['exchDisp'] == ticker.exchange or item['exchDisp'] == self.exchange_mic.get(ticker.exchange,
                                                                                                    {}).get('acronym'):
                    yahoo_symbol = item['symbol']
                    break
                else:
                    logger.warning(f"Check ticker exchange {ticker.ticker} - {ticker.exchange}")

            if ticker.exchange and (
                    item['exchange'] in ticker.exchange or item['exchange'] in self.exchange_mic.get(ticker.exchange,
                                                                                                     {"acronym": ""}).get(
                    'acronym')):
                logger.warning(f"Check ticker exchange {ticker.ticker} - {ticker.exchange}")

                if not ticker.ticker:
                    yahoo_symbol = item['symbol']
                    break
                if ticker.ticker in item['symbol']:
                    yahoo_symbol = item['symbol']
                    break

        if not yahoo_symbol:
            logger.error(f"Unable to detect the Yahoo symbol for {ticker.ticker} - {ticker.isin}")
            return None
        return yahoo_symbol

    def search_by_isin(self, tickers):
        isins = [t.isin for t in tickers]
        logger.info("Try to fetch symbol for: {}".format(isins))
        url = 'https://api.openfigi.com/v3/mapping'
        headers = {'Content-Type': 'text/json'}
        batch_size = 10

        results = []
        # payload = [{"idType": "ID_ISIN", "idValue": "US53225G1022", "micCode": "XNAS"}]
        for i in range(0, len(isins), batch_size):
            batch = isins[i:i + batch_size]
            payload = [{"idType": "ID_ISIN", "idValue": isin} for isin in batch]

            try:
                rsp = requests.post(url, headers=headers, data=json.dumps(payload))
                if rsp.ok:
                    results.extend(rsp.json())
                else:
                    logger.error(f"Failed to send batch starting at {i}. Status code: {rsp.status_code}")
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")

        logger.info(f"Found {len(results)} symbols")
        for ticker, k in zip(tickers, results):
            # print(f"Matching {ticker} - {k.get('data', [0])[0]}")
            if k.get('data'):
                ticker.ticker = k['data'][0]['ticker']
                for s in k['data']:
                    if ticker.currency in s['ticker']:
                        ticker.ticker = s['ticker'].replace(ticker.currency, "")
                        break
            else:
                ticker.ticker = self.get_ticker(ticker)

            #if not ticker.ticker:
#                ticker.ticker = self.get_ticker_ib(ticker.isin)
        return tickers

    def get_ticker_ib(self, isin):
        from xml.etree import ElementTree
        params = f"action=Ajax%20Search&start=0&description={isin}&ajaxQuery=Y&xtm=Wed%20Feb%2026%202025%2021:57:32%20GMT+0100%20(Central%20European%20Standard%20Time)"
        q = requests.get('https://pennies.interactivebrokers.com/cstools/contract_info/v3.10/index.php', params=params)

        root = ElementTree.fromstring(q.content)

        # Extract information from the 'obj' element
        obj_element = root.find('obj')
        if obj_element is not None:
            # Get all attributes as a dictionary
            obj_attributes = obj_element.attrib

            # Access specific attributes
            entity_id = obj_attributes.get('id')
            company_name = obj_attributes.get('d')
            market_symbol = obj_attributes.get('ms')
            market_exchange = obj_attributes.get('me')
            return market_symbol

        return None
