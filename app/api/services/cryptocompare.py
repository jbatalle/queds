import requests
import requests.utils
import logging
from datetime import datetime, timedelta
from services import redis_svc
from concurrent.futures import ThreadPoolExecutor, as_completed


logger = logging.getLogger(__name__)


class CryptoCompareClient:

    def __init__(self):
        self.client = requests.Session()
        self.redis = redis_svc

    def _fetch_and_cache(self, source, target, redis_key, endpoint, cache_expiry=None):
        cached_symbols = self.redis.get(redis_key) or {}
        normalized_target = [s.replace("IOTA", "MIOTA").replace("BTTC", "BTT") for s in target]
        missing_symbols = [s for s in normalized_target if s not in cached_symbols]

        if not missing_symbols:
            return cached_symbols

        logger.debug(f"Missing symbols for {redis_key}: {missing_symbols}")
        timestamp = int((datetime.today() - timedelta(days=1)).timestamp())
        failed_symbols = set()
        update = False

        def fetch_chunk(chunk):
            try:
                symbols_str = ",".join(chunk)
                logger.debug(f"Querying {endpoint} for: {symbols_str} (len: {len(symbols_str)})")
                response = requests.get(f"https://min-api.cryptocompare.com{endpoint}",
                                        params={"fsym": source, "tsyms": symbols_str, "ts": timestamp}
                )
                data = response.json()
                if data.get('Response') == 'Error':
                    logger.warning(f"Error response for chunk {chunk}: {data.get('Message')}")
                    return {}, chunk
                # result = data.get(source, data)  # handles /price vs /pricehistorical
                result = data
                # logger.debug(f"Retrieved data: {result} - {response.url} - {symbols_str}")
                return result, []
            except Exception as e:
                logger.error(f"Request failed for chunk {chunk}: {e}")
                return {}, chunk

        chunks = [missing_symbols[i:i + 4] for i in range(0, len(missing_symbols), 4)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                result, failed = future.result()
                if result:
                    cached_symbols.update(result)
                    update = True
                failed_symbols.update(failed)

        if update:
            if cache_expiry:
                self.redis.store(redis_key, cached_symbols, cache_expiry)
            else:
                self.redis.store(redis_key, cached_symbols)

        for symbol in failed_symbols:
            cached_symbols.pop(symbol, None)

        return cached_symbols

    def get_prices(self, source, target):
        return self._fetch_and_cache(
            source=source,
            target=target,
            redis_key='crypto_prices',
            endpoint='/data/price',
            cache_expiry=600
        )

    def get_changes(self, source, target):
        return self._fetch_and_cache(
            source=source,
            target=target,
            redis_key='crypto_changes',
            endpoint='/data/pricehistorical'
        )


class CryptoCompareClientOld:

    def __init__(self):
        self.client = requests.Session()
        self.redis = redis_svc
        self.prices = {}

    logger = logging.getLogger(__name__)

    def get_prices(self, source, target):
        cached_symbols = self.redis.get('crypto_prices') or {}
        missing_prices = [symbol for symbol in target if symbol not in cached_symbols]

        if not missing_prices:
            return cached_symbols

        logger.debug(f"Missing prices are {missing_prices}...")
        missing_prices = [m.replace("IOTA","MIOTA").replace("BTTC","BTT") for m in missing_prices]
        update = False
        timestamp = int((datetime.today() - timedelta(days=1)).timestamp())
        failed_symbols = set()

        def fetch_price_chunk(chunk):
            try:
                logger.debug(f"Querying for: {','.join(chunk)}. Len: {len(','.join(chunk))}")
                r = requests.get(
                    f"https://min-api.cryptocompare.com/data/price",
                    params={
                        "fsym": source,
                        "tsyms": ",".join(chunk),
                        "ts": timestamp
                    }
                )
                data = r.json()
                if data.get('Response') == 'Error':
                    logger.warning(f"Error response for chunk {chunk}: {data.get('Message')}")
                    failed = chunk  # consider whole chunk failed
                    return {}, failed
                logger.debug(f"Retrieved prices: {data}")
                return data, []
            except Exception as e:
                logger.error(f"Request failed for chunk {chunk}: {e}")
                return {}, chunk

        chunks = [missing_prices[i:i + 4] for i in range(0, len(missing_prices), 4)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_price_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                result, failed = future.result()
                if result:
                    cached_symbols.update(result)
                    update = True
                failed_symbols.update(failed)

        if update:
            self.redis.store('crypto_prices', cached_symbols, 600)

        # Optionally store known failed symbols to avoid retrying them in the future
        # self.redis.store('failed_crypto_symbols', list(failed_symbols))

        # Filter them out from return if you don't want them in the result
        for failed in failed_symbols:
            cached_symbols.pop(failed, None)

        return cached_symbols

    def get_changes(self, source, target):
        cached_symbols = self.redis.get('crypto_changes') or {}
        missing_prices = [symbol.replace("IOTA","MIOTA").replace("BTTC","BTT") for symbol in target if symbol not in cached_symbols]

        if not missing_prices:
            return cached_symbols

        update = False
        timestamp = int((datetime.today() - timedelta(days=1)).timestamp())
        failed_symbols = set()

        def fetch_change_chunk(chunk):
            try:
                symbols_str = ",".join(chunk)
                logger.debug(f"Querying changes for: {symbols_str}. Len: {len(symbols_str)}")
                r = requests.get(
                    "https://min-api.cryptocompare.com/data/pricehistorical",
                    params={
                        "fsym": source,
                        "tsyms": symbols_str,
                        "ts": timestamp
                    }
                )
                data = r.json()
                if data.get('Response') == 'Error':
                    logger.warning(f"Error response for chunk {chunk}: {data.get('Message')}")
                    return {}, chunk
                return data.get(source, {}), []
            except Exception as e:
                logger.error(f"Request failed for chunk {chunk}: {e}")
                return {}, chunk

        chunks = [missing_prices[i:i + 4] for i in range(0, len(missing_prices), 4)]

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(fetch_change_chunk, chunk) for chunk in chunks]
            for future in as_completed(futures):
                result, failed = future.result()
                if result:
                    cached_symbols.update(result)
                    update = True
                failed_symbols.update(failed)

        if update:
            self.redis.store('crypto_changes', cached_symbols)

        # Optionally exclude failed symbols from the return
        for symbol in failed_symbols:
            cached_symbols.pop(symbol, None)

        return cached_symbols
