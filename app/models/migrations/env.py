from __future__ import with_statement
import sys
import logging
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic.script import ScriptDirectory

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# add your model's MetaData object here
# for 'autogenerate' support
from os.path import abspath, dirname, join
PROJ_DIR = abspath(join(dirname(abspath(__file__)), '../..'))
sys.path.insert(0, PROJ_DIR)

from config import settings

sql_conf = settings.SQL_CONF
if sql_conf['db_type'] == 'postgresql':
    connection_string = f'postgresql://{sql_conf["user"]}:{sql_conf["password"]}@{sql_conf["host"]}:{sql_conf["port"]}/{sql_conf["database"]}'
else:
    connection_string = f'sqlite:///{sql_conf["database"]}'

from models import sql
from models.broker import *
from models.crypto import *
target_metadata = sql.Base.metadata


def run_migrations_offline():
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = connection_string
    context.configure(
        url=url, target_metadata=target_metadata, literal_binds=True
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """

    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = connection_string

    # this callback is used to prevent an auto-migration from being generated
    # when there are no changes to the schema
    # reference: http://alembic.zzzcomputing.com/en/latest/cookbook.html
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')
                return

        # extract Migration
        migration_script = directives[0]
        # extract current head revision
        head_revision = ScriptDirectory.from_config(context.config).get_current_head()

        if head_revision is None:
            # edge case with first migration
            new_rev_id = 1
        else:
            # default branch with incrementation
            last_rev_id = int(head_revision.lstrip('0'))
            new_rev_id = last_rev_id + 1
        # fill zeros up to 4 digits: 1 -> 0001
        migration_script.rev_id = '{0:04}'.format(new_rev_id)


    connectable = engine_from_config(
        configuration,
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            process_revision_directives=process_revision_directives
            # **current_app.extensions['migrate'].configure_args
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
