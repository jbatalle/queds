import os
import json
import requests
import datetime
import csv
import time
import logging
from collections import defaultdict

logger = logging.getLogger("utils.crypto_prices")

backup_prices = "backend/wallet_processor/utils/prices.json"
prices = defaultdict(lambda: defaultdict(dict))
if not os.path.exists(backup_prices):
    backup_prices = "wallet_processor/utils/prices.json"

if os.path.exists(backup_prices):
    print("Loading wallet prices...")
    with open(backup_prices) as f:
        prices = defaultdict(lambda: defaultdict(dict), json.load(f))


def get_nano_prices():
    with open("wallet_processor/utils/xno-eur-max.csv", newline='') as csvfile:
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
    iota_file = "backend/wallet_processor/utils/miota-eur-max.csv"
    if not os.path.exists(iota_file):
        iota_file = "wallet_processor/utils/prices.json"
    with open(iota_file, newline='') as csvfile:
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
        logger.debug("Downloading {}".format(source))

    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={source}&tsym={target}&limit=1&toTs={timestamp}"
    # timestamp = int(timestamp.strftime("%s"))
    # r = requests.get(url.format(source, target, timestamp))
    r = requests.get(url)
    data = r.json()
    if r.status_code != 200:
        logger.error(f"Error: {data}")
    try:
        data.get('Data').get('Data')[1].get('close')
    except:
        logger.error("Unable to recover price of {}/{}: {}".format(source, target, data))
        check_limit(data)
        # get to USD
        if target != "USD":
            usd_price = get_price(source, "USD", timestamp)
            usd_eur_price = get_price("USD", "EUR", timestamp)
            return usd_price * usd_eur_price
        return 1
    if data.get('Data').get('Data')[1].get('close') == 0:
        logger.error("HEY!! price is 0!")
        return data.get('Data').get('Data')[1].get('close')
    try:
        prices[source][target][timestamp] = data.get('Data').get('Data')[1].get('close')
    except:
        logger.error(f"Error: {data.get('Data')}")

    with open(backup_prices, "w") as f:
        json.dump(prices, f)
    return data.get('Data').get('Data')[1].get('close')


def check_limit(data):
    if 'You are over' not in data.get('Message'):
        logger.error(data.get('Message'))
    time.sleep(2)
    # TODO: check limits and retry after limits


def search_in_temporal(source, target, timestamp):

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

    if (source == 'IOTA' and target == 'EUR') or (target == 'IOTA'):
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
        logger.debug("Downloading {}".format(source))

    return False


def get_prices(sources, target, timestamp):
    try:
        timestamp = int(timestamp.strftime("%s"))
    except:
        timestamp = timestamp

    source_prices = []
    for source in sources:
        source_prices.append(search_in_temporal(source, target, timestamp))

    if False not in source_prices:
        return source_prices[0], source_prices[1]

    logger.error(f"Get prices from {sources} to {target} at {timestamp}")
    sources_str = ','.join(sources)
    r = requests.get(f"https://min-api.cryptocompare.com/data/pricehistorical?fsym={target}&tsyms={sources_str}&ts={timestamp}")
    data = r.json()

    if r.status_code != 200:
        if 'There is no data for the ' in data.get('Message'):
            # TODO
            return 1, 1

        logger.error(f"Error: {data}")
        check_limit(data)
        return 1, 1

    try:
        for k, v in data[target].items():
            if target not in prices[k]:
                prices[k][target] = {}
            prices[k][target][str(timestamp)] = v
    except:
        logger.error(f"Error: {data}")
        check_limit(data)
        return 1,1
    try:
        with open(backup_prices, "w") as f:
            json.dump(prices, f)
    except:
        logger.error("Error saving prices")
        return 1, 1

    return data[target][sources[0]], data[target][sources[1]]
