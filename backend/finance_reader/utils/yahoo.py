import requests
import csv
import requests.utils
import logging


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
        with open("finance_reader/utils/ISO10383_MIC_NewFormat.csv") as f:
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
        r = self.client.get(f"https://query2.finance.yahoo.com/v1/finance/search?q={ticker.isin}")
        d = r.json()['quotes']
        items = [c for c in d if c['typeDisp'] == 'Equity']
        yahoo_symbol = None
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
                                                                                                     {}).get(
                    'acronym')):
                logger.warning(f"Check ticker exchange {ticker.ticker} - {ticker.exchange}")
                if ticker.ticker in item['symbol']:
                    yahoo_symbol = item['symbol']
                    break

        if not yahoo_symbol:
            logger.error(f"Unable to detect the Yahoo symbol for {ticker.ticker}")
            return None
        return yahoo_symbol
