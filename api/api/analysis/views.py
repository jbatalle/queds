import logging
from flask_restx import Resource, Namespace
from models.system import Account, Entity, User, EntityCredentialType, AccountCredentialParam
from models.broker import Watchlist, Watchlists, Wallet, Ticker
from flask import request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from services.yahoo import YahooClient
from services.zinc import ZincClient
from api import filter_by_username

log = logging.getLogger(__name__)


namespace = Namespace("analysis")


@namespace.route('/watchlist')
class WatchlistList(Resource):

    @jwt_required()
    def get(self):
        """Returns all watchlists."""
        watchlists = filter_by_username(Watchlists).all()
        items = []
        for item in watchlists:
            items.append(item.json)
        return jsonify(items)

    @jwt_required()
    def post(self):
        current_user_email = get_jwt_identity()
        user_id = User.find_by_email(current_user_email).id
        post_data = request.get_json()
        w = Watchlists()
        w.name = post_data.get('name')
        w.user_id = user_id
        w.save()

        return w.json, 201


@namespace.route('/watchlist/<int:id>')
class WatchlistItems(Resource):

    @jwt_required()
    def get(self, id):
        """Returns a watchlist."""
        username = get_jwt_identity()
        user_id = User.find_by_email(username).id
        if id == 0:
            # get wallet items
            items = Wallet.query.filter(Wallet.user_id==user_id).all()
            tickers = Ticker.query.filter(Ticker.id.in_([w.ticker_id for w in items])).all()
        else:
            watchlist = Watchlist.query.filter_by(watchlists=int(id)).all()
            tickers = Ticker.query.filter(Ticker.id.in_([w.ticker for w in watchlist])).all()

        y = YahooClient()
        # to be moved outside
        to_be_req = [t for t in tickers if not t.ticker_yahoo]
        log.info(f"Tickers without yahoo: {to_be_req}")
        for no_yahoo_symbol in to_be_req:
            yahoo_symbol = y.get_yahoo_symbol(no_yahoo_symbol.ticker)
            log.info(f"{no_yahoo_symbol.ticker} - {yahoo_symbol}")
            no_yahoo_symbol.ticker_yahoo = yahoo_symbol
            q = no_yahoo_symbol.save()
            log.info(q)

        tickers = {t.ticker_yahoo: t for t in tickers}
        symbols = ",".join(list(tickers.keys()))
        log.info(f"Symbols: {symbols}")
        if not symbols:
            return [], 200
        r = y.get_current_tickers(symbols)

        # TODO: include ticker id here
        [q.update({'id': tickers[q['symbol']].id}) for q in r]

        return r, 200

    @jwt_required()
    def post(self, id):
        log.info(f"Saving ticker to watchlist {id}")
        post_data = request.get_json()
        symbol = post_data.get('ticker')
        ticker = Ticker.query.filter(Ticker.ticker == symbol).first()
        if not ticker:
            # get yahoo ticker!

            y = YahooClient()
            yahoo_symbol = y.get_yahoo_symbol(symbol)
            if not yahoo_symbol:
                return 404
            ticker = Ticker(ticker=symbol,
                            name="",
                            currency="",
                            isin="",
                            ticker_yahoo=yahoo_symbol)
            ticker.save()
        w = Watchlist()
        w.ticker = ticker.id
        w.watchlists = id
        w.save()

        return w.json, 201

    @jwt_required()
    def delete(self, id):
        """Deletes a watchlist and the items."""

        watchlist = Watchlists.query.filter(Watchlists.id == id).one()
        Watchlist.query.filter(Watchlist.watchlists == watchlist.id).delete()

        watchlist.destroy()

        return {'message': 'Watchlist deleted!'}


@namespace.route('/watchlist/<int:watchlist_id>/<int:id>')
class WatchlistItems(Resource):

    @jwt_required()
    def delete(self, watchlist_id, id):
        log.info(f"Deleting ticker {id} from watchlist {watchlist_id}")

        Watchlist.query.filter(Watchlist.watchlists == watchlist_id, Watchlist.ticker == id).delete()
        return {'message': 'Ticker deleted!'}


@namespace.route('/comments')
class CommentsList(Resource):

    @jwt_required()
    def get(self):
        zinc_client = ZincClient("oracle", "admin", "Complexpass#123")

        comments = zinc_client.get_last_items()
        comments = [
            {
                "date": c['_source']['date'],
                "message": c['_source']['message'],
                "source": c['_type'],
                "tickers": ', '.join(c['_source']['ticker'])
             } for c in comments]

        return comments, 200


@namespace.route('/comments/<string:symbol>')
class CommentsList(Resource):

    @jwt_required()
    def get(self, symbol):
        # TODO: should receive ID in order to avoid problems
        # ticker = Ticker.query.filter(Ticker.ticker == symbol).first()
        zinc_client = ZincClient("oracle", "admin", "Complexpass#123")

        comments = zinc_client.search_by_ticker(symbol)
        comments = [{"date": c['_source']['date'], "message": c['_source']['message'], "source": c['_type']} for c in comments]

        return comments, 200
