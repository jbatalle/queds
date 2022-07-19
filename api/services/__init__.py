import json
import redis
from config import settings


class RedisClient:
    def __init__(self, config=None):
        self._config = config or settings.REDIS
        self.pool = None
        self.client = None  # type: redis.StrictRedis
        self.default_expiration = 300
        self.connect()

    def connect(self):
        if self._config:
            self.client = redis.StrictRedis(**self._config)
            self.client.ping()

    def store(self, key, data, expiration=None):
        json_data = json.dumps(data)
        expiration = expiration or self.default_expiration
        self.client.set(key, json_data, expiration)

    def get(self, key):
        json_data = self.client.get(key)

        if json_data:
            return json.loads(json_data.decode())

        return None

    def exists(self, key):
        return self.client.exists(key)


redis_svc = RedisClient()
