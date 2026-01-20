import logging
import redis
import json
import time


from models.system import Account, EntityCredentialType, AccountCredentialParam
from models.broker import Ticker, StockTransaction
from finance_reader.entities.brokers import SUPPORTED_BROKERS
from finance_reader.utils.yahoo import YahooClient
from models.cryptography import AESCipher
from sqlalchemy.dialects.postgresql import insert
from config import settings

logger = logging.getLogger("broker_read")


def _store_validation_status(account_id, status_data):
    """Store validation status in Redis for polling"""
    try:
        redis_client = redis.Redis(
            host=settings.REDIS.get("host"),
            port=settings.REDIS.get("port", 6379),
            decode_responses=True,
        )

        status_key = f"validation_status:account_{account_id}"
        new_status = status_data.get("status")
        
        # Get old status and clear if transitioning to different state
        old_status_json = redis_client.get(status_key)
        if old_status_json:
            old_status_data = json.loads(old_status_json)
            old_status = old_status_data.get("status")
            
            # If transitioning to a different status, delete the old one first
            if old_status and old_status != new_status:
                redis_client.delete(status_key)
                logger.info(
                    f"Cleared old status for account {account_id}: {old_status} → {new_status}"
                )
        
        # Store new status with fresh timestamp
        status_json = json.dumps({**status_data, "timestamp": time.time()})
        redis_client.set(status_key, status_json, ex=300)  # Expire after 5 minutes
        
        logger.info(
            f"Stored validation status for account {account_id}: {status_data.get('status')}"
        )
        return True
    except Exception as e:
        logger.error(f"Failed to store validation status for account {account_id}: {e}")
        return False


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
        last_transaction = (
            StockTransaction.query.filter(StockTransaction.account_id == account_id)
            .order_by(StockTransaction.value_date.desc())
            .first()
        )
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
        login_result = broker.login(data)

        # Handle multi-step authentication
        if isinstance(login_result, dict):
            if login_result.get("status") == "device_validation_required":
                logger.info("Device validation required")

                # Store validation status in Redis for polling
                _store_validation_status(
                    account_id,
                    {
                        "status": "validation_required",
                        "requires_otp": login_result.get("requires_otp", False),
                        "message": login_result.get(
                            "message", "Device validation required"
                        ),
                        "account_id": account_id,
                    },
                )

                return {
                    "status": "validation_required",
                    "requires_otp": login_result.get("requires_otp", False),
                    "message": login_result.get(
                        "message", "Device validation required"
                    ),
                    "account_id": account_id,
                }
            elif login_result.get("status") == "success":
                # Save device tokens if returned
                if "cookie_token" in login_result:
                    self._save_device_token(
                        account_id,
                        EntityCredentialType.Type.COOKIE_TOKEN,
                        login_result["cookie_token"],
                        data.get("encrypt_password"),
                    )
                if "token" in login_result:
                    self._save_device_token(
                        account_id,
                        EntityCredentialType.Type.DEVICE_TOKEN,
                        login_result["token"],
                        data.get("encrypt_password"),
                    )
                entity_account = login_result.get("account")
            else:
                logger.error(f"Unexpected login result: {login_result}")
                if (
                    isinstance(login_result, dict)
                    and login_result.get("status") == "error"
                ):
                    pass
                return
        else:
            # Non-OTP login successful
            entity_account = login_result
            logger.info(f"Non-OTP authentication successful for account {account_id}, proceeding to read transactions")

        if not entity_account:
            return

        try:
            start_date = self._get_start_date(account_id) or "01/01/2017"
            logger.info(f"Reading transactions from {start_date}...")
            transactions = broker.read_transactions(start_date)
            logger.info(f"Found {len(transactions)} transactions in {broker_name}")

            self.parse_read(account_id, entity_account, transactions)
            logger.info("Read done!")
        except Exception as e:
            logger.error(f"Error reading transactions for account {account_id}: {str(e)}")
            # Still store error status so frontend knows read failed
            _store_validation_status(
                account_id,
                {
                    "status": "error",
                    "message": "An error occurred while reading transactions. Please review server logs.",
                    "account_id": account_id,
                },
            )
            return

        # Store success status when read completes successfully
        # We only reach this point if validation_required was not returned and no errors occurred
        logger.info(f"Stored validation status: success for account {account_id}")
        _store_validation_status(
            account_id,
            {
                "status": "success",
                "message": "Account read successfully",
                "account_id": account_id,
            },
        )

    def parse_read(self, account_id, entity_account, transactions):
        logger.info(f"Updating account id {account_id}")
        broker_account = self._update_account(account_id, entity_account)

        # new implementation
        logger.info("Creating/updating tickers...")

        # Separate cash-only transactions from ticker transactions
        ticker_transactions = [t for t in transactions if t.ticker is not None]
        cash_transactions = [t for t in transactions if t.ticker is None]

        transaction_isins = {t.ticker.isin: t.ticker for t in ticker_transactions}
        # we use ticker.ticker, last saved, because some brokers change the ISIN of old transactions to new ISIN
        tickers = {
            ticker.isin: ticker
            for ticker in Ticker.query.filter(
                Ticker.isin.in_(transaction_isins.keys())
            ).all()
        }

        # tickers to be created
        missing_tickers = [
            t for t in transaction_isins.values() if t.isin not in tickers
        ]
        update_tickers = self._create_or_update_tickers(missing_tickers)

        logger.info("Inserting tickers to DB...")
        Ticker.bulk_insert(list(update_tickers))
        tickers = {ticker.isin: ticker for ticker in list(Ticker.query.all())}

        logger.info(f"Inserting {len(transactions)} transactions to DB...")
        trans_list = []

        # Process ticker transactions
        for t in ticker_transactions:
            r = t.to_dict()
            r["account_id"] = str(broker_account.id)
            r["ticker_id"] = tickers[t.ticker.isin].id
            trans_list.append(r)

        # Process cash-only transactions (deposits, withdrawals, dividends)
        for t in cash_transactions:
            r = t.to_dict()
            r["account_id"] = str(broker_account.id)
            r["ticker_id"] = None
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
            logger.info(
                f"Creating new ticker {ticker.ticker} - {ticker.isin} - {ticker.exchange}!"
            )

            try:
                yahoo_ticker = self.yahoo_client.get_ticker(ticker)
            except:
                yahoo_ticker = None
            ticker = Ticker(
                ticker=ticker.ticker[:8] if ticker.ticker else ticker.isin[:8],
                isin=ticker.isin,
                name=ticker.name,
                currency=ticker.currency,
                status=ticker.active,
                market=ticker.exchange,
                ticker_yahoo=yahoo_ticker,
            )
            update_tickers.append(ticker)

        return update_tickers

    def _save_device_token(self, account_id, token_type, device_token, encrypt_password):
        """Save device token to account credentials"""
        if not device_token or not encrypt_password:
            return

        logger.info(f"Saving device token for account {account_id}. device_token: {device_token}")

        # Get device token credential type
        # NOTE: entity_credential_types table may not exist in database
        # If table doesn't exist or DEVICE_TOKEN type not found, skip saving
        device_token_type = EntityCredentialType.query.filter(
            EntityCredentialType.cred_type == token_type.name
        ).first()

        if not device_token_type:
            logger.warning(
                "Device token credential type not found or entity_credential_types table doesn't exist"
            )
            logger.info("Skipping device token save (not critical for OTP flow)")
            return

        try:
            cipher = AESCipher(encrypt_password)
            
            # Serialize device_token to JSON string if it's a dict/list
            if isinstance(device_token, (dict, list)):
                device_token_str = json.dumps(device_token)
            else:
                device_token_str = device_token
            
            encrypted_token = cipher.encrypt(device_token_str)

            # Save device token
            values = {
                "account_id": account_id,
                "credential_type_id": device_token_type.id,
                "value": encrypted_token.decode(),
            }
            stmt = insert(AccountCredentialParam).values(values)
            stmt = stmt.on_conflict_do_update(
                index_elements=["credential_type_id", "account_id"],
                set_={"value": stmt.excluded.value},
            )

            cred_param = AccountCredentialParam()
            cred_param.update_on_conflict(stmt)
            logger.info("Device token saved successfully")

        except Exception as e:
            logger.error(f"Error saving device token: {e}")

    @staticmethod
    def _create_or_update_ticker_old(tickers, t):
        logger.debug(
            f"Check ticker {t.ticker.ticker} - {t.ticker.isin} - {t.ticker.active}!"
        )

        # if t.ticker.ticker not in tickers or t.ticker.isin not in [t.isin for t in tickers.values()]:
        if (
            t.ticker.isin not in tickers
        ):  # or t.ticker.isin not in [t.isin for t in tickers.values()]:
            logger.info(
                f"Creating new ticker {t.ticker.ticker} - {t.ticker.isin} - {t.ticker.exchange}!"
            )
            try:
                yahoo_ticker = YahooClient().get_ticker(t.ticker)
                logger.info(f"Ticker {t.ticker.ticker} - Yahoo ticker: {yahoo_ticker}!")
                # tickers[t.ticker.isin].ticker_yahoo = yahoo_ticker  # , market=exchange
            except:
                yahoo_ticker = None
            ticker = Ticker(
                ticker=t.ticker.ticker,
                isin=t.ticker.isin,
                name=t.ticker.name,
                currency=t.currency,
                status=t.ticker.active,
                market=t.ticker.exchange,
                ticker_yahoo=yahoo_ticker,
            )
            tickers[t.ticker.isin] = ticker
            return

        # TODO: create else?
        if t.ticker.active == Ticker.Status.ACTIVE:
            # check if some ticker with this ticker already exists, and set to status INACTIVE
            try:
                for db_ticker in tickers.values():
                    if (
                        db_ticker.ticker == t.ticker.ticker
                        and db_ticker.isin != t.ticker.isin
                        and db_ticker.status == Ticker.Status.ACTIVE
                    ):
                        logger.debug(
                            f"Old ticker already exists! Disabling {t.ticker.ticker} - {db_ticker.isin}"
                        )
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
