import os
import json
import requests
import datetime
import csv
import time
import logging
from collections import defaultdict
from typing import Dict, Optional

logger = logging.getLogger("utils.crypto_prices")

# ----------------------------
# File & Cache Initialization
# ----------------------------
backup_paths = [
    "backend/wallet_processor/utils/prices.json",
    "wallet_processor/utils/prices.json",
    "app/backend/wallet_processor/utils/prices.json",
]
backup_prices = next((p for p in backup_paths if os.path.exists(p)), backup_paths[0])

prices: Dict[str, Dict[str, Dict[str, float]]] = defaultdict(lambda: defaultdict(dict))
if os.path.exists(backup_prices):
    logger.debug("Loading cached crypto prices...")
    with open(backup_prices) as f:
        prices.update(json.load(f))

# ----------------------------
# CSV Price Loaders
# ----------------------------

def load_csv_prices(file_path: str) -> Dict[int, float]:
    prices = {}
    if not os.path.exists(file_path):
        logger.warning(f"Missing file: {file_path}")
        return prices
    with open(file_path, newline='') as csvfile:
        reader = csv.reader(csvfile)
        next(reader, None)  # Skip header
        for row in reader:
            try:
                ts = int(datetime.datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S %Z").timestamp())
                prices[ts] = float(row[1])
            except Exception as e:
                logger.warning(f"Skipping invalid row {row}: {e}")
    return prices

def get_nano_prices() -> Dict[int, float]:
    return load_csv_prices("wallet_processor/utils/xno-eur-max.csv")

def get_iota_prices() -> Dict[int, float]:
    paths = [
        "backend/wallet_processor/utils/miota-eur-max.csv",
        "wallet_processor/utils/miota-eur-max.csv",
    ]
    for path in paths:
        if os.path.exists(path):
            return load_csv_prices(path)
    return {}

# ----------------------------
# Price Lookup Logic
# ----------------------------

def get_price(source: str, target: str, timestamp) -> Optional[float]:
    """Get historical price for a given crypto pair and timestamp."""
    try:
        timestamp = int(timestamp.strftime("%s"))
    except AttributeError:
        timestamp = int(timestamp)

    if source == 'BTTC':
        source = 'BTT'

    daily_ts = int(datetime.datetime.fromtimestamp(timestamp).replace(hour=0, minute=0, second=0).timestamp())
    cache_key = str(timestamp)

    if price := prices.get(source, {}).get(target, {}).get(cache_key):
        return price
    
    # Handle symbol aliases
    if source in ['XNO', 'NANO']:
        source = 'NANO'
        return store_and_return(source, target, timestamp, get_offline_price(get_nano_prices(), daily_ts))

    if source == 'IOTA' and target == 'EUR':
        return store_and_return(source, target, timestamp, get_offline_price(get_iota_prices(), daily_ts))

    # CryptoCompare fetch
    logger.debug(f"Fetching {source}/{target} at {timestamp}")
    url = f"https://min-api.cryptocompare.com/data/v2/histoday?fsym={source}&tsym={target}&limit=1&toTs={timestamp}"

    price = fetch_price_from_url(url)
    if price is not None:
        return store_and_return(source, target, timestamp, price)

    # Try HitBTC exchange
    market = get_markets(source, target)
    if not market:
        url += f"&e={market}"
        logger.warning(f"Retrying {source}/{target} using {market} exchange...")
        price = fetch_price_from_url(url)
        if price is not None:
            return store_and_return(source, target, timestamp, price)
    
    if target == 'BTC':
        raise

    logger.info(f"Fallback: {source}→BTC→{target}")
    try:
        btc_price = get_price(source, "BTC", timestamp)
        target_price = get_price("BTC", target, timestamp)
        if btc_price and target_price:
            return store_and_return(source, target, timestamp, btc_price * target_price)
    except Exception as e:
        logger.error(f"BTC fallback failed: {e}")
    return 0

# ----------------------------
# Helpers
# ----------------------------

def get_markets(source, target):
    url = f"https://min-api.cryptocompare.com/data/top/exchanges/full?fsym={source}&tsym={target}"
    r = requests.get(url)
    data = r.json()
    if 'Data' not in data:
        return None
    if 'Exchange' not in data['Data']:
        return None
    if len(data['Data']['Exchange']) > 0:
        return data['Data']['Exchange'][0]['MARKET']

def get_offline_price(price_dict: Dict[int, float], timestamp: int) -> float:
    """Get price from local CSV by timestamp."""
    return float(price_dict.get(timestamp, 0.0))

def fetch_price_from_url(url: str) -> Optional[float]:
    try:
        # logger.debug(f"Url: {url}")
        r = requests.get(url)
        if r.status_code != 200:
            logger.error(f"Error from API: {r.text}")
            return None
        data = r.json()
        if not is_valid_price_data(data):
            logger.warning(f"Invalid price data structure: {data}")
            check_limit(data)
            return None
        price = data['Data']['Data'][1]['close']
        if price == 0:
            logger.warning(f"Price is 0 for {url}")
        return data['Data']['Data'][1]['close']
    except Exception as e:
        logger.error(f"Exception fetching URL: {e}")
        return None
    


def is_valid_price_data(data) -> bool:
    try:
        return (
            'Data' in data and
            'Data' in data['Data'] and
            len(data['Data']['Data']) > 1 and 'close' in data['Data']['Data'][1]
        )
    except:
        return False

def check_limit(data):
    if 'You are over' in data.get('Message', ''):
        logger.warning("Rate limit exceeded. Waiting...")
        time.sleep(2)
    #else:
        #logger.error("Error: ", data.get('Message'))

def store_and_return(source: str, target: str, timestamp: int, price: float) -> float:
    """Store price in cache and return it."""
    str_ts = str(timestamp)
    prices.setdefault(source, {}).setdefault(target, {})[str_ts] = price
    try:
        with open(backup_prices, "w") as f:
            json.dump(prices, f)
    except Exception as e:
        logger.warning(f"Could not write to price cache: {e}")
    return price
