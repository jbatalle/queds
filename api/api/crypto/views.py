import logging
from flask import request, jsonify
from flask_restx import Resource, Namespace
from models.crypto import ExchangeWallet, ExchangeOrder, ExchangeClosedOrder
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
        result = Entity.query.filter(Entity.type==Entity.Type.EXCHANGE)
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


@namespace.route('/wallet')
class BalanceList(Resource):

    @jwt_required()
    def get(self):
        """Returns all open_orders."""
        username = get_jwt_identity()
        user_id = User.find_by_email(username).id

        # TODO: get open orders
        wallet_items = ExchangeWallet.query.options(joinedload('open_orders'))\
             .options(joinedload('open_orders.order')).filter(ExchangeWallet.user_id == user_id).all()

        # wallet_items = ExchangeWallet.query.filter(ExchangeWallet.user_id == user_id).all()
        if len(wallet_items) == 0:
            return {'message': "Unable to detect tickers in open transactions. Recalculate the wallet!"}, 400

        c = CryptoCompareClient()
        currencies = [p.currency for p in wallet_items]
        prices_eur = c.get_price("EUR", ','.join(currencies))
        prices_usd = c.get_price("USD", ','.join(currencies))
        prices_btc = c.get_price("BTC", ','.join(currencies))

        items = []
        for r in wallet_items:
            item = r.json
            if r.currency == 'EUR':
                continue
            if r.currency in prices_eur:
                item['current_price'] = 1/prices_eur[r.currency]
                item['current_price_eur'] = item['current_price']
                item['current_price_currency'] = 'eur'
            elif r.currency in prices_usd:
                item['current_price'] = 1/prices_usd[r.currency]
                item['current_price_eur'] = item['current_price'] * prices_eur['USD']
                item['current_price_currency'] = 'usd'
            elif r.currency in prices_btc:
                item['current_price'] = 1/prices_btc[r.currency]
                item['current_price_eur'] = item['current_price'] * prices_eur['BTC']
                item['current_price_currency'] = 'btc'
            else:
                log.error(f"Unable to get prices of {r.currency}")

            item['current_value'] = item['amount'] * item['current_price']
            item['current_benefit'] = item['current_value'] - item['cost'] #+ r.benefits + r.fees
            item['open_orders'] = []

            for oo in r.open_orders:
                oo_item = oo.json
                oo_item['order'] = oo.order.json
                item['open_orders'].append(oo_item)


            # item['market'] = {}
            # if r.ticker.ticker in tickers_by_ticker:
                # item['market'] = tickers_by_ticker[r.ticker.ticker]
            # item['transaction'] = r.transaction.json
            items.append(item)
        return jsonify(items)


@namespace.route('/orders')
class OrdersCollection(Resource):

    @jwt_required()
    def get(self):
        args = request.args
        pagination = args.to_dict()
        exchange_names = args.get('exchange', None)
        username = get_jwt_identity()
        user_id = User.find_by_email(username).id

        accounts = Account.query.filter(Account.user_id == user_id, Account.entity.has(type=Entity.Type.EXCHANGE))

        if exchange_names:
            exchange_list = exchange_names.split(",")
            accounts = accounts.filter(Account.name.in_(exchange_list))
        accounts = accounts.all()

        query = ExchangeOrder.query.filter(ExchangeOrder.account_id.in_([a.id for a in accounts])).order_by(
            ExchangeOrder.value_date.desc())

        limit = int(pagination['limit'])
        page = int(pagination['page']) - 1
        orders = query.limit(limit).offset(page * limit).all()

        items = []
        for order in orders:
            o = order.to_dict()
            o['currency_source'] = order.pair.split("/")[0]
            o['currency_target'] = order.pair.split("/")[1]
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


@namespace.route('/calculate')
class Calculate(Resource):

    @demo_check
    @jwt_required()
    def get(self):
        current_user_email = get_jwt_identity()
        user_id = User.find_by_email(current_user_email).id
        data = {
            "user_id": user_id,
            "mode": "crypto"
        }
        queue_process(data)


@namespace.route('/tax')
class CryptoTax(Resource):

    @jwt_required()
    def get(self):
        """Returns all closed orders."""
        args = request.args.to_dict()

        year = int(args.get('year', 2021))
        username = get_jwt_identity()
        user_id = User.find_by_email(username).id
        accounts = Account.query.with_entities(Account.id).filter(Account.user_id == user_id,
                                                                  Account.entity.has(type=Entity.Type.EXCHANGE)).all()

        closed_orders = ExchangeClosedOrder.query.options(joinedload('sell_order'))\
            .options(joinedload('buy_order')).options(joinedload('buy_order.order'))\
            .join(ExchangeClosedOrder.sell_order) \
            .filter(ExchangeOrder.value_date >= f"{year}-01-01") \
            .filter(ExchangeOrder.value_date < f"{year + 1}-01-01") \
            .filter(ExchangeOrder.account_id.in_([a_id for a_id in accounts])).all()

        items = []
        for r in closed_orders:
            item = r.sell_order.json
            children = []
            for q in r.buy_order:
                buy = q.order.json
                buy['amount'] = q.amount
                buy['partial_fee'] = q.partial_fee
                children.append(buy)

            item['children'] = children
            items.append(item)
        return jsonify(items)
