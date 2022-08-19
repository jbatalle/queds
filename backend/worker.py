import os
import sys
import logging
from kombu.mixins import ConsumerMixin
from kombu import Exchange, Queue, Connection

logger = logging.getLogger("worker")


class HandlerType:
    BROKER_READ = 'broker'
    CRYPTO_READ = 'crypto'
    WALLET_PROCESS = 'wallet'


_handler_map = {}


def _build_handler_map():
    from finance_reader.handlers.broker_read import BrokerReader
    from finance_reader.handlers.exchange_read import ExchangeReader
    from wallet_processor.handlers.wallet_processor import WalletProcessor

    _handler_map.update({
        HandlerType.BROKER_READ: BrokerReader,
        HandlerType.CRYPTO_READ: ExchangeReader,
        HandlerType.WALLET_PROCESS: WalletProcessor,
    })


def get_request_handler(request_type):
    if not _handler_map:
        _build_handler_map()

    return _handler_map.get(request_type, None)


task_exchange = Exchange('tasks', type='direct')
task_queues = [Queue('broker', task_exchange, routing_key='broker'),
               Queue('crypto', task_exchange, routing_key='crypto'),
               Queue('wallet', task_exchange, routing_key='wallet')]


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
            message.ack()
            raise (e)

        message.ack()


if __name__ == '__main__':
    # import config and models from main path
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))

    from config import Settings
    settings_module = os.environ.get("BACKEND_SETTINGS", None) or None
    settings = Settings(settings_module)

    from models.sql import create_db_connection
    create_db_connection(settings.SQL_CONF)

    with Connection(f'redis://{settings.REDIS.get("host")}:{settings.REDIS.get("port")}') as conn:
        while True:
            try:
                worker = Worker(conn)
                worker.run()
            except KeyboardInterrupt:
                logger.error('Keyboard error')
            except Exception as e:
                logger.exception(e)
