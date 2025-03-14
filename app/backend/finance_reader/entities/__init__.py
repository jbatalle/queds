import requests
import logging
from abc import ABC, abstractmethod

DEFAULT_REQUEST_TIMEOUT = 60


class TimeoutRequestsSession(requests.Session):
    def request(self, *args, **kwargs):
        if kwargs.get('timeout') is None:
            kwargs['timeout'] = DEFAULT_REQUEST_TIMEOUT
        return super(TimeoutRequestsSession, self).request(*args, **kwargs)


class EntityType:
    BANK = 0
    BROKER = 1
    CROWD = 2
    EXCHANGE = 3


class AbstractEntity(ABC):

    source_type = None

    def __init__(self):
        self._state = None
        self._client = TimeoutRequestsSession()
        self._logger = None  # type: logging.Logger
        self._init_logger()

    @abstractmethod
    def login(self, parameters: dict):
        raise NotImplementedError

    def logout(self):
        pass

    def read(self):
        pass

    def _init_logger(self):
        tmp_logger_name = type(self).__name__
        self._logger = logging.getLogger(tmp_logger_name)
