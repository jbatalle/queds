import os
from flask.cli import FlaskGroup
from sqlalchemy import create_engine
from sqlalchemy_utils import database_exists, create_database
from app import app


@app.shell_context_processor
def make_shell_context():
    return {"app": app}


def make_shell_context2():
    return app


app = make_shell_context()['app']
cli = FlaskGroup(create_app=make_shell_context2)


@cli.command('create')
def create_db():
    raise Exception("NotImplemented!")

    engine = create_engine(os.environ.get('DATABASE_URL'))
    if not database_exists(engine.url):
        create_database(engine.url)


def create_broker_account(user_id):
    from models.system import Entity, Account

    entity = Entity.query.filter(Entity.name == "Degiro").first()
    accounts = Account.query.filter(Account.entity == entity).first()
    if accounts:
        return accounts.id

    print("Creating broker account")
    acc = Account(
            name="Degiro acc",
            entity_id=entity.id,
            user_id=user_id,
            currency="EUR",
            balance=500,
            virtual_balance=1800
        )
    acc.save()

    return acc.id


def create_exchange_account(user_id):
    from models.system import Entity, Account

    entity = Entity.query.filter(Entity.name == "Bitstamp").first()
    accounts = Account.query.filter(Account.entity == entity).first()
    if accounts:
        return accounts.id

    print("Creating exchange account")
    acc = Account(
            name="Bitstamp acc",
            entity_id=entity.id,
            user_id=user_id,
            currency="EUR",
            balance=1000
        )
    acc.save()

    return acc.id


def seed_sample_transactions(account_id):
    from models.sql import db_session
    from models.broker import StockTransaction, Ticker

    print("Creating ticker")
    try:
        ticker = Ticker(ticker="TSLA",
                        name="TESLA C",
                        currency="USD",
                        isin="ISIN NUM",
                        ticker_yahoo="TSLA",
                        status=Ticker.Status.ACTIVE
                        )
        ticker.save()
    except:
        ticker = Ticker.query.filter(Ticker.ticker == "TSLA").first()

    print("Inserting broker transactions")
    # Degiro
    objects = []
    for i in range(1, 4):
        order = StockTransaction(
            account_id=account_id,
            external_id=f"external_id_{i}",
            value_date=f"2021-01-0{i}",
            name="TESLA",
            ticker_id=ticker.id,
            shares=10,
            type=StockTransaction.Type.BUY,
            currency="USD",
            price=500.2 + i,
            fee=2,
            exchange_fee=1,
            currency_rate=1)
        objects.append(order)

    # sell order
    order = StockTransaction(
        account_id=account_id,
        external_id=f"external_id_sell",
        value_date=f"2021-02-01",
        name="TESLA",
        ticker_id=ticker.id,
        shares=5,
        type=StockTransaction.Type.SELL,
        currency="USD",
        price=600,
        fee=3,
        exchange_fee=1,
        currency_rate=1)
    objects.append(order)
    order = StockTransaction(
        account_id=account_id,
        external_id=f"external_id_sell2",
        value_date=f"2021-02-02",
        name="TESLA",
        ticker_id=ticker.id,
        shares=10,
        type=StockTransaction.Type.SELL,
        currency="USD",
        price=600,
        fee=3,
        exchange_fee=1,
        currency_rate=1)
    objects.append(order)

    db_session.bulk_save_objects(objects)


def seed_sample_exchange_order(acc_id):
    from models.sql import db_session
    from models.crypto import ExchangeOrder
    objects = [
        ExchangeOrder(
            account_id=acc_id,
            external_id="external_id",
            value_date="2021-01-01",
            pair="ETH/EUR",
            amount=3,
            type=ExchangeOrder.Type.BUY,
            price=950.2,
            fee=12),
        ExchangeOrder(
            account_id=acc_id,
            external_id="external_id2",
            value_date="2021-01-02",
            pair="ETH/EUR",
            amount=3,
            type=ExchangeOrder.Type.BUY,
            price=970.2,
            fee=12),
        ExchangeOrder(
            account_id=acc_id,
            external_id="external_id3",
            value_date="2021-01-03",
            pair="ETH/EUR",
            amount=4,
            type=ExchangeOrder.Type.SELL,
            price=960.2,
            fee=13)
    ]

    db_session.bulk_save_objects(objects)


def create_wallet(acc):
    pass


def create_taxes(acc):
    pass


@cli.command('seed')
def seed_db():
    """Seeds the database with demo data"""
    from loader import load_models
    load_models()
    from models.sql import create_db_connection
    from config import settings
    create_db_connection(settings.SQL_CONF)
    from models.system import User, Entity

    users = User.query.all()

    if not users:
        print("Create user")
        user = User(
            email='demo@queds.com',
            password='supersecret'
        )
        user.save()

    user_id = User.query.filter(User.email == 'demo@queds.com').first().id
    acc_id = create_broker_account(user_id)
    acc_id2 = create_exchange_account(user_id)
    seed_sample_transactions(acc_id)
    seed_sample_exchange_order(acc_id2)
    create_wallet(acc_id)
    create_taxes(acc_id)


if __name__ == '__main__':
    cli()
