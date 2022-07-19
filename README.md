# Queds Finance
Finance portfolio for manage all your finance assets: stock transactions, crypto transactions, bank statements... It reads the data automatically from the Brokers, Crypto Exchanges and Banks.

## Demo
https://queds-api.herokuapp.com/overview

## Features
* Wallet tracking with Session/Pre/Post market prices
* Tax calculation
* Watchlist stock
* Automatic read from Degiro, Clicktrade and InteractiveBrokers
* Automatic read from exchanges: Bitstamp, Kraken, Bittrex and Binance

## In progress
* Include dividends
* Allow to import broker/crypto data from CSV
* Profile view -> Change default portfolio currency
* Include crowdlending platform: October
* Include investment funds

## Table of Contents
1. [Getting Started](#getting-started)
2. [Initial steps](#initial-steps)
3. [Development](#development)

## Getting Started
You can deploy using docker-compose or installing each component.

### Docker compose
Deploy everything with docker-compose (including external services: redis + nginx + postgresql):
```
docker-compose build --parallel
docker-compose up
```
Check the VUE_APP_BACKEND_URL environment variable in docker-compose.yml. 

The database is created automatically via alembic migrations. To be sure, once everything is ready, apply migrations again.
```
docker-compose run migrate
```

## Initial steps
1. Visit http://0.0.0.0:6060
2. Create a user using the Register form
3. Add a broker/exchange account in Accounts view
4. Execute a read over the accounts
5. Check orders
6. Execute wallet calculation in order to generate the Wallet and the Tax report
7. Add stock to a watchlist

## Development

### Structure
    .
    ├── api/
    ├── backend/ (worker) 
    ├── config/ (app configs)
    ├── frontend/ (vue web page)
    ├── models/ (DB models) 
    └── docker-compose.yml
    
### Configuration
Edit the configuration file `config/local.py` and set the parameters according to your local environment.
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
Create a database in Postgres and apply migrations:
```
BACKEND_SETTINGS=config.local alembic upgrade head
```

Create new migrations:
```
BACKEND_SETTINGS=conf.local alembic revision --autogenerate
```

#### With docker-compose
You can modify the database using the docker-compose. After the model modification, you can generate the new migrations with:
```
docker-compose run migrate /bin/bash
cd models && alembic revision --autogenerate
```

Downgrade migration:
```
docker-compose run migrate /bin/bash
cd models && alembic downgrade -1
```

### API
Create a virtual environment and initialize the API:
```
cd api
pip install -r requirements.txt
BACKEND_SETTINGS=config.local python app.py run -h 0.0.0.0
```

Test the API:
```
BACKEND_SETTINGS=config.local python -m unittest
```

Finally, check API endpoints in Swagger: http://0.0.0.0:5000/api

### Backend
Create a virtual environment and initialize a worker:
```
cd backends
pip install -r requirements.txt
BACKEND_SETTINGS=config.local python finance_reader/worker.py
```

Init test client:
```
BACKEND_SETTINGS=config.local python finance_reader/client.py
```

### Frontend
Init frontend:
```
cd frontend
npm install
npm install @vue/cli -g
npm run serve
```

Build:
```
npm run-script build
```
