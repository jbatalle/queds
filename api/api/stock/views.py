import logging
from flask_restx import Resource, fields, Namespace
from models.broker import Watchlist, Watchlists, Wallet, StockTransaction, Ticker, OpenOrder, ClosedOrder, ProxyOrder
from models.system import Account, Entity, User
from flask import jsonify, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from api import filter_by_username, demo_check
from services.queue import queue_process
from services.yahoo import YahooClient
from sqlalchemy.orm import joinedload


log = logging.getLogger(__name__)
namespace = Namespace("stock")

exchange_account = namespace.model('UserEditModel', {
    "name": fields.String(required=True, min_length=1, max_length=32),
    "entity_id": fields.Integer(required=True)
})


@namespace.route('/brokers')
class BrokerList(Resource):

    def get(self):
        """Returns all brokers."""
        result = Entity.query.filter(Entity.type == Entity.Type.BROKER)
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/accounts')
class AccountList(Resource):

    @jwt_required()
    def get(self):
        """Returns all user broker accounts."""
        result = filter_by_username(Account).filter(Entity.type == Entity.Type.BROKER)
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/orders')
class OrdersCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all user broker orders."""
        args = request.args
        broker_names = args.get('broker', None)
        pagination = args.to_dict()
        user_id = User.find_by_email(get_jwt_identity()).id

        accounts = Account.query.filter(Account.user_id == user_id, Account.entity.has(type=Entity.Type.BROKER))

        if broker_names:
            exchange_list = broker_names.split(",")
            accounts = accounts.filter(Account.name.in_(exchange_list))
        accounts = accounts.all()

        query = StockTransaction.query.options(joinedload('ticker'))\
            .filter(StockTransaction.account_id.in_([a.id for a in accounts])).order_by(
            StockTransaction.value_date.desc())

        limit = int(pagination.get('limit', 10))
        page = int(pagination.get('page', 1)) - 1
        orders = query.limit(limit).offset(page * limit).all()

        items = []
        for order in orders:
            o = order.to_dict()
            o['ticker'] = order.ticker.to_dict()
            items.append(o)

        total = query.count()

        results = {
            "results": items,
            "pagination":
                {
                    "count": total,
                    "page": page,
                    "per_page": limit,
                    "pages": int(total / limit),
                },
        }
        return jsonify(results)


@namespace.route('/tickers')
class TickersCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all tickers."""
        orders = Ticker.query.all()
        items = []
        for order in orders:
            o = order.to_dict()
            items.append(o)
        return jsonify(items)


@namespace.route('/wallet')
class WalletCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all open_orders."""

        username = get_jwt_identity()
        user_id = User.find_by_email(username).id
        wallet_items = Wallet.query.options(joinedload('ticker')).options(joinedload('open_orders'))\
            .options(joinedload('open_orders.transaction')).filter(Wallet.user_id == user_id).all()
        tickers_yahoo = {t.ticker.ticker_yahoo: t.ticker.ticker for t in wallet_items if t.ticker.ticker_yahoo}
        symbols = ",".join(list(tickers_yahoo.keys()))
        if len(wallet_items) == 0:
            return {'message': "Unable to detect tickers in open transactions"}, 400

        # TODO: to be moved to backend
        y = YahooClient()
        to_be_req = Ticker.query.filter(Ticker.id.in_([w.ticker_id for w in wallet_items])).filter(Ticker.ticker_yahoo == None).all()
        # to_be_req = [t for t in tickers if not t.ticker_yahoo]
        log.info(f"Tickers without yahoo: {to_be_req}")
        for no_yahoo_symbol in to_be_req:
            yahoo_symbol = y.get_yahoo_symbol(no_yahoo_symbol.ticker)
            log.info(f"{no_yahoo_symbol.ticker} - {yahoo_symbol}")
            if not yahoo_symbol:
                continue
            no_yahoo_symbol.ticker_yahoo = yahoo_symbol
            # this update here can cause delay in the joinedload due is commiting to the DB!
            q = no_yahoo_symbol.save()

        if len(symbols) == 0:
            log.error("Unable to detect tickers in open transactions")
            return {'message': "Unable to detect tickers in open transactions"}, 400

        try:
            yahoo_prices = y.get_current_tickers(symbols)
        except:
            yahoo_prices = []
            log.error("Error when retrieving prices from yahoo")

        tickers_by_ticker = {}
        for d in yahoo_prices:
            tickers_by_ticker[tickers_yahoo[d.get('symbol')]] = d

        items = []
        for r in wallet_items:
            item = r.json
            item['ticker'] = r.ticker.to_dict()
            item['open_orders'] = []
            for oo in r.open_orders:
                oo_item = oo.json
                oo_item['transaction'] = oo.transaction.json
                item['open_orders'].append(oo_item)

            item['market'] = {}
            if r.ticker.ticker in tickers_by_ticker:
                item['market'] = tickers_by_ticker[r.ticker.ticker]
            # item['transaction'] = r.transaction.json
            items.append(item)
        return jsonify(items)


@namespace.route('/tax')
class Tax(Resource):

    @jwt_required()
    def get(self):
        """Returns all closed orders."""
        args = request.args.to_dict()

        year = int(args.get('year', 2021))
        username = get_jwt_identity()
        user_id = User.find_by_email(username).id
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.BROKER)).all()

        closed_orders = ClosedOrder.query.options(joinedload('sell_transaction'))\
            .options(joinedload('buy_transaction')).options(joinedload('buy_transaction.transaction'))\
            .join(ClosedOrder.sell_transaction) \
            .filter(StockTransaction.value_date >= f"{year}-01-01") \
            .filter(StockTransaction.value_date < f"{year + 1}-01-01") \
            .filter(StockTransaction.account_id.in_([a_id for a_id in accounts])).all()

        items = []
        for r in closed_orders:
            item = r.sell_transaction.json
            item['ticker'] = r.sell_transaction.ticker.json
            children = []
            for q in r.buy_transaction:
                buy = q.transaction.json
                buy['shares'] = q.shares
                buy['partial_fee'] = q.partial_fee
                children.append(buy)

            item['children'] = children
            items.append(item)
        return jsonify(items)


@namespace.route('/calculate')
class Calculate(Resource):

    @demo_check
    @jwt_required()
    def get(self):
        current_user_email = get_jwt_identity()
        user_id = User.find_by_email(current_user_email).id
        data = {
            "user_id": user_id,
            "mode": "stock"
        }
        queue_process(data)


@namespace.route('/stats')
class CalcStats(Resource):

    @jwt_required()
    def get(self):
        user_id = User.find_by_email(get_jwt_identity()).id

        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.BROKER)).all()
        query = StockTransaction.query.filter(StockTransaction.account_id.in_([a_id for a_id in accounts])).order_by(
            StockTransaction.value_date.desc())

        orders = query.with_entities(StockTransaction.type, StockTransaction.shares, StockTransaction.price, StockTransaction.currency_rate).all()
        invested = 0
        for o in orders:
            if o[0] == StockTransaction.Type.BUY:
                invested += o.shares * o.price * o.currency_rate
            else:
                invested -= o.shares * o.price * o.currency_rate

        # Closed orders
        closed_orders = ClosedOrder.query.join(ClosedOrder.sell_transaction) \
            .filter(StockTransaction.account_id.in_([a_id for a_id in accounts])).all()

        gain = 0
        for o in closed_orders:
            gain += (o.sell_transaction.shares * o.sell_transaction.price * o.sell_transaction.currency_rate) + o.sell_transaction.fee + o.sell_transaction.exchange_fee
            for t in o.buy_transaction:
                buy_order = t.transaction
                gain -= t.shares * buy_order.price * buy_order.currency_rate - t.partial_fee

        stats = {
            "portfolio_value": 0,
            "invested": invested,
            "gain": gain,
            # "fiat": 0
        }

        return stats


@namespace.route('/fx_rate')
class Calculate(Resource):

    @demo_check
    @jwt_required()
    def get(self):
        """Returns current eur/usd price."""
        y = YahooClient()
        r = y.get_currency()
        return r, 200
