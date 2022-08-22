import logging
from models.system import Account
from models.broker import Ticker, StockTransaction
from finance_reader.entities.brokers import SUPPORTED_BROKERS
from finance_reader.utils.yahoo import YahooClient

logger = logging.getLogger("broker_read")


class BrokerReader:
    def __init__(self):
        pass

    @staticmethod
    def _validate_data(data):
        logger.info("Validating data...")
        if 'account_id' not in data:
            return False
        if 'entity_name' not in data:
            return False
        if 'username' not in data:
            return False
        if 'password' not in data:
            return False
        return True

    def _get_start_date(self, account_id):
        logger.info("Reading last transaction in order to extract start_date")
        last_transaction = StockTransaction.query.filter(StockTransaction.account_id==account_id).order_by(StockTransaction.value_date.desc()).first()
        if last_transaction:
            logger.info(f"Setting start date to: {last_transaction.value_date}")
            return last_transaction.value_date.strftime("%d/%m/%Y")
        return None

    def process(self, data):
        if not self._validate_data(data):
            logger.error("Invalid request data")
            return

        account_id = data.get('account_id')
        broker_name = data.get('entity_name').lower()
        username = data.get('username')
        password = data.get('password')

        broker = SUPPORTED_BROKERS.get(broker_name)
        if not broker:
            return

        logger.info("Login...")
        entity_account = broker.login(username, password)
        if not entity_account:
            return

        start_date = self._get_start_date(account_id) or "01/01/2017"
        logger.info(f"Reading transactions from {start_date}...")
        transactions = broker.read_transactions(start_date)
        logger.info("Found {} transactions in {}".format(len(transactions), broker_name))

        logger.info("Done. Transactions: {}".format(len(transactions)))
        self._parse_read(account_id, entity_account, transactions)
        logger.info("Read done!")

    @staticmethod
    def _update_account(account_id, entity_account):
        broker_account = Account.get_by_account_id(account_id)
        if entity_account.currency:
            broker_account.currency = entity_account.currency
        broker_account.balance = entity_account.balance
        broker_account.virtual_balance = entity_account.virtual_balance
        broker_account.save()
        return broker_account

    def _parse_read(self, account_id, entity_account, trans):
        logger.info(f"Updating account: {account_id}")
        broker_account = self._update_account(account_id, entity_account)

        logger.info("Get tickers")
        tickers = list(Ticker.query.all())
        tickers = {ticker.isin: ticker for ticker in tickers}

        logger.info(f"Processing {len(trans)} transactions")
        transactions = []
        for t in trans:
            r = t.to_dict()
            r['account_id'] = str(broker_account.id)

            if t.ticker.isin in list(tickers.keys()):
                if tickers[t.ticker.isin].status != t.ticker.active:
                    tickers[t.ticker.isin].save()
            else:
                ticker = self._create_new_ticker(tickers, t)
                tickers[t.ticker.isin] = ticker

            r['ticker_id'] = tickers[t.ticker.isin].id
            transactions.append(r)

        StockTransaction.bulk_insert(transactions)

    @staticmethod
    def _create_new_ticker(tickers, t):
        logger.info(f"Creating new ticker {t.ticker.ticker} - {t.ticker.isin}!")

        if t.ticker.active == Ticker.Status.ACTIVE:
            # check if some ticker with this ticker already exists, and set to status INACTIVE
            try:
                old_tickers = [tick for tick in tickers.values() if
                               tick.ticker == t.ticker.ticker and tick.status == Ticker.Status.ACTIVE]
                for old_ticker in old_tickers:
                    logger.info(f"Old ticker already exists! Disabling {t.ticker.ticker} - {old_ticker.isin}")
                    old_ticker.status = Ticker.Status.INACTIVE
                    old_ticker.save()
            except:
                pass

        yahoo_ticker = YahooClient().get_ticker(t.ticker)
        logger.info(f"Ticker {t.ticker.ticker} - Yahoo ticker: {yahoo_ticker}!")
        ticker = Ticker(ticker=t.ticker.ticker,
                        isin=t.ticker.isin,
                        name=t.ticker.name,
                        currency=t.currency,
                        status=t.ticker.active,
                        ticker_yahoo=yahoo_ticker  # , market=exchange
                        )
        try:
            ticker.save()
        except Exception as e:
            logger.info(f"Unable to store ticker {ticker.ticker.ticker}: {e}")

        return ticker
