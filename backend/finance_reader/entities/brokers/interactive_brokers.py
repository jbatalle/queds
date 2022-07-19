import random
import execjs
import time
from datetime import datetime, timedelta
from requests.cookies import create_cookie
from bs4 import BeautifulSoup
from finance_reader.entities import TimeoutRequestsSession
from finance_reader.entities.brokers import AbstractBroker
from finance_reader.entities.brokers.dtos import BrokerAccount, Transaction, Ticker


class InteractiveBrokers(AbstractBroker):

    def __init__(self):
        super(InteractiveBrokers, self).__init__()
        self._client = TimeoutRequestsSession()
        self._client.headers = {
            "cache-control": "no-cache",
            "origin": "https://www.interactivebrokers.co.uk",
            "pragma": "no-cache",
            "referer": "https://www.interactivebrokers.co.uk/sso/Login",
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-ch-ua": '"Chromium";v="91", " Not;A Brand";v="99"',
            "sec-ch-ua-mobile": "?0",
            "upgrade-insecure-requests": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36"
        }
        self.account_id = None
        self.session_id = None
        self.acc_id = None
        self.conids = []

    @staticmethod
    def randomize_a(engine):
        p = engine.call("xyz_initialize")
        A = p.get('A')
        a = p.get('a')
        return A, a

    @staticmethod
    def load_xml(content):
        return BeautifulSoup(content, "xml")

    def login(self, username, password):
        self._logger.info("Init IB login")

        self._client.get("https://www.interactivebrokers.co.uk/en/home.php")
        self._client.get("https://www.interactivebrokers.co.uk/sso/Login?RL=1&locale=en_US")

        engine = execjs.compile(open("finance_reader/entities/brokers/ib_functions.js").read())
        A, a = self.randomize_a(engine)
        data = {
            "ACTION": "INIT",
            "APP_NAME": "",
            "MODE": "NORMAL",
            "FORCE_LOGIN": "",
            "USER": username,
            "ACCT": "",
            "A": A,
            "LOGIN_TYPE": 1
        }
        url = f"https://www.interactivebrokers.co.uk/sso/Authenticator?{random.randint(1, 10000)}"
        r1 = self._client.post(url, data=data)
        root = self.load_xml(r1.text)

        n_string = engine.eval("N.toString()")
        n_returned = engine.eval(f"parseBigInt('{root.find('N').text}', 16).toString()")
        if n_string != n_returned:
            self._logger.error("Different N")

        g = engine.eval("g.toString()")
        g_returned = root.find('g').text
        if g != g_returned:
            self._logger.error("Different g")

        salt = root.find('s').text
        B = root.find('B').text
        rsapub = root.find('rsapub').text
        js_response = engine.call("second_step", username, password, salt, B, rsapub, a, A)
        M1 = js_response.get('M1')
        EKX = js_response.get('EKX')
        pre_calc_m2 = js_response.get('M2')
        sk = js_response.get('sk')

        data = {
            "ACTION": "COMPLETEAUTH",
            "APP_NAME": "",
            "USER": username,
            "ACCT": "",
            "M1": M1,
            "VERSION": 1,
            "LOGIN_TYPE": 1,
            "EKX": EKX
        }
        url = f"https://www.interactivebrokers.co.uk/sso/Authenticator?{random.randint(1, 10000)}"
        r2 = self._client.post(url, data=data)
        root = self.load_xml(r2.text)
        if root.find('M2').text == 'null':
            self._logger.error("Invalid credentials")
            self._logger.error(r2.text)
            return False

        M2 = root.find('M2').text
        if M2 != pre_calc_m2:
            self._logger.error("Different M2")

        data = {
            "ACTION": "COMPLETEAUTH_1",
            "APP_NAME": "",
            "USER": username,
            "ACCT": "",
            "M1": M1,
            "VERSION": 1,
            "SF": "5.2a"
        }
        self._client.post(url, data=data)

        self._client.cookies.set_cookie(create_cookie("XYZAB_AM.LOGIN", sk))
        self._client.cookies.set_cookie(create_cookie("XYZAB", sk))

        # push notification
        data = {
            "ACTION": "COMPLETETWOFACT",
            "APP_NAME": "",
            "USER": username,
            "VERSION": 1,
            "SF": "5.2a",
            "PUSH": "true",
            "counter": 1
        }
        logged = False
        for i in range(1, 20):
            url = f"https://www.interactivebrokers.co.uk/sso/Authenticator?{random.randint(1, 10000)}"
            r4 = self._client.post(url, data=data)
            root = self.load_xml(r4.text)
            if root.find('auth_res').text != 'false':
                logged = True
                break

            data['counter'] = i
            time.sleep(3)

        if not logged:
            return False

        data = {
            "user_name": username,
            "password": "",
            "chlginput": "",
            "loginType": 1,
            "M1": M1,
            "M2": M2
        }
        self._client.headers.update({
            "sec-fetch-user": "?1",
            "sec-fetch-dest": "document",
            "sec-fetch-mode": "navigate",
            "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
        })
        url = "https://www.interactivebrokers.co.uk/sso/Dispatcher;jsessionid=" + self._client.cookies.get("JSESSIONID")
        self._client.post(url, data=data)

        url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/sso/validate"
        r = self._client.get(url)
        validate = r.json()
        user_id = validate.get('USER_ID')

        url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/ssodh/init"
        self._client.get(url)

        url = "https://www.interactivebrokers.co.uk/ibcust.proxy/v1/ibcust/one/user"
        self._client.get(url)

        url = "https://www.interactivebrokers.co.uk/AccountManagement/OneBarAuthentication?json=1"
        self._client.get(url)

        url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio/accounts"
        r = self._client.get(url)
        accounts_json = r.json()
        for acc in accounts_json:
            currency = acc.get('currency')
            # self._logger.debug(acc.get('id'))
            # self._logger.debug(acc.get('accountStatus'))
            self.acc_id = acc.get('id')

        url = f"https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio2/{self.acc_id}/positions?sort=marketValue&direction=d"
        r = self._client.get(url)
        positions = r.json()
        self.conids = [c['conid'] for c in positions]

        url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio/allocation"
        # TODO: get user_id? or account_id?
        url = f"https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio/{self.acc_id}/summary"
        r = self._client.get(url)
        summary = r.json()

        # TODO: get user_id? or account_id?
        url = f"https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio/{self.acc_id}/ledger"
        r = self._client.get(url)
        ledger = r.json()

        entity_account = BrokerAccount()
        entity_account.balance = round(summary.get('totalcashvalue').get('amount'), 2) or 0
        entity_account.currency = summary.get('totalcashvalue').get('currency')
        entity_account.virtual_balance = round(sum(p['marketValue'] for p in positions), 2)

        return entity_account

    def read_transactions(self, start_date):
        transactions = []
        conids_isin = {}
        tickers = {}
        now = datetime.now()
        start_date = datetime.strptime(start_date, "%d/%m/%Y")
        for con_id in self.conids:
            data = {
                "acctIds": [
                    self.acc_id
                ],
                "additional": None,
                "conids": [con_id],
                "currency": "EUR",
                "days": (now - start_date).days
            }
            url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/pa/transactions"
            r = self._client.post(url, json=data)
            transactions.extend(r.json()['transactions'])

            if con_id not in conids_isin:
                q = self.get_position()
                if len(q[self.acc_id]) > 1:
                    self._logger.warning("More than two positions!")
                exchange = q[self.acc_id][0]['listingExchange']
                d = self.search_isin(con_id, exchange)
                isin = d.get('result')[0]['fullIsin']
                conids_isin[con_id] = isin

                ticker = Ticker()
                ticker.isin = isin
                ticker.ticker = d.get('result')[0]['symbol']
                ticker.name = d.get('result')[0]['description']
                ticker.active = Ticker.Status.ACTIVE
                tickers[isin] = ticker

        to_insert = []
        for trans in transactions:
            t = Transaction()
            t.name = trans.get("desc")
            t.ticker = tickers[conids_isin[str(trans.get('conid'))]]
            t.currency = trans.get("cur")
            t.shares = trans.get("qty")
            t.type = Transaction.Type.BUY if trans.get('type') == 'Buy' else Transaction.Type.SELL
            t.currency_rate = trans.get("fxRate")
            t.price = trans.get("pr")
            # 'Tue Jul 27 00:00:00 EDT 2021'
            if 'EDT' in trans.get('date'):
                t.value_date = datetime.strptime(trans.get("date"), "%a %b %d %H:%M:%S EDT %Y") - timedelta(hours=4)
            elif 'EST' in trans.get('date'):
                t.value_date = datetime.strptime(trans.get("date"), "%a %b %d %H:%M:%S EST %Y") - timedelta(hours=4)
            else:
                self._logger.warning(f"Different timezone to handle: {trans['date']}")
                t.value_date = datetime.strptime(trans.get("date"), "%a %b %d %H:%M:%S %Z %Y")
            t.fee = 0
            t.external_id = f"{t.ticker.ticker}.{t.value_date}.{t.shares}.{t.price}"
            # t.exchange_fee = exchange_fee
            #         start_date = datetime.strptime(start_date, "%d/%m/%Y").strftime("%Y-%m-%d")

            to_insert.append(t)

        return to_insert

    def search_isin(self, conid, exchange):
        data = {
            "conid": conid,
            "exchange": exchange  # "NASDAQ"
        }
        url = "https://www.interactivebrokers.co.uk/cstoolsws/ibgroup.custops.cust.slb/slb/search/"
        r = self._client.post(url, json=data)
        return r.json()

    def get_position(self):
        url = "https://www.interactivebrokers.co.uk/portal.proxy/v1/portal/portfolio/positions/366131373"
        r = self._client.get(url)
        return r.json()
