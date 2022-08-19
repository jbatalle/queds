import requests
import json
from datetime import datetime
from urllib.parse import urlparse, parse_qs
import requests.utils
import binascii
import pickle
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
        try:
            with open("finance_reader/utils/cookies.pickle") as f:
                self.client.cookies = pickle.loads(binascii.a2b_base64(f.read()))
        except:
            self.generate_cookies()

    def get_ticker_info(self, symbol):
        endpoint = "https://query1.finance.yahoo.com/v7/finance/quote?lang=en-US&region=US&corsDomain=finance.yahoo.com"
        flds = ("symbol", "shortName", "currency", "fullExchangeName", "exchange")

        url = f"{endpoint}&fields={','.join(flds)}&symbols={symbol}"
        r = self.client.get(url)
        api_json = json.loads(r.text)

        return api_json['quoteResponse']['result'][0]['shortName'], api_json['quoteResponse']['result'][0]['currency']

    def generate_cookies(self):
        logger.info("Generating cookies!")
        url = "https://finance.yahoo.com"
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

        with open("finance_reader/utils/cookies.pickle", 'w') as f:
            f.write(parsed_cookies)

    def get_yahoo_symbol(self, symbol):
        url = "http://d.yimg.com/autoc.finance.yahoo.com/autoc?query={}&region=1&lang=en".format(symbol)
        url = "https://finance.yahoo.com/_finance_doubledown/api/resource/searchassist;searchTerm={}?device=console&returnMeta=true".format(symbol)

        r = self.client.get(url)
        if r.status_code != 200:
            logger.error(f"Status code: {r.status_code}. Error: {r.text}")
            return None

        try:
            result = r.json()
        except:
            logger.error("Unable to read response as json")
            return None

        if len(result['data']['items']) == 1:
            return result['data']['items'][0]['symbol']

        # search by name
        for x in result['data']['items']:
            # if x['name']
            return x['symbol']
            # if x['symbol'] == symbol:

        return None
