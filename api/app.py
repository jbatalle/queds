import sys
import os
import time
import logging.config
import sqlalchemy
from flask import Flask, Blueprint
from flask_restx import Api
from flask_jwt_extended import JWTManager
from flask_jwt_extended.exceptions import JWTExtendedException
from jwt.exceptions import ExpiredSignatureError
from flask_sqlalchemy import SQLAlchemy

# import config and models from main path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')))

try:
    with open("../VERSION") as f:
        VERSION = f.read()
except:
    with open("VERSION") as f:
        VERSION = f.read()

from config import settings
from models.sql import create_db_connection

db = SQLAlchemy()

app = Flask(__name__, static_folder="dist" if settings.DEMO_MODE else None)

# Load the file specified by the APP_CONFIG_FILE environment variable
# Variables defined here will override those in the default configuration
app.config['SQLALCHEMY_POOL_RECYCLE'] = 280
app.config['SQLALCHEMY_POOL_TIMEOUT'] = 20
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True

app.config['JWT_SECRET_KEY'] = settings.JWT_SECRET_KEY

jwt = JWTManager(app)

log = logging.getLogger(__name__)
authorizations = {
    'apikey': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': "Type in the *'Value'* input box below: **'Bearer &lt;JWT&gt;'**, where JWT is the token"
    }
}

rest_api = Api(version="1.0", title="Queds API", authorizations=authorizations, security='apikey')


def configure_app(flask_app):
    create_db_connection(settings.SQL_CONF)

    # for tests
    conn_string = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(settings.SQL_CONF['user'],
                                                            settings.SQL_CONF['password'],
                                                            settings.SQL_CONF['host'],
                                                            settings.SQL_CONF['port'],
                                                            settings.SQL_CONF['database'])
    app.config['SQLALCHEMY_DATABASE_URI'] = conn_string
    db.init_app(flask_app)


@rest_api.errorhandler(JWTExtendedException)
def handle_jwt_exceptions(error):
    return {'message': str(error)}, getattr(error, 'code', 401)


@rest_api.errorhandler(ExpiredSignatureError)
def handle_jwt_exceptions(error):
    return {'message': str(error)}, getattr(error, 'code', 401)


@rest_api.errorhandler(sqlalchemy.orm.exc.NoResultFound)
def handle_no_result_exception(error):
    """Return a custom not found error message and 404 status code"""
    return {'message': 'Not Found'}, 404


def initialize_app(flask_app):
    configure_app(flask_app)
    from api.users.views import namespace as api_users
    from api.accounts.views import namespace as api_accounts
    from api.stock.views import namespace as api_stock
    from api.crypto.views import namespace as api_exchange
    from api.analysis.views import namespace as api_analysis

    blueprint = Blueprint('api', __name__, url_prefix='/api')

    @app.route("/api/version")
    def version():
        return VERSION

    if settings.DEMO_MODE:
        log.info("Setting DEMO MODE!")

        @app.route("/overview")
        def index():
            return app.send_static_file("index.html")

        @app.route('/*')
        @app.route('/<path:path>')
        def paths(path):
            return app.send_static_file(path)

    rest_api.init_app(blueprint)

    rest_api.add_namespace(api_users)
    rest_api.add_namespace(api_stock)
    rest_api.add_namespace(api_exchange)
    rest_api.add_namespace(api_accounts)
    rest_api.add_namespace(api_analysis)

    flask_app.register_blueprint(blueprint)


def main():
    try:
        initialize_app(app)
        log.info('>>>>> Starting development server at http://{}/api/ <<<<<'.format(app.config['SERVER_NAME']))
        log.info(f"Demo mode: {settings.DEMO_MODE}. Debug mode: {settings.DEBUG} - Port: {os.getenv('PORT') or 5000}")
        app.run(host='0.0.0.0', port=os.getenv("PORT") or 5000, debug=settings.DEBUG)
    except Exception as e:
        log.exception(e)
        time.sleep(2)
        main()


if __name__ == "__main__":
    main()
