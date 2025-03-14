import os
import sys
import logging
import time
import threading
from kombu.mixins import ConsumerMixin
from kombu import Exchange, Queue, Connection

logger = logging.getLogger("worker")


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

    from kombu.pools import producers
    task_exchange = Exchange('tasks', type='direct')
    with producers[connection].acquire(block=True) as producer:
        producer.publish(payload, serializer='pickle', compression='bzip2', exchange=task_exchange,
                         declare=[task_exchange], routing_key=queue, headers={"delay": 10})


class Worker(ConsumerMixin):

    def __init__(self, connection):
        self.connection = connection

    def get_consumers(self, Consumer, channel):
        return [Consumer(queues=task_queues,
                         accept=['pickle', 'json'],
                         callbacks=[self.process_task])]

    def process_task(self, body, message):
        logger.info(f"Processing task: {message.properties}")
        routing_key = message.delivery_info['routing_key']
        args = body['args']
        kwargs = body['kwargs']
        logger.info(f"Got task with routing_key: {message.delivery_info['routing_key']}!")

        cls_handler = get_request_handler(routing_key)
        if not cls_handler:
            logger.error(f"Handler no exists for routing_key: {routing_key}")
            message.ack()
            return

        handler = cls_handler()
        try:
            handler.process(args)
        except Exception as e:
            # TODO: decide when requeue
            logger.error(e)
            logger.exception(e)
            message.ack()
            raise (e)

        message.ack()


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
