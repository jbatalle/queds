import os
from alembic import op
import sqlalchemy as sa
from alembic.runtime.migration import MigrationContext
from alembic.operations import Operations


def list_entities():
    from models.system import User, Entity, EntityCredentialType, Account
    entities = [
        {
            "name": "Degiro", "type": Entity.Type.BROKER, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.USERNAME.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.PASSWORD.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "ClickTrade", "type": Entity.Type.BROKER, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.USERNAME.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.PASSWORD.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "IB", "type": Entity.Type.BROKER, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.USERNAME.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.PASSWORD.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "October", "type": Entity.Type.CROWD, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.USERNAME.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.PASSWORD.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "BBVA", "type": Entity.Type.BANK, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.USERNAME.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.PASSWORD.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "Bitstamp", "type": Entity.Type.EXCHANGE, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.API_KEY.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.API_SECRET.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }, {
                "cred_type": EntityCredentialType.Type.USER_ID.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }]
        }, {
            "name": "Kraken", "type": Entity.Type.EXCHANGE, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.API_KEY.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.API_SECRET.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "Bittrex", "type": Entity.Type.EXCHANGE, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.API_KEY.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.API_SECRET.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        }, {
            "name": "Binance", "type": Entity.Type.EXCHANGE, "active": True,
            "creds": [{
                "cred_type": EntityCredentialType.Type.API_KEY.name,
                "mode": EntityCredentialType.Mode.TEXT.name
            }, {
                "cred_type": EntityCredentialType.Type.API_SECRET.name,
                "mode": EntityCredentialType.Mode.PASSWORD.name
            }]
        },
    ]
    return entities


def insert_entities(entities):
    table = sa.table('entities',
                     sa.column('type', sa.Integer),
                     sa.column('name', sa.String),
                     sa.column('active', sa.Integer)
                     )
    q = op.bulk_insert(table, entities)
    return q


def insert_creds(credentials):
    table = sa.table('entity_credential_types',
    sa.column('entity_id', sa.Integer),
    sa.column('cred_type', sa.String),
    sa.column('mode', sa.String)
    )
    q = op.bulk_insert(table, credentials)
    return q


def upgrade_fixtures():
    conn = op.get_bind()
    query = conn.execute("select id, name from entities")
    db_entities = query.fetchall()
    db_entities_names = {d.name: {"id": d.id, "name": d.name} for d in db_entities}

    query = conn.execute("select entity_id, cred_type, mode from entity_credential_types")
    db_creds = query.fetchall()
    db_creds_entity = [{"entity_id": d.entity_id, "cred_type": d.cred_type, "mode": d.mode} for d in db_creds]

    to_insert = []
    cred_to_insert = []
    entities = list_entities()
    for entity in entities:
        if entity['name'] not in db_entities_names:
            to_insert.append(entity)
            continue
        # check creds
        db_entity = db_entities_names[entity['name']]
        db_entity_creds = {f['cred_type']: f for f in db_creds_entity if f['entity_id'] == db_entity['id']}
        for c in entity['creds']:
            if c['cred_type'] in db_entity_creds:
                continue
            # to insert
            c['entity_id'] = db_entity['id']
            cred_to_insert.append(c)

    # insert_entities(to_insert)
    insert_creds(cred_to_insert)

    print("Check creds")


def upgrade():
    entities = [{"name": "Degiro", "type": Entity.Type.BROKER, "active": True},
                {"name": "ClickTrade", "type": Entity.Type.BROKER, "active": True},
                {"name": "IB", "type": Entity.Type.BROKER, "active": True},
                {"name": "October", "type": Entity.Type.CROWD, "active": True},
                {"name": "BBVA", "type": Entity.Type.BANK, "active": True},
                {"name": "Bitstamp", "type": Entity.Type.EXCHANGE, "active": True},
                {"name": "Kraken", "type": Entity.Type.EXCHANGE, "active": True},
                {"name": "Bittrex", "type": Entity.Type.EXCHANGE, "active": True},
                {"name": "Binance", "type": Entity.Type.EXCHANGE, "active": True}]

    print("Creating entities")
    table = sa.table('entities',
                     sa.column('type', sa.Integer),
                     sa.column('name', sa.String),
                     sa.column('active', sa.Integer)
                     )
    op.bulk_insert(table, entities)

    # credential types
    from models.system import Entity, EntityCredentialType, Account

    print("Insert credential types")
    conn = op.get_bind()
    query = conn.execute("select id from entities where name = 'Degiro'")
    degiro_entity = query.fetchone()[0]
    query = conn.execute("select id from entities where name = 'ClickTrade'")
    clicktrade_entity = query.fetchone()[0]
    query = conn.execute("select id from entities where name = 'Bitstamp'")
    bitstamp_entity = query.fetchone()[0]
    query = conn.execute("select id from entities where name = 'Kraken'")
    kraken_entity = query.fetchone()[0]
    query = conn.execute("select id from entities where name = 'Bittrex'")
    bittrex_entity = query.fetchone()[0]
    query = conn.execute("select id from entities where name = 'Binance'")
    binance_entity = query.fetchone()[0]
    bulk_insert = [{
        "entity_id": degiro_entity,
        "cred_type": EntityCredentialType.Type.USERNAME.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": degiro_entity,
        "cred_type": EntityCredentialType.Type.PASSWORD.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }, {
        "entity_id": clicktrade_entity,
        "cred_type": EntityCredentialType.Type.USERNAME.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": clicktrade_entity,
        "cred_type": EntityCredentialType.Type.PASSWORD.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }, {
        "entity_id": bitstamp_entity,
        "cred_type": EntityCredentialType.Type.API_KEY.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": bitstamp_entity,
        "cred_type": EntityCredentialType.Type.API_SECRET.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }, {
        "entity_id": bitstamp_entity,
        "cred_type": EntityCredentialType.Type.USER_ID.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": kraken_entity,
        "cred_type": EntityCredentialType.Type.API_KEY.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": kraken_entity,
        "cred_type": EntityCredentialType.Type.API_SECRET.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }, {
        "entity_id": bittrex_entity,
        "cred_type": EntityCredentialType.Type.API_KEY.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": bittrex_entity,
        "cred_type": EntityCredentialType.Type.API_SECRET.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }, {
        "entity_id": binance_entity,
        "cred_type": EntityCredentialType.Type.API_KEY.name,
        "mode": EntityCredentialType.Mode.TEXT.name
    }, {
        "entity_id": binance_entity,
        "cred_type": EntityCredentialType.Type.API_SECRET.name,
        "mode": EntityCredentialType.Mode.PASSWORD.name
    }]
    table = sa.table('entity_credential_types',
                     sa.column('entity_id', sa.Integer),
                     sa.column('cred_type', sa.String),
                     sa.column('mode', sa.String)
                     )
    op.bulk_insert(table, bulk_insert)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    conn.execute(sa.text("""truncate entities cascade;"""))
    # ### end Alembic commands ###


if __name__ == '__main__':
    from models import sql
    from config import Settings

    settings_module = os.environ.get("BACKEND_SETTINGS", None) or None
    settings = Settings(settings_module)
    engine = sql.create_db_connection(settings.SQL_CONF)
    conn = engine.connect()
    ctx = MigrationContext.configure(conn)
    op = Operations(ctx)

    upgrade_fixtures()
    print("Done")
