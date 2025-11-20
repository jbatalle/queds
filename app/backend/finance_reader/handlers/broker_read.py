import logging
from models.system import Account
from models.broker import Ticker, StockTransaction
from finance_reader.entities.brokers import SUPPORTED_BROKERS
from finance_reader.utils.yahoo import YahooClient

logger = logging.getLogger("broker_read")


class BrokerReader:
    def __init__(self):
        self.yahoo_client = YahooClient()
        pass

    @staticmethod
    def _validate_data(data):
        logger.debug("Validating data...")
        if 'account_id' not in data:
            return False
        if 'entity_name' not in data:
            return False
        if 'username' not in data:
            return False
        if 'password' not in data:
            return False
        return True

    @staticmethod
    def _get_start_date(account_id):
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

        broker = SUPPORTED_BROKERS.get(broker_name)
        if not broker:
            return

        logger.info("Login...")
        entity_account = broker.login(data)
        if not entity_account:
            return

        start_date =  self._get_start_date(account_id) or "01/01/2017"
        logger.info(f"Reading transactions from {start_date}...")
        transactions = broker.read_transactions(start_date)
        logger.info(f"Found {len(transactions)} transactions in {broker_name}")

        self.parse_read(account_id, entity_account, transactions)
        logger.info("Read done!")

    def parse_read(self, account_id, entity_account, transactions):
        logger.info(f"Updating account id {account_id}")
        broker_account = self._update_account(account_id, entity_account)

        # new implementation
        logger.info("Creating/updating tickers...")
        transaction_isins = {t.ticker.isin: t.ticker for t in transactions}
        # we use ticker.ticker, the last saved, because some brokers change the ISIN of old transactions to new ISIN
        tickers = {ticker.isin: ticker for ticker in
                   Ticker.query.filter(Ticker.isin.in_(transaction_isins.keys())).all()}

        # tickers to be created
        missing_tickers = [t for t in transaction_isins.values() if t.isin not in tickers]
        update_tickers = self._create_or_update_tickers(missing_tickers)

        logger.info("Inserting tickers to DB...")
        Ticker.bulk_insert(list(update_tickers))
        tickers = {ticker.isin: ticker for ticker in list(Ticker.query.all())}

        logger.info(f"Inserting {len(transactions)} transactions to DB...")
        trans_list = []
        for t in transactions:
            r = t.to_dict()
            r['account_id'] = str(broker_account.id)
            r['ticker_id'] = tickers[t.ticker.isin].id
            trans_list.append(r)

        StockTransaction.bulk_insert(trans_list)

    @staticmethod
    def _update_account(account_id, entity_account):
        broker_account = Account.get_by_account_id(account_id)
        if entity_account.currency:
            broker_account.currency = entity_account.currency
        broker_account.balance = entity_account.balance
        broker_account.virtual_balance = entity_account.virtual_balance
        broker_account.save()
        return broker_account

    def _create_or_update_tickers(self, tickers):
        update_tickers = []
        self.yahoo_client.search_by_isin([t for t in tickers if not t.ticker])

        for ticker in tickers:
            logger.info(f"Creating new ticker {ticker.ticker} - {ticker.isin} - {ticker.exchange}!")

            try:
                yahoo_ticker = self.yahoo_client.get_ticker(ticker)
            except:
                yahoo_ticker = None
            ticker = Ticker(ticker=ticker.ticker[:8] if ticker.ticker else ticker.isin[:8],
                            isin=ticker.isin,
                            name=ticker.name,
                            currency=ticker.currency,
                            status=ticker.active,
                            market=ticker.exchange,
                            ticker_yahoo=yahoo_ticker
                            )
            update_tickers.append(ticker)

        return update_tickers

    @staticmethod
    def _create_or_update_ticker_old(tickers, t):
        logger.debug(f"Check ticker {t.ticker.ticker} - {t.ticker.isin} - {t.ticker.active}!")

        # if t.ticker.ticker not in tickers or t.ticker.isin not in [t.isin for t in tickers.values()]:
        if t.ticker.isin not in tickers:  # or t.ticker.isin not in [t.isin for t in tickers.values()]:
            logger.info(f"Creating new ticker {t.ticker.ticker} - {t.ticker.isin} - {t.ticker.exchange}!")
            try:
                yahoo_ticker = YahooClient().get_ticker(t.ticker)
                logger.info(f"Ticker {t.ticker.ticker} - Yahoo ticker: {yahoo_ticker}!")
                # tickers[t.ticker.isin].ticker_yahoo = yahoo_ticker  # , market=exchange
            except:
                yahoo_ticker = None
            ticker = Ticker(ticker=t.ticker.ticker,
                            isin=t.ticker.isin,
                            name=t.ticker.name,
                            currency=t.currency,
                            status=t.ticker.active,
                            market=t.ticker.exchange,
                            ticker_yahoo=yahoo_ticker
                            )
            tickers[t.ticker.isin] = ticker
            return

        # TODO: create else?
        if t.ticker.active == Ticker.Status.ACTIVE:
            # check if some ticker with this ticker already exists, and set to status INACTIVE
            try:
                for db_ticker in tickers.values():
                    if db_ticker.ticker == t.ticker.ticker and db_ticker.isin != t.ticker.isin and db_ticker.status == Ticker.Status.ACTIVE:
                        logger.debug(f"Old ticker already exists! Disabling {t.ticker.ticker} - {db_ticker.isin}")
                        tickers[t.ticker.isin].status = Ticker.Status.INACTIVE
            except:
                pass
        #
        # try:
        #     if not tickers[t.ticker.isin].ticker_yahoo:
        #         yahoo_ticker = YahooClient().get_ticker(t.ticker)
        #         logger.info(f"Ticker {t.ticker.ticker} - Yahoo ticker: {yahoo_ticker}!")
        #         tickers[t.ticker.isin].ticker_yahoo = yahoo_ticker  # , market=exchange
        # except Exception as e:
        #     pass

        tickers[t.ticker.isin].status = t.ticker.active
        return
