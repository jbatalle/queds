import os
import sys
import logging
import time
import threading
from kombu.mixins import ConsumerMixin
from kombu import Exchange, Queue, Connection
from kombu.pools import producers


logger = logging.getLogger("worker")
MAX_RETRIES = 3

class HandlerType:
    BROKER_READ = 'broker'
    CRYPTO_READ = 'crypto'
    WALLET_PROCESS = 'wallet'
    CSV_READ = 'csv'
    ALERT = 'alerts'


_handler_map = {}


def _build_handler_map():
    from finance_reader.handlers.broker_read import BrokerReader
    from finance_reader.handlers.exchange_read import ExchangeReader
    from wallet_processor.handlers.wallet_processor import WalletProcessor
    from finance_reader.handlers.csv_read import CSVReader
    # from alerts.alert_processor import AlertProcessor

    _handler_map.update({
        HandlerType.BROKER_READ: BrokerReader,
        HandlerType.CRYPTO_READ: ExchangeReader,
        HandlerType.WALLET_PROCESS: WalletProcessor,
        HandlerType.CSV_READ: CSVReader,
#        HandlerType.ALERT: AlertProcessor
    })


def get_request_handler(request_type):
    if not _handler_map:
        _build_handler_map()

    return _handler_map.get(request_type, None)


task_exchange = Exchange('tasks', type='direct')
task_queues = [Queue('broker', task_exchange, routing_key='broker'),
               Queue('crypto', task_exchange, routing_key='crypto'),
               Queue('wallet', task_exchange, routing_key='wallet'),
               Queue('csv', task_exchange, routing_key='csv'),
               Queue('alerts', task_exchange, routing_key='alerts')]


def enqueue_job(delay=0):
    connection = Connection(f'redis://{settings.REDIS.get("host")}')
    payload = {'args': {}, 'kwargs': {}}
    queue = "alerts"

    task_exchange = Exchange('tasks', type='direct')
    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload, serializer='pickle', compression='bzip2', exchange=task_exchange,
                         declare=[task_exchange], routing_key=queue, headers={"delay": 10})


class Worker(ConsumerMixin):

    def __init__(self, connection):
        self.connection = connection
        self.retry_counts = {}  # Track retries per message

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=task_queues,
                         accept=['pickle', 'json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        logger.info(f"Processing task: {message.properties}")
        routing_key = message.delivery_info['routing_key']
        args = body['args']
        kwargs = body['kwargs']
        logger.info(f"Got task with routing_key: {routing_key}!")
        msg_id = message.delivery_tag  # Unique per message

        # Use meta for retry tracking
        if 'meta' not in body:
            body['meta'] = {}
        retries = body['meta'].get('retries', 0)

        try:
            cls_handler = get_request_handler(routing_key)
            if not cls_handler:
                logger.error(f"Handler no exists for routing_key: {routing_key}")
                message.ack()
                return

            handler = cls_handler()
            handler.process(args)
            message.ack()

            # send wallet processor message in case of read
            if routing_key in [HandlerType.BROKER_READ, HandlerType.CRYPTO_READ, HandlerType.CSV_READ]:
                if 'data' in body['args']:
                    body['args']['data'] = None
                if routing_key == HandlerType.BROKER_READ or routing_key == HandlerType.CSV_READ:
                    body['args']["mode"] = "stock"
                else:
                    body['args']["mode"] = "crypto"

                task_exchange = Exchange('tasks', type='direct')
                with producers[self.connection].acquire(block=True) as producer:
                    producer.publish(body, serializer='pickle', compression='bzip2', exchange=task_exchange,
                                    declare=[task_exchange], routing_key=HandlerType.WALLET_PROCESS, headers={"delay": 2})

        except Exception as e:
            logger.error(f"Error processing task {msg_id}: {e}. Retries: {retries}")
            logger.exception(e)
            retries += 1
            body['meta']['retries'] = retries
            if retries >= MAX_RETRIES:
                logger.error(f"Max retries ({MAX_RETRIES}) reached for message {msg_id}. Removing from queue.")
                message.ack()  # Remove from queue
                # Do NOT re-raise, message is acknowledged and will not be retried
            else:
                logger.info(f"Re-publishing message for retry {retries} (routing_key: {routing_key})")
                task_exchange = Exchange('tasks', type='direct')
                with producers[self.connection].acquire(block=True) as producer:
                    producer.publish(body, serializer='pickle', compression='bzip2', exchange=task_exchange,
                                    declare=[task_exchange], routing_key=routing_key, headers={"delay": 2})
                message.ack()  # Remove the current message so only the new one is retried


def alert_worker(telegram_settings):
    if not telegram_settings['chat']:
        logger.warning("Telegram chat is not configured. Disabling alerts!")
        return

    from alerts.alert_processor import AlertProcessor
    while True:
        logger.debug("Process alerts")
        # enqueue_job()
        p = AlertProcessor(telegram_settings)
        # p.process()
        time.sleep(60 * 2)


if __name__ == '__main__':
    # import config and models from main path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))

    from config import Settings
    settings_module = os.environ.get("BACKEND_SETTINGS", None) or None
    settings = Settings(settings_module)

    from models.sql import create_db_connection
    create_db_connection(settings.SQL_CONF)

    t = threading.Thread(target=alert_worker, args=(settings.TELEGRAM_CONFIG,))
    # t.start()
    logger.info("Alert worker started")

    with Connection(f'redis://{settings.REDIS.get("host")}:{settings.REDIS.get("port")}') as conn:
        while True:
            try:
                worker = Worker(conn)
                worker.run()
            except KeyboardInterrupt:
                logger.error('Keyboard error')
            except Exception as e:
                logger.exception(e)
                time.sleep(2)
