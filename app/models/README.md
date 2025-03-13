README.md

## Requirements
sudo apt-get install python-psycopg2

## Generate revision
alembic revision --autogenerate

## Apply migration
alembic -c local.ini upgrade head

## Downgrade migration
alembic -c local.ini downgrade -1

## Use fixtures
Use fixtures file in order to fill the database with basic information

## Problems
- In case of delete all the database, some types should be removed:
```
DROP TYPE "mode";
DROP TYPE "cred_type";
```