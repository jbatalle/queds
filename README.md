# Queds Finance
Queds Finance is a finance portfolio management tool that allows you to track your finance assets, including stock transactions, crypto transactions, and bank statements. It automatically reads data from various brokers abd crypto exchanges, making it easier for you to manage your investments.

## Demo
Check out the demo at http://queds.alwaysdata.net/overview

## Features
* Stock and crypto portfolio tracking
* Wallet tracking with Session/Pre/Post market prices
* Wallet movement tracking with tax basis explanation per transaction
* Tax calculation with FIFO
* Profit/Loss dashboard with realized and unrealized gain tracking
* Watchlist for monitoring assets
* Automatic data import from Degiro, Clicktrade and InteractiveBrokers
* Automatic data import from exchanges: Bitstamp, Kraken, Bittrex, Binance and KuCoin
* TradingView graphs for visualizing asset performance
* CSV import for broker and crypto data

## In progress
* Dividends tracking
* Price alerts via Telegram
* Default portfolio currency setting
* Create a Trading Log with all the movements and relations between orders

## Table of Contents
1. [Getting Started](#getting-started)
2. [Initial steps](#initial-steps)
3. [Development](#development)

## Getting Started
To get started with Queds Finance, you can deploy the tool using docker-compose or install each component individually.

### Docker compose
Deploy everything with docker-compose:
```
docker-compose build --parallel
docker-compose up
```
Check the VUE_APP_BACKEND_URL environment variable in docker-compose.yml. 

The database is created automatically via alembic migrations. To be sure, once everything is ready, apply migrations again.
```
docker-compose run migrate
```

#### Full environment
```
docker-compose -f docker-compose.full.yml build --parallel
docker-compose -f docker-compose.full.yml up
```

## Initial steps
1. Visit http://0.0.0.0:6060
2. Create a user using the Register form
3. Add a broker/exchange account in Accounts view
4. Execute a read over the accounts or upload a CSV to an account
5. Wait few seconds until the read finishes and the wallet is calculated
6. Check orders
7. Check the generated Wallet and the Tax report
8. Add stock to a watchlist

## Development
Queds Finance is built using Python, Vue, Redis, and Timescaledb. Here's an overview of the directory structure:

    .
    ├── app
    │   ├── api/ (flask app)
    │   ├── backend/ (worker) 
    │   ├── config/ (app configs)
    │   └── models/ (database models)
    ├── frontend/ (vue web page)
    ├── docker-compose.full.yml
    ├── docker-compose.yml
    └── nginx_template.conf
    
### Configuration
Edit the configuration file `app/config/local.py` and set the parameters according to your local environment.
```
DEBUG = True

SQL_CONF = {
    'user': 'username',
    'password': 'password',
    'host': 'localhost',
    'port': '5432',
    'database': 'queds_local'
}

REDIS = {
    'host': 'localhost',
    'port': 6379
}
```
    
### Database
Create a database in Postgres(TimescaleDB) and apply migrations:
```
BACKEND_SETTINGS=config.local alembic upgrade head
```

And for create new migrations:
```
BACKEND_SETTINGS=conf.local alembic revision --autogenerate
```

#### With docker-compose
You can modify the database using the docker-compose. After the model modification, you can generate the new migrations with:
```
docker-compose run migrate /bin/bash
cd app/models && alembic revision --autogenerate
```

To downgrade a migration, use:
```
docker-compose run migrate /bin/bash
cd app/models && alembic downgrade -1
```

Or directly with:
```bash
docker-compose -f docker-compose.yml restart migrate
```

### API
To initialize the API, create a virtual environment and run:
```
cd app/api
pip install -r requirements.txt
BACKEND_SETTINGS=config.local python app.py run -h 0.0.0.0
```

Test the API:
```
BACKEND_SETTINGS=config.local python -m unittest
```

Finally, check API endpoints in Swagger: http://0.0.0.0:5000/api

Check out the demo API at https://queds.alwaysdata.net/overview

### Backend
Create a virtual environment and initialize a worker:
```
cd app/backends
pip install -r requirements.txt
BACKEND_SETTINGS=config.local python finance_reader/worker.py
```

Test the backend client with:
```
BACKEND_SETTINGS=config.local python finance_reader/client.py
```

### Frontend
To start the frontend:
```
cd frontend
npm install
npm install @vue/cli -g
npm run serve
```

To build the frontend:
```
npm run-script build
```

### Database management
You can access to the database using the docker-compose.


# Screenshots
Track your assets and monitor your portfolio performance.
![Queds wallet](docs/img/wallet.png)

Check your taxes and dividends.
![Queds taxes](docs/img/taxes.png)

Monitor your assets with the watchlist.
![Queds watchlist](docs/img/watchlist.png)
