
import logging
from datetime import datetime
from typing import Any, Dict, List
from flask import request, jsonify
from flask_restx import Resource, Namespace
from models.crypto import (
    ExchangeWallet, ExchangeClosedOrder, ExchangeOpenOrder, ExchangeProxyOrder, CryptoEvent
)
from models.system import Account, Entity, User, EntityCredentialType
from flask_jwt_extended import jwt_required, get_jwt_identity
from api import filter_by_username, demo_check
from services.queue import queue_process
from services.cryptocompare import CryptoCompareClient
from sqlalchemy.orm import joinedload

log = logging.getLogger(__name__)
namespace = Namespace("crypto")


def paginate_query(query, pagination: Dict[str, Any]) -> List[Any]:
    limit = int(pagination.get('limit', 10))
    page = int(pagination.get('page', 1)) - 1
    return query.limit(limit).offset(page * limit).all(), limit, page

def map_currency_names(prices: Dict[str, Any]) -> Dict[str, Any]:
    return {key.replace("MIOTA", "IOTA").replace("BTT", "BTTC"): value for key, value in prices.items()}



@namespace.route('/exchanges')
class List(Resource):
    def get(self):
        """Returns all exchange."""
        result = Entity.query.filter(Entity.type == Entity.Type.EXCHANGE)
        items = [r.json for r in result]
        return jsonify(items)



@namespace.route('/accounts')
class AccountList(Resource):
    @jwt_required()
    def get(self):
        """Returns all exchange accounts."""
        result = filter_by_username(Account).filter(Entity.type == Entity.Type.EXCHANGE)
        items = [r.json for r in result]
        return jsonify(items)



@namespace.route('/wallet/assets')
class BalanceList(Resource):
    @jwt_required()
    def get(self):
        """Returns wallet assets without price info."""
        user_id = get_jwt_identity()
        wallet_items = (
            ExchangeWallet.query
            .options(joinedload(ExchangeWallet.open_orders).joinedload(ExchangeOpenOrder.exchange))
            .options(joinedload(ExchangeWallet.open_orders).joinedload(ExchangeOpenOrder.order).joinedload(CryptoEvent.account))
            .filter(ExchangeWallet.user_id == user_id).all()
        )
        if not wallet_items:
            return jsonify([])
        assets = [
            {**r.json, 'open_orders': [oo.json for oo in r.open_orders]}
            for r in wallet_items
        ]
        return jsonify(assets)


@namespace.route('/wallet/prices')
class WalletPrices(Resource):
    @jwt_required()
    def post(self):
        """Returns price info for given currencies."""
        data = request.get_json()
        currencies = data.get('currencies', [])
        if not currencies:
            return jsonify([])
        c = CryptoCompareClient()
        prices_eur = map_currency_names(c.get_prices("EUR", currencies))
        changes_24h = c.get_changes("EUR", currencies)
        # If you want to populate USD/BTC, do it here
        prices_usd, prices_btc = {}, {}
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
        accounts_query = Account.query.filter(Account.user_id == user_id, Account.entity.has(type=Entity.Type.EXCHANGE))
        if exchange_names:
            exchange_list = exchange_names.split(",")
            accounts_query = accounts_query.filter(Account.name.in_(exchange_list))
        accounts = accounts_query.all()
        query = CryptoEvent.query.filter(CryptoEvent.account_id.in_([a.id for a in accounts])).order_by(CryptoEvent.value_date.desc())
        if search:
            # query = query.filter(or_(Ticker.ticker.ilike(f"%{search}%"), Ticker.name.ilike(f"%{search}%"), Ticker.isin.ilike(f"%{search}%")))
            query = query.filter(CryptoEvent.symbol.ilike(f"%{search}%"))
        orders, limit, page = paginate_query(query, pagination)
        def order_to_dict(order):
            o = order.to_dict()
            if order.type in [CryptoEvent.Type.BUY, CryptoEvent.Type.SELL]:
                o['currency_source'], o['currency_target'] = order.symbol.split("/")
            elif order.type == CryptoEvent.Type.DEPOSIT:
                o['currency_source'], o['currency_target'] = order.symbol, ""
            elif order.type == CryptoEvent.Type.WITHDRAWAL:
                o['currency_source'], o['currency_target'] = "", order.symbol
            return o
        items = [order_to_dict(order) for order in orders]
        total = query.count()
        results = {
            "results": items,
            "pagination": {
                "count": total,
                "page": page,
                "per_page": limit,
                "pages": int(total / limit) if limit else 0,
            },
        }
        return jsonify(results)



@namespace.route('/tax')
class CryptoTax(Resource):
    @jwt_required()
    def get(self):
        """Returns all closed orders."""
        args = request.args.to_dict()
        year = int(args.get('year', datetime.now().year - 1))
        user_id = get_jwt_identity()
        accounts = Account.query.with_entities(Account.id).filter(
            Account.user_id == user_id,
            Account.entity.has(type=Entity.Type.EXCHANGE)
        ).all()
        closed_orders = (
            ExchangeClosedOrder.query.options(joinedload(ExchangeClosedOrder.sell_order))
            .options(joinedload(ExchangeClosedOrder.buy_order).joinedload(ExchangeProxyOrder.order))
            .join(ExchangeClosedOrder.sell_order)
            .filter(CryptoEvent.value_date >= f"{year}-01-01")
            .filter(CryptoEvent.value_date < f"{year + 1}-01-01")
            .filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).all()
        )
        def closed_order_to_dict(r):
            item = r.sell_order.json
            item['children'] = [
                {**q.order.json, 'amount': q.amount, 'price': q.user_price, 'partial_fee': q.partial_fee}
                for q in r.buy_order
            ]
            return item
        items = [closed_order_to_dict(r) for r in closed_orders]
        return jsonify(items)



@namespace.route('/calculate')
class Calculate(Resource):
    @demo_check
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        data = {"user_id": user_id, "mode": "crypto"}
        queue_process(data)



@namespace.route('/stats')
class CalcStats(Resource):
    @jwt_required()
    def get(self):
        """
        Returns portfolio value, total buy amount, total sell amount and the gain of the closed orders.
        """
        user_id = get_jwt_identity()
        accounts = Account.query.with_entities(Account.id).filter(
            Account.user_id == user_id,
            Account.entity.has(type=Entity.Type.EXCHANGE)
        ).all()
        query = CryptoEvent.query.filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).order_by(CryptoEvent.value_date.desc())
        orders = query.with_entities(CryptoEvent.type, CryptoEvent.amount, CryptoEvent.price, CryptoEvent.fee, CryptoEvent.event_type).all()
        buy = sum(o.amount * o.price - o.fee for o in orders if o[0] == CryptoEvent.Type.BUY and o.event_type != 'exchange_transaction')
        sell = sum(-(o.amount * o.price + o.fee) for o in orders if o[0] == CryptoEvent.Type.SELL and o.event_type != 'exchange_transaction')
        closed_orders = (
            ExchangeClosedOrder.query.options(joinedload(ExchangeClosedOrder.sell_order))
            .options(joinedload(ExchangeClosedOrder.buy_order).joinedload(ExchangeProxyOrder.order))
            .join(ExchangeClosedOrder.sell_order)
            .filter(CryptoEvent.account_id.in_([a_id[0] for a_id in accounts])).all()
        )
        current_year = datetime.now().year
        gain, current_year_gain = 0, 0
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
            if o.sell_order.value_date.year == current_year:
                current_year_gain += total_sell_value - total_buy_value
        stats = {
            "portfolio_value": 0,
            "buy": buy,
            "sell": sell,
            "gain": gain,
            "current_year_gain": current_year_gain
        }
        return jsonify(stats)
