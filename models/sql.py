from sqlalchemy import create_engine, sql
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
import datetime

mysql_engine = None
db_session = None
Base = declarative_base()
settings = None


def create_db_connection(SQL_CONF):
    global settings

    options = {'pool_pre_ping': True}
    return do_create_engine(SQL_CONF['user'], SQL_CONF['password'], SQL_CONF['host'], SQL_CONF['port'],
                     SQL_CONF['database'], options)


def do_create_engine(user, password, host, port, database, options={}):
    global mysql_engine, db_session, Base

    conn_string = 'postgresql://{0}:{1}@{2}:{3}/{4}'.format(user, password, host, port, database)
    mysql_engine = create_engine(conn_string, pool_pre_ping=True, pool_timeout=20, pool_recycle=299)
    db_session = scoped_session(sessionmaker(bind=mysql_engine, autocommit=True))  # type: Session
    Base = declarative_base(bind=mysql_engine)
    Base.query = db_session.query_property()
    return mysql_engine


class CRUD:

    def __init__(self):
        pass

    def save(self):
        if self.id == None:
            db_session.add(self)
        else:
            db_session.merge(self)

        try:
            db_session.flush()
        except Exception as e:
            db_session.rollback()
            raise e

    def update_on_conflict(self, statement):
        db_session.execute(statement)

    def destroy(self):
        db_session.delete(self)
        try:
            return db_session.flush()
        except Exception as e:
            db_session.rollback()
            raise e

    @property
    def json(inst):
        """
        Jsonify the sql alchemy query result.
        """

        instance = inst.__dict__.copy()
        instance.pop('_sa_instance_state', None)

        d = dict()
        for k, v in instance.items():
            if v is None:
                d[k] = str()
            elif isinstance(v, sql.sqltypes.Date):
                d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            elif isinstance(v, datetime.date):
                d[k] = v.strftime("%Y-%m-%d %H:%M:%S")
            else:
                d[k] = v
        return d
