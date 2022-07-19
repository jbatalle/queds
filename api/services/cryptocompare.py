import requests
import json
from datetime import datetime
import requests.utils
import logging
import csv
from services import redis_svc


logger = logging.getLogger(__name__)


class CryptoCompareClient:

    def __init__(self):
        self.client = requests.Session()
        self.cached = None
        self.prices = {}
        if redis_svc.client:
            self.cached = redis_svc
            self.prices = self.cached.get("prices")

    def get_price(self, source, target):
        # if source in self.prices:
        url = "https://min-api.cryptocompare.com/data/price?fsym={}&tsyms={}"
        # url = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={}&tsym={}&limit=1&toTs={}"
        r = requests.get(url.format(source, target))
        data = r.json()
        if r.status_code != 200:
            logger.error(f"Error retrieving data: {r.text}")
        try:
            # return data.get('Data').get('Data')[1].get('close')
            return data
        except:
            return 0

    def get_historic_price(self, source, target, timestamp):
        if source in self.prices:
            if target in self.prices[source]:
                if str(timestamp) in self.prices[source][target]:
                    return self.prices[source][target][str(timestamp)]

        if source == 'XNO' or source == 'NANO':
            nano_prices = self.get_nano_prices()
            date = datetime.fromtimestamp(timestamp)
            new_timestamp = int(datetime(date.year, date.month, date.day).strftime("%s"))
            price = float(nano_prices[new_timestamp])

            if target not in self.prices[source]:
                self.prices[source][target] = {}
            self.prices[source][target][timestamp] = price

            with open(backup_prices, "w") as f:
                json.dump(prices, f)

            return price

        if source == 'IOTA' and target == 'EUR':
            nano_prices = self.get_iota_prices()
            date = datetime.datetime.fromtimestamp(timestamp)
            new_timestamp = int(datetime.datetime(date.year, date.month, date.day).strftime("%s"))
            price = float(nano_prices[new_timestamp])

            if target not in self.prices[source]:
                self.prices[source][target] = {}
            self.prices[source][target][timestamp] = price

            with open(backup_prices, "w") as f:
                json.dump(prices, f)

            return price

        url = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={}&tsym={}&limit=1&toTs={}"
        r = requests.get(url.format(source, target, timestamp))
        data = r.json()
        if r.status_code != 200:
            logger.error(f"Error retrieving data: {r.text}")
        try:
            data.get('Data').get('Data')[1].get('close')
        except:
            logger.warning("Unable to recover price of {}/{}: {}".format(source, target, data))
            # get to USD
            if target != "USD":
                usd_price = self.get_price(source, "USD", timestamp)
                usd_eur_price = self.get_price("USD", "EUR", timestamp)
                return usd_price * usd_eur_price
            return 1
        if data.get('Data').get('Data')[1].get('close') == 0:
            logger.warning("HEY!! price is 0!")
            return data.get('Data').get('Data')[1].get('close')
        self.prices[source][target][timestamp] = data.get('Data').get('Data')[1].get('close')
        self.cached.set("prices", self.prices)

        return data.get('Data').get('Data')[1].get('close')

    def get_old_data(self):
        url = "https://www.coingecko.com/es/monedas/nano/historical_data/eur?start_date=2017-01-02&end_date=2022-02-17"
        pass

    @staticmethod
    def get_nano_prices():
        with open("utils/xno-eur-max.csv", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            prices = {}
            for idx, row in enumerate(reader):
                if idx == 0:
                    continue
                # 2017-07-15 00:00:00 UTC
                time = int(datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S %Z").strftime("%s"))
                prices[time] = row[1]

        return prices

    @staticmethod
    def get_iota_prices(self):
        with open("utils/miota-eur-max.csv", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter=',')
            prices = {}
            for idx, row in enumerate(reader):
                if idx == 0:
                    continue
                # 2017-07-15 00:00:00 UTC
                time = int(datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S %Z").strftime("%s"))
                prices[time] = row[1]

        return prices
