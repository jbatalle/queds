import logging
from datetime import datetime
from flask_restx import Resource, fields, Namespace
from models.broker import Watchlist, Watchlists, Wallet, StockTransaction, Ticker, OpenOrder, ClosedOrder, ProxyOrder
from models.system import Account, Entity, User
from flask import jsonify, request
from sqlalchemy import or_
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
        print("SHit")
        result = filter_by_username(Account).filter(Entity.type == Entity.Type.BROKER)
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/wallet')
class WalletCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all open_orders."""
        user_id = get_jwt_identity()

        wallet_items = (Wallet.query
                        .options(joinedload(Wallet.ticker))
                        .options(joinedload(Wallet.open_orders).joinedload(OpenOrder.transaction).joinedload(StockTransaction.account))
                        .filter(Wallet.user_id == user_id).all())

        if len(wallet_items) == 0:
            return [], 200

        tickers_yahoo = {t.ticker.ticker_yahoo: t.ticker.ticker for t in wallet_items if t.ticker.ticker_yahoo}
        symbols = ",".join(list(tickers_yahoo.keys()))
        if len(symbols) == 0:
            log.error("Unable to detect tickers in open transactions")
            # return {'message': "Unable to detect tickers in open transactions"}, 400

        y = YahooClient()
        try:
            yahoo_prices = y.get_current_tickers(symbols)
        except Exception as e:
            yahoo_prices = []
            log.error(f"Error when retrieving prices from yahoo: {e}")

        tickers_by_ticker = {}
        for d in yahoo_prices:
            #if tickers_yahoo[d.get('ticker_yahoo')] not in tickers_by_ticker:
#                log.warning(f"Symbol {d.get('symbol')} not in tickers")
#                continue
            tickers_by_ticker[tickers_yahoo[d.get('symbol')]] = d

        fx_rate = y.get_currency() or 1
        items = []
        for idx, r in enumerate(wallet_items):
            item = r.json
            item['ticker'] = r.ticker.to_dict()
            item['close_fees'] = r.fees/len(r.open_orders) if len(r.open_orders) > 0 else 0
            item['open_orders'] = []
            item['base_cost'] = 0  # cost of open orders in user currency
            item['current_benefit'] = 0  # benefits with current values and with closed orders in user currency
            item['base_current_value'] = 0  # portfolio value in user currency
            item['current_value'] = 0  # in ticker currency
            item['base_previous_value'] = 0  # portfolio value previous day in user currency

            for oo in r.open_orders:
                oo_item = oo.json
                oo_item['transaction'] = oo.transaction.json
                # oo_item['cost'] = oo.shares * oo.transaction.price
                oo_item['cost'] = oo.shares * oo.price
                # TODO: transaction fee should be partial in case of partial sell
                # oo_item['base_cost'] = round(oo_item['cost'] * oo.transaction.currency_rate - oo.transaction.fee - oo.transaction.exchange_fee, 2)
                oo_item['base_cost'] = round(oo_item['cost'] * oo.currency_rate - oo.transaction.fee - oo.transaction.exchange_fee, 2)
                item['base_cost'] += oo_item['base_cost']
                item['open_orders'].append(oo_item)

            item['market'] = {}
            if r.ticker.ticker in tickers_by_ticker:
                item['market'] = tickers_by_ticker[r.ticker.ticker]

            item['current_value'] = r.shares * (item['market'].get('price', 0) or 0)
            item['previous_day_value'] = r.shares * (item['market'].get('previous_close', 0) or 0)

            item_fx_rate = fx_rate if r.ticker.currency != 'EUR' else 1
            # item['current_benefit'] = r.benefits + item['close_fees'] + item['current_value'] * item_fx_rate - (item['base_cost'])
            item['current_benefit'] = item['close_fees'] + item['current_value'] * item_fx_rate - (item['base_cost'])
            item['base_current_value'] += item['current_value'] * item_fx_rate
            item['base_previous_value'] += item['previous_day_value'] * item_fx_rate

            items.append(item)

        return jsonify(items)


@namespace.route('/orders')
class OrdersCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all user broker orders."""
        args = request.args
        broker_names = args.get('broker', None)
        pagination = args.to_dict()
        search = args.get('search', None)
        user_id = get_jwt_identity()
        accounts = Account.query.filter(Account.user_id == user_id, Account.entity.has(type=Entity.Type.BROKER))

        if broker_names:
            exchange_list = broker_names.split(",")
            accounts = accounts.filter(Account.name.in_(exchange_list))
        accounts = accounts.all()

        query = StockTransaction.query \
            .join(StockTransaction.ticker) \
            .options(joinedload(StockTransaction.ticker)) \
            .filter(StockTransaction.account_id.in_([a.id for a in accounts])) \
            .order_by(StockTransaction.value_date.desc())

        if search:
            query = query.filter(or_(Ticker.ticker.ilike(f"%{search}%"), Ticker.name.ilike(f"%{search}%"), Ticker.isin.ilike(f"%{search}%")))

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


@namespace.route('/tax')
class Tax(Resource):

    @jwt_required()
    def get(self):
        """Returns all closed orders."""
        args = request.args.to_dict()

        year = int(args.get('year', datetime.now().year - 1))
        user_id = get_jwt_identity()
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.BROKER)).all()

        closed_orders = ClosedOrder.query.options(joinedload(ClosedOrder.sell_transaction).joinedload(StockTransaction.ticker))\
            .options(joinedload(ClosedOrder.buy_transaction).joinedload(ProxyOrder.transaction)) \
            .join(ClosedOrder.sell_transaction) \
            .filter(StockTransaction.value_date >= f"{year}-01-01") \
            .filter(StockTransaction.value_date < f"{year + 1}-01-01") \
            .filter(StockTransaction.account_id.in_([a_id[0] for a_id in accounts])).all()

        items = []
        for r in closed_orders:
            item = r.sell_transaction.json
            # item['ticker'] = r.sell_transaction.ticker.to_dict()
            children = []
            for q in r.buy_transaction:
                buy = q.transaction.json
                buy['shares'] = q.shares
                buy['price'] = q.price
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
        user_id = get_jwt_identity()
        data = {
            "user_id": user_id,
            "mode": "stock"
        }
        queue_process(data)


@namespace.route('/stats')
class CalcStats(Resource):

    @jwt_required()
    def get(self):
        """
        Returns portfolio value, total buy amount, total sell amount and the gain of the closed orders.
        """
        user_id = get_jwt_identity()
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.BROKER)).all()

        query = StockTransaction.query.filter(StockTransaction.account_id.in_([a_id[0] for a_id in accounts])).order_by(
            StockTransaction.value_date.desc())

        orders = query.with_entities(StockTransaction.type, StockTransaction.shares, StockTransaction.price,
                                     StockTransaction.currency_rate, StockTransaction.fee,
                                     StockTransaction.exchange_fee).all()

        buy = 0
        sell = 0
        for o in orders:
            if o[0] == StockTransaction.Type.BUY:
                buy += o.shares * o.price * o.currency_rate - o.fee - o.exchange_fee
            elif o[0] == StockTransaction.Type.SELL:
                sell -= o.shares * o.price * o.currency_rate + o.fee + o.exchange_fee
            else:
                continue

        # TODO: get all values from closed orders
        # TODO2: save global info into new table

        # Closed orders
        closed_orders = ClosedOrder.query.options(joinedload(ClosedOrder.sell_transaction)) \
            .options(joinedload(ClosedOrder.buy_transaction).joinedload(ProxyOrder.transaction)) \
            .join(ClosedOrder.sell_transaction) \
            .filter(StockTransaction.account_id.in_([a_id[0] for a_id in accounts])).all()

        # Get the current year
        current_year = datetime.now().year
        gain = 0
        current_year_gain = 0

        for o in closed_orders:
            # Calculate the total gain

            buy_amount = sum(t.shares * t.transaction.price * t.transaction.currency_rate for t in o.buy_transaction)
            buy_shares = sum(t.shares for t in o.buy_transaction)
            buy_fees = sum(t.partial_fee for t in o.buy_transaction)
            total_buy_value = buy_amount - buy_fees

            # sell_amount = o.sell_transaction.shares * o.sell_transaction.price * o.sell_transaction.currency_rate
            # We need to use the buy shares, as the sell_transaction can have partial sells
            sell_amount = buy_shares * o.sell_transaction.price * o.sell_transaction.currency_rate
            sell_fees = o.sell_transaction.fee + o.sell_transaction.exchange_fee
            total_sell_value = sell_amount + sell_fees

            gain += total_sell_value - total_buy_value

            # Check if the closed order happened in the current year
            sell_transaction_date = o.sell_transaction.value_date
            if sell_transaction_date.year == current_year:
                current_year_gain += total_sell_value - total_buy_value

        stats = {
            "portfolio_value": 0,
            "buy": buy,
            "sell": sell,
            "gain": gain,
            "current_year_gain": current_year_gain
        }
        return stats


@namespace.route('/fx_rate')
class FxRate(Resource):

    @jwt_required()
    def get(self):
        """Returns current eur/usd price."""
        y = YahooClient()
        r = y.get_currency()
        return r, 200

@namespace.route('/ticker')
class TickerClass(Resource):

    @demo_check
    @jwt_required()
    def post(self):
        """Create an account."""
        user_id = get_jwt_identity()

        content = request.get_json(silent=True)

        print(content['id'])
        ticker = Ticker.query.filter(Ticker.id==content['id']).one()
        ticker.ticker_yahoo = content['ticker_yahoo']
        ticker.save()

        return {'message': 'Ticker updated!'}

