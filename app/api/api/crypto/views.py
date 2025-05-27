import logging
from datetime import datetime
from flask import request, jsonify
from flask_restx import Resource, Namespace
from models.crypto import (ExchangeWallet, ExchangeClosedOrder, ExchangeOpenOrder, ExchangeProxyOrder, CryptoEvent)
from models.system import Account, Entity, User, EntityCredentialType
from flask_jwt_extended import jwt_required, get_jwt_identity
from api import filter_by_username, demo_check
from services.queue import queue_process
from services.cryptocompare import CryptoCompareClient
from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)
namespace = Namespace("crypto")


@namespace.route('/exchanges')
class List(Resource):

    def get(self):
        """Returns all exchange."""
        result = Entity.query.filter(Entity.type == Entity.Type.EXCHANGE)
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/accounts')
class AccountList(Resource):

    @jwt_required()
    def get(self):
        """Returns all exchange accounts."""
        result = filter_by_username(Account).filter(Entity.type == Entity.Type.EXCHANGE)
        items = []
        for r in result:
            items.append(r.json)
        return jsonify(items)


@namespace.route('/wallet/assets')
class BalanceList(Resource):

    @jwt_required()
    def get(self):
        """Returns wallet assets without price info."""
        user_id = get_jwt_identity()

        wallet_items = (ExchangeWallet.query
                        .options(joinedload(ExchangeWallet.open_orders)
                                 .joinedload(ExchangeOpenOrder.exchange))
                        .options(joinedload(ExchangeWallet.open_orders)
                                 .joinedload(ExchangeOpenOrder.order)
                                 .joinedload(CryptoEvent.account))
                        .filter(ExchangeWallet.user_id == user_id).all())

        if not wallet_items:
            return [], 200

        assets = []
        for r in wallet_items:
            item = r.json
            item['open_orders'] = [oo.json for oo in r.open_orders]
            assets.append(item)

        return jsonify(assets)

@namespace.route('/wallet/prices')
class WalletPrices(Resource):

    @jwt_required()
    def post(self):
        """Returns price info for given currencies."""
        data = request.get_json()
        currencies = data.get('currencies', [])

        if not currencies:
            return [], 200

        c = CryptoCompareClient()
        prices_eur = c.get_prices("EUR", currencies)
        changes_24h = c.get_changes("EUR", currencies)
        prices_usd = {}  # You can populate these as needed
        prices_btc = {}

        # replace some currencies
        prices_eur = {key.replace("MIOTA", "IOTA").replace("BTT", "BTTC"): value for key, value in prices_eur.items()}

        return jsonify({
            'eur': prices_eur,
            'usd': prices_usd,
            'btc': prices_btc,
            'changes_24h': changes_24h
        })


@namespace.route('/orders')
class OrdersCollection(Resource):

    @jwt_required()
    def get(self):
        """Returns all user exchange orders."""
        args = request.args
        exchange_names = args.get('exchange', None)
        pagination = args.to_dict()
        search = args.get('search', None)
        user_id = get_jwt_identity()

        accounts = Account.query.filter(Account.user_id == user_id, Account.entity.has(type=Entity.Type.EXCHANGE))

        if exchange_names:
            exchange_list = exchange_names.split(",")
            accounts = accounts.filter(Account.name.in_(exchange_list))
        accounts = accounts.all()
        account_ids = [a.id for a in accounts]

        # If no accounts are found, return an empty result
        if not account_ids:
            return jsonify({
                "results": [],
                "pagination": {
                    "count": 0,
                    "page": 1,
                    "per_page": pagination.get('limit', 50),
                    "pages": 0
                }
            })

        # Define limit and offset for pagination
        limit = int(pagination.get('limit', 50))
        page = int(pagination.get('page', 1)) - 1
        offset = page * limit

        query = CryptoEvent.query.filter(CryptoEvent.account_id.in_([a.id for a in accounts])) \
            .order_by(CryptoEvent.value_date.desc())

        # Apply search filter
        if search:
            query = query.filter(CryptoEvent.symbol.ilike(f"%{search}%"))

        # Get total count before applying pagination
        total = query.count()

        # Apply pagination
        paginated_results = query.limit(limit).offset(offset).all()

        # Convert results to dictionary format
        items = []
        for row in paginated_results:
            o = row.to_dict()

            # Append currency details based on type
            if row.type in [CryptoEvent.Type.BUY, CryptoEvent.Type.SELL]:
                o['currency_source'] = row.symbol.split("/")[0]
                o['currency_target'] = row.symbol.split("/")[1]
            elif row.type == CryptoEvent.Type.DEPOSIT:
                o['currency_source'] = row.symbol  # Currency is mapped to pair
                o['currency_target'] = ""
            elif row.type == CryptoEvent.Type.WITHDRAWAL:
                o['currency_source'] = ""
                o['currency_target'] = row.symbol  # Currency is mapped to pair

            items.append(o)

        # Return results with pagination details
        results = {
            "results": items,
            "pagination": {
                "count": total,
                "page": page + 1,
                "per_page": limit,
                "pages": (total + limit - 1) // limit,  # Total pages, handle edge cases
            },
        }
        return jsonify(results)
        return


@namespace.route('/tax')
class CryptoTax(Resource):
    @jwt_required()
    def get(self):
        """Returns all closed orders."""
        args = request.args.to_dict()
        year = int(args.get('year', datetime.now().year - 1))
        user_id = get_jwt_identity()
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.EXCHANGE)).all()

        closed_orders = ExchangeClosedOrder.query.options(joinedload(ExchangeClosedOrder.sell_order)) \
            .options(joinedload(ExchangeClosedOrder.buy_order).joinedload(ExchangeProxyOrder.order)) \
            .join(ExchangeClosedOrder.sell_order) \
            .filter(CryptoEvent.value_date >= f"{year}-01-01") \
            .filter(CryptoEvent.value_date < f"{year + 1}-01-01") \
            .filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).all()

        items = []
        for r in closed_orders:
            item = r.sell_order.json
            children = []
            for q in r.buy_order:
                buy = q.order.json
                buy['amount'] = q.amount
                buy['price'] = q.user_price
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
            "mode": "crypto"
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
                                                                  Account.entity.has(type=Entity.Type.EXCHANGE)).all()
        query = CryptoEvent.query.filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).order_by(
            CryptoEvent.value_date.desc())

        orders = query.with_entities(CryptoEvent.type, CryptoEvent.amount, CryptoEvent.price,
                                     CryptoEvent.fee, CryptoEvent.event_type).all()
        buy = 0
        sell = 0
        for o in orders:
            if o.event_type == 'exchange_transaction':
                continue
            if o[0] == CryptoEvent.Type.BUY:
                buy += o.amount * o.price - o.fee
            elif o[0] == CryptoEvent.Type.SELL:
                sell -= o.amount * o.price + o.fee
            else:
                continue

        # Closed orders
        closed_orders = ExchangeClosedOrder.query.options(joinedload(ExchangeClosedOrder.sell_order))\
            .options(joinedload(ExchangeClosedOrder.buy_order).joinedload(ExchangeProxyOrder.order)) \
            .join(ExchangeClosedOrder.sell_order) \
            .filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).all()

        # Get the current year
        current_year = datetime.now().year
        gain = 0
        current_year_gain = 0

        for o in closed_orders:
            # Calculate the total gain
            buy_amount = sum(t.amount * (t.user_price or 0) for t in o.buy_order)
            buy_shares = sum(t.amount for t in o.buy_order)
            buy_fees = sum(t.partial_fee for t in o.buy_order)
            total_buy_value = buy_amount - buy_fees

            # sell_amount = o.sell_transaction.shares * o.sell_transaction.price * o.sell_transaction.currency_rate
            # We need to use the buy shares, as the sell_transaction can have partial sells
            sell_amount = buy_shares * (o.sell_order.price or 0)
            sell_fees = o.sell_order.fee
            total_sell_value = sell_amount + sell_fees

            gain += total_sell_value - total_buy_value

            # Check if the closed order happened in the current year
            sell_transaction_date = o.sell_order.value_date
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
