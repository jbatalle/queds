from finance_reader.entities import AbstractEntity
import time


class AbstractExchange(AbstractEntity):

    def __init__(self):
        super(AbstractExchange, self).__init__()

    @staticmethod
    def nonce():
        """
        Creates a Nonce value for signature generation
        :return:
        """
        return str(round(100000 * time.time()) * 2)


from finance_reader.entities.exchanges.bitstamp import Bitstamp
from finance_reader.entities.exchanges.kraken import Kraken
from finance_reader.entities.exchanges.bittrex import Bittrex
from finance_reader.entities.exchanges.binance import Binance
from finance_reader.entities.exchanges.kucoin import Kucoin


SUPPORTED_EXCHANGES = {
    "bitstamp": Bitstamp(),
    "kraken": Kraken(),
    "bittrex": Bittrex(),
    "binance": Binance(),
    "kucoin": Kucoin()
}
