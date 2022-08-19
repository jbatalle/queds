import os
import json
import requests
import datetime
import csv
from collections import defaultdict

backup_prices = "wallet_processor/utils/prices.json"
prices = defaultdict(lambda: defaultdict(dict))

if os.path.exists(backup_prices):
    with open(backup_prices) as f:
        prices = defaultdict(lambda: defaultdict(dict), json.load(f))


def get_nano_prices():
    with open("utils/xno-eur-max.csv", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        prices = {}
        for idx, row in enumerate(reader):
            if idx == 0:
                continue
            # 2017-07-15 00:00:00 UTC
            time = int(datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S %Z").strftime("%s"))
            prices[time] = row[1]

    return prices


def get_iota_prices():
    with open("utils/miota-eur-max.csv", newline='') as csvfile:
        reader = csv.reader(csvfile, delimiter=',')
        prices = {}
        for idx, row in enumerate(reader):
            if idx == 0:
                continue
            # 2017-07-15 00:00:00 UTC
            time = int(datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S %Z").strftime("%s"))
            prices[time] = row[1]

    return prices

# For old data:
# url = "https://www.coingecko.com/es/monedas/nano/historical_data/eur?start_date=2017-01-02&end_date=2022-02-17"


def get_price(source, target, timestamp):
    try:
        timestamp = int(timestamp.strftime("%s"))
    except:
        timestamp = timestamp

    if source in prices:
        if target in prices[source]:
            if str(timestamp) in prices[source][target]:
                return prices[source][target][str(timestamp)]

    if source == 'XNO' or source == 'NANO':
        nano_prices = get_nano_prices()
        date = datetime.datetime.fromtimestamp(timestamp)
        new_timestamp = int(datetime.datetime(date.year, date.month, date.day).strftime("%s"))
        price = float(nano_prices[new_timestamp])

        if target not in prices[source]:
            prices[source][target] = {}
        prices[source][target][timestamp] = price

        with open(backup_prices, "w") as f:
            json.dump(prices, f)

        return price

    if source == 'IOTA' and target == 'EUR':
        nano_prices = get_iota_prices()
        date = datetime.datetime.fromtimestamp(timestamp)
        new_timestamp = int(datetime.datetime(date.year, date.month, date.day).strftime("%s"))
        price = float(nano_prices[new_timestamp])

        if target not in prices[source]:
            prices[source][target] = {}
        prices[source][target][timestamp] = price

        with open(backup_prices, "w") as f:
            json.dump(prices, f)

        return price

        # coin_price = float(row[3]) / float(row[1])
        usd_price = get_price("IOTA", "USD", timestamp)
        eur_usd = get_price("USD", "EUR", timestamp)
        if usd_price == 0:
            usd_price = 0.01
        prices[source][target][timestamp] = usd_price * eur_usd
        return usd_price * eur_usd

    if source != 'IOTA':
        print("Downloading {}".format(source))

    url = "https://min-api.cryptocompare.com/data/v2/histoday?fsym={}&tsym={}&limit=1&toTs={}"
    # timestamp = int(timestamp.strftime("%s"))
    r = requests.get(url.format(source, target, timestamp))
    data = r.json()
    if r.status_code != 200:
        print("error")
    try:
        data.get('Data').get('Data')[1].get('close')
    except:
        print("Unable to recover price of {}/{}: {}".format(source, target, data))
        check_limit(data)
        # get to USD
        if target != "USD":
            usd_price = get_price(source, "USD", timestamp)
            usd_eur_price = get_price("USD", "EUR", timestamp)
            return usd_price * usd_eur_price
        return 1
    if data.get('Data').get('Data')[1].get('close') == 0:
        print("HEY!! price is 0!")
        return data.get('Data').get('Data')[1].get('close')
    prices[source][target][timestamp] = data.get('Data').get('Data')[1].get('close')

    with open(backup_prices, "w") as f:
        json.dump(prices, f)
    return data.get('Data').get('Data')[1].get('close')


def check_limit(data):
    if 'You are over' not in data.get('Message'):
        print(data)
    # TODO: check limits and retry after limits
