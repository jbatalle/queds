from finance_reader.entities import AbstractEntity


class AbstractBroker(AbstractEntity):

    def __init__(self):
        super(AbstractBroker, self).__init__()


from finance_reader.entities.brokers.degiro import Degiro
from finance_reader.entities.brokers.clicktrade import Clicktrade
from finance_reader.entities.brokers.interactive_brokers import InteractiveBrokers


SUPPORTED_BROKERS = {
    "degiro": Degiro(),
    "clicktrade": Clicktrade(),
    "ib": InteractiveBrokers()
}
