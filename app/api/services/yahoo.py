import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests.utils
import binascii
import pickle
import logging
from services import redis_svc
from curl_cffi import requests


logger = logging.getLogger(__name__)


class YahooClient:

    def __init__(self):
        self.client = requests.Session(impersonate="chrome")
        self.client.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.8,es;q=0.6,ca;q=0.4',
                'Accept-Encoding': 'gzip, deflate, br, zstd'
            }
        )
        self.redis = redis_svc
        return
        if redis_svc.client:
            if not redis_svc.get('yahoo_cookies'):
                self.generate_cookies()

            self.client.cookies = pickle.loads(binascii.a2b_base64(redis_svc.get('yahoo_cookies')))
        else:
            try:
                with open("services/cookies.pickle") as f:
                    self.client.cookies = pickle.loads(binascii.a2b_base64(f.read()))
            except:
                self.generate_cookies()

    def get_current_tickers(self, symbols):
        cached_symbols = self.redis.get('symbols')
        # if all symbols are cached, return them
        if cached_symbols:
            logger.debug(f"Cached: {[s['symbol'] for s in cached_symbols['symbols']]}")

        if cached_symbols and all(symbol in [s['symbol'] for s in cached_symbols['symbols']] for symbol in symbols.split(",")):
            return cached_symbols['symbols']
        r = self.client.get("https://query2.finance.yahoo.com/v1/test/getcrumb")
        crumb = r.text

        if r.status_code != 200:
            logger.debug(f"Regenerate cookies due state: {r.status_code}")
            self.generate_cookies()
            r = self.client.get("https://query2.finance.yahoo.com/v1/test/getcrumb")
            crumb = r.text

        # r = self.client.get(f"https://query1.finance.yahoo.com/v7/finance/quote?lang=en-US&region=US&corsDomain=finance.yahoo.com")
        # r = self.client.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{symbols}")
        r = self.client.get(f"https://query1.finance.yahoo.com/v7/finance/quote?crumb={crumb}&lang=en-US&region=US&corsDomain=es.finance.yahoo.com&symbols={symbols}")

        parsed_json = []
        for d in r.json().get('quoteResponse').get('result'):
            market_time = None
            if d.get('regularMarketTime'):
                market_time = datetime.fromtimestamp(d.get('regularMarketTime')).strftime('%Y/%m/%d %H:%M:%S')
            else:
                # TODO: handle this case
                pass
            q = {
                "symbol": d.get("symbol"),
                "price_change": d.get('regularMarketChangePercent'),
                "market_time": market_time,
                "price": d.get('regularMarketPrice'),
                "high": d.get('regularMarketDayHigh'),
                "low": d.get('regularMarketDayLow'),
                "vol": d.get('regularMarketVolume'),
                "pre": d.get('preMarketPrice', None),  # postMarketChangePercent
                "pre_change": d.get('preMarketChangePercent', None),  # postMarketChangePercent
                "previous_close": d.get('regularMarketPreviousClose'),
                "market_open": d.get('regularMarketPreviousClose')
            }
            parsed_json.append(q)

        self.redis.store('symbols', {"symbols": parsed_json})
        return parsed_json

    def get_ticker_info(self, symbol):
        endpoint = "https://query1.finance.yahoo.com/v7/finance/quote?lang=en-US&region=US&corsDomain=finance.yahoo.com"
        flds = ("symbol", "shortName", "currency", "fullExchangeName", "exchange")

        url = f"{endpoint}&fields={','.join(flds)}&symbols={symbol}"
        r = self.client.get(url)
        api_json = json.loads(r.text)

        return api_json['quoteResponse']['result'][0]['shortName'], api_json['quoteResponse']['result'][0]['currency']

    def generate_cookies(self):
        logger.info("Generating cookies!")
        url = "https://finance.yahoo.com/"
        r = self.client.get(url)

        o = urlparse(r.url)
        params = parse_qs(o.query)
        session_id = params['sessionId'][0]
        url = f"https://consent.yahoo.com/v2/collectConsent?sessionId={session_id}"

        o = urlparse(r.history[1].url)
        params = parse_qs(o.query)
        csrf_token = params['gcrumb'][0]
        data = {
            "csrfToken": csrf_token,
            "sessionId": session_id,
            "originalDoneUrl": "https://finance.yahoo.com/?guccounter=1",
            "namespace": "yahoo",
            "agree": "agree"
        }

        self.client.post(url, data=data)

        logger.info("Saving cookies to pickle file")
        cookies = requests.utils.dict_from_cookiejar(self.client.cookies)
        parsed_cookies = binascii.b2a_base64(pickle.dumps(self.client.cookies)).decode()

        if redis_svc.client:
            self.client.cookies = redis_svc.store('yahoo_cookies', parsed_cookies, 60*60*24*30)
        else:
            with open("services/cookies.pickle", 'w') as f:
                f.write(parsed_cookies)

    def get_yahoo_symbol(self, symbol):
        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
        url = "https://finance.yahoo.com/_finance_doubledown/api/resource/searchassist;searchTerm={}?device=console&returnMeta=true".format(symbol)
        url = f"https://query1.finance.yahoo.com/v1/finance/search?q={symbol}&lang=es-ES&region=ES&quotesCount=1&newsCount=0"

        r = self.client.get(url)
        if r.status_code != 200:
            logger.error(f"Status code: {r.status_code}. Error: {url}")
            return None

        try:
            result = r.json()
        except:
            logger.error(f"Unable to read response as json. Url: {url}")
            return None

        if len(result['quotes']) == 0:
            return None

        return result['quotes'][0]['symbol']

        if len(result['data']['items']) == 1:
            return result['data']['items'][0]['symbol']

        # search by name
        for x in result['data']['items']:
            # if x['name']
            return x['symbol']
            # if x['symbol'] == symbol:

        return None

    def get_currency(self):
        if self.redis.get('currency'):
            return self.redis.get('currency')['USD/EUR']
        timestamp = int(datetime.now().timestamp()) - 1
        url = "https://query1.finance.yahoo.com/v8/finance/chart/USDEUR=X?symbol=USDEUR%3DX&period1={}&period2=9999999999&useYfid=true&interval=1d&includePrePost=true&events=div%7Csplit%7Cearn&lang=es-ES&region=ES&crumb=O4yJagJUQUh&corsDomain=es.finance.yahoo.com"
        response = self.client.get(url.format(timestamp))
        api_json = response.json()
        if api_json['chart']['error']:
            logger.error(api_json['chart']['error'])
            return
        indicators = api_json['chart']['result'][0]['indicators']

        to_insert = []
        rate = 1
        if 'timestamp' not in api_json['chart']['result'][0]:
            logger.error("No timestamp found. Returning last value")
            d = api_json['chart']['result'][0]['meta']
            a = {
                "timestamp": d['regularMarketTime'],
                "pair": "USD/EUR",
                "close": d['regularMarketPrice']
            }
            rate = round(a['close'], 2)
        for idx, timestamp in enumerate(api_json['chart']['result'][0]['timestamp']):
            a = {
                "timestamp": timestamp,
                "pair": "USD/EUR",
                "close": indicators['quote'][0]['close'][idx]
            }
            rate = round(a['close'], 2)

        self.redis.store('currency', {"USD/EUR": rate}, expiration=3600*6)
        return rate
