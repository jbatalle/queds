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

    options = {'pool_size': 15}
    return do_create_engine(SQL_CONF['db_type'], SQL_CONF['user'], SQL_CONF['password'], SQL_CONF['host'], SQL_CONF['port'],
                            SQL_CONF['database'], options)


def do_create_engine(db_type, user, password, host, port, database, options={}):
    global mysql_engine, db_session, Base

    if db_type == 'postgresql':
        conn_string = f'postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}'
    elif db_type == 'sqlite':
        conn_string = f'sqlite:///{database}'
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

    mysql_engine = create_engine(conn_string, pool_pre_ping=True, pool_timeout=20, pool_recycle=299, echo=False, isolation_level='AUTOCOMMIT', **options)
    db_session = scoped_session(sessionmaker(bind=mysql_engine))  # type: Session
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
        #db_session.commit()

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
            elif hasattr(v, 'json'):# and callable(v.json):
                d[k] = v.json
            else:
                d[k] = v
        return d

    def to_dict(self):
        a = {field.name: getattr(self, field.name) for field in self.__table__.c}
        return {field.name: getattr(self, field.name) for field in self.__table__.columns}

    @property
    def dto(self):
        dto_dict = {field.name: getattr(self, field.name) for field in self.__table__.c}
        options = self.query._with_options

        for relationship in self.__mapper__.relationships:
            rel_name = relationship.key
            rel_value = getattr(self, rel_name)

            if rel_name in self.__mapper__.relationships.keys():
                if rel_value is not None:
                    if isinstance(rel_value, list):
                        dto_dict[rel_name] = [item.dto for item in rel_value]
                    else:
                        dto_dict[rel_name] = rel_value.dto

        return type(
            f"{self.__class__.__name__}DTO",
            (object,),
            dto_dict
        )

    @classmethod
    def get_type(cls, type):
        return {v: n for n, v in vars(cls.Type).items() if n.isupper()}[type]
