import logging
from config import settings
from kombu import Connection, Exchange
from kombu.pools import producers


logger = logging.getLogger(__name__)


def enqueue_job(queue_name, data):
    logger.info(f"Queue process {queue_name}")
    connection = Connection(f'redis://{settings.REDIS.get("host")}')
    payload = {'args': data, 'kwargs': {}}
    queue = queue_name

    task_exchange = Exchange('tasks', type='direct')
    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload, serializer='pickle', compression='bzip2', exchange=task_exchange,
                         declare=[task_exchange], routing_key=queue)


def queue_read(data, queue_name):
    if not queue_name:
        return None
    enqueue_job(queue_name, data)
    return True


def queue_process(data):
    queue = "wallet"
    enqueue_job(queue, data)

