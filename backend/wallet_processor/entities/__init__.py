import logging
from abc import ABC


class EntityType:
    BANK = 0
    BROKER = 1
    CROWD = 2
    EXCHANGE = 3


class AbstractEntity(ABC):

    source_type = None

    def __init__(self):
        self._state = None
        self._logger = None  # type: logging.Logger
        self._init_logger()

    def trade(self, queue, order):
        raise NotImplementedError

    def clean(self):
        pass

    def get_orders(self, user_id):
        pass

    def create_closed_orders(self):
        pass

    def calc_wallet(self):
        pass

    def calc_balance_with_orders(self):
        pass

    def _init_logger(self):
        tmp_logger_name = type(self).__name__
        self._logger = logging.getLogger(tmp_logger_name)
