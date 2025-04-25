import abc
import time
import asyncio
from collections import OrderedDict

class Cache(metaclass=abc.ABCMeta):

    def __init__(self):
        self.client = None

    def get(self, key, default=None, with_age=False):
        NotImplementedError

    def set(self, key, value, expiration):
        NotImplementedError

    def items(self):
        NotImplementedError


class ExpiringDict(Cache, OrderedDict):
    def __init__(self, default_expiration=600):
        OrderedDict.__init__(self)
        Cache.__init__(self)
        self.lock = asyncio.Lock()
        self.default_expiration = default_expiration
        self._safe_keys = lambda: list(self.keys())
        self.max_len = 500

    async def connect(self):
        pass

    def get_size(self):
        return len(self)

    async def clear(self):
        """ Clear old keys """
        items = await self.items()
        for key, item in items:
            item_age = item[1] - time.time()
            if item[1] < time.time():
                del self[key]

    def __contains__(self, key):
        """ Return True if the dict has a key, else return False. """
        try:
            item = OrderedDict.__getitem__(self, key)
            if item[1] > time.time():
                return True
            else:
                del self[key]
        except KeyError:
            pass
        return False

    def ttl(self, key):
        """ Return TTL of the `key` (in seconds).
        Returns None for non-existent or expired keys.
        """
        key_value, key_ttl = self.get(key, with_age=True)
        if key_ttl:
            if key_ttl > 0:
                return key_ttl
        return None

    def get(self, key, default=None, with_age=False):
            """ Return the value for key if key is in the dictionary, else default. """
        #with self.lock:
            try:
                item = OrderedDict.__getitem__(self, key)
                item_age = item[1] - time.time()
                if item[1] > time.time():
                    if with_age:
                        return item[0], item_age
                    else:
                        return item[0]
                else:
                    del self[key]
                    raise KeyError(key)
            except KeyError:
                if with_age:
                    return default, None
                else:
                    return default

    def set(self, key, value, expiration=None):
        #with self.lock:
            if len(self) == self.max_len:
                if key in self:
                    del self[key]
                else:
                    try:
                        self.popitem(last=False)
                    except KeyError:
                        pass
            if expiration is None:
                expiration = time.time() + self.default_expiration
            else:
                expiration = time.time() + expiration
            OrderedDict.__setitem__(self, key, (value, expiration))

    def items(self):
        """ Return a copy of the dictionary's list of (key, value) pairs. """
        r = []
        for key in self._safe_keys():
            try:
                r.append((key, self[key]))
            except KeyError:
                pass
        return r
    
    def store(self, key, value, expiration=None):
        self.set(key, value, expiration)


from config import settings
if settings.REDIS:
    from services.redis import RedisClient
    redis_svc = RedisClient()
else:
    redis_svc = ExpiringDict()
