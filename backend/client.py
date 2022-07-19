import os
import sys
import logging
from kombu import Connection, Exchange
from kombu.pools import producers


logger = logging.getLogger(__name__)


def queue_read(data, queue='broker'):
    connection = Connection(f'redis://{settings.REDIS.get("host")}')
    payload = {'args': data, 'kwargs': {}}

    task_exchange = Exchange('tasks', type='direct')
    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload, serializer='pickle', compression='bzip2', exchange=task_exchange,
                         declare=[task_exchange], routing_key=queue)


def queue_process(data):
    connection = Connection(f'redis://{settings.REDIS.get("host")}')
    payload = {'args': data, 'kwargs': {}}
    queue = "wallet"

    task_exchange = Exchange('tasks', type='direct')
    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload, serializer='pickle', compression='bzip2', exchange=task_exchange,
                         declare=[task_exchange], routing_key=queue)


if __name__ == '__main__':
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))

    from config import Settings
    settings_module = os.environ.get("BACKEND_SETTINGS", None) or None
    settings = Settings(settings_module)

    data = {
        "broker_name": "degiro",
        "username": "",
        "password": ""
    }
    data = {
        "broker_name": "clicktrade",
        "username": "",
        "password": ""
    }
    data = {
        "account_id": 3,
        "entity_name": "ib",
        "username": "",
        "password": ""
    }
    queue_read(data)
    data = {
        "user_id": 1,
        "mode": "stock"
    }
    # queue_process(data)

    data = {
        "exchange_name": "bittrex",
        "account_id": 2,
        "user_id": "",
        "api_key": "",
        "api_secret": ""
    }
    queue_read(data, "crypto")
