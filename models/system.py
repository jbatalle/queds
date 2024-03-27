# -*- coding: utf-8 -*-
import bcrypt
from datetime import datetime
from models.sql import Base, CRUD, db_session
from enum import unique, Enum as pEnum
from sqlalchemy import Enum, Column, Integer, String, func, UniqueConstraint, ForeignKey, Boolean, Float, DateTime, \
    Unicode
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import relationship


class User(Base, CRUD):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    registered_on = Column(DateTime, nullable=False)
    admin = Column(Boolean, nullable=False, default=False)
    currency = Column(String(5), default=False)
    # telegram_chat = Column(String(30), default=False)
    # telegram_token = Column(String(60), default=False)

    def __init__(self, email, password, admin=False, currency="EUR"):
        self.email = email
        self.password = generate_password_hash(password)
        self.registered_on = datetime.now()
        self.admin = admin
        self.currency = currency

    @classmethod
    def find_by_email(cls, email):
        return cls.query.filter_by(email=email).first()

    def authenticate(self, password):
        try:
            return bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        except:
            return False

    def get_id(self):
        return self.id

    def __repr__(self):
        return '<User {0}>'.format(self.email)

    def save_to_db(self):
        db_session.add(self)
        db_session.commit()
        db_session.flush()

    @classmethod
    def get_by_email(cls, email):
        return db_session.query(cls).filter_by(email=email).first()

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)


class Entity(Base, CRUD):
    __tablename__ = 'entities'

    class Type:
        BANK = 0
        BROKER = 1
        CROWD = 2
        EXCHANGE = 3

    class Status:
        ACTIVE = 0
        INACTIVE = 1

    id = Column(Integer, primary_key=True)
    name = Column(String(20), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    type = Column(Integer)

    def __str__(self):
        return self.name

    @classmethod
    def get(cls, entity_id):
        return db_session.query(cls).filter(cls.id == entity_id).one_or_none()


class EntityCredentialType(Base, CRUD):
    __tablename__ = 'entity_credential_types'

    @unique
    class Type(pEnum):
        API_KEY = 'api_key'
        API_SECRET = 'api_secret'
        USERNAME = 'username'
        USER_ID = 'user_id'
        PASSWORD = 'password'

    @unique
    class Mode(pEnum):
        TEXT = 'text'
        PASSWORD = 'password'
        OPTION = 'option'

    mode_choices = list(Mode.__members__.keys())
    type_choices = list(Type.__members__.keys())

    def __init__(self, entity_id, mode, cred_type):
        self.entity_id = entity_id
        self.mode = mode
        self.cred_type = cred_type

    id = Column(Integer, primary_key=True)
    entity_id = Column(Integer, ForeignKey('entities.id'))
    entity = relationship("Entity")
    mode = Column(Enum(*mode_choices, name='mode'), nullable=False)
    cred_type = Column(Enum(*type_choices, name='cred_type'), nullable=False)
    __table_args__ = (UniqueConstraint('entity_id', 'mode', 'cred_type', name='_mode_cred_type_uc'),)


class Account(Base, CRUD):
    __tablename__ = 'accounts'
    __table_args__ = (UniqueConstraint('name', 'user_id', name='_name_user_id_unique'),)

    id = Column(Integer, primary_key=True)
    updated_on = Column(DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)
    name = Column(String(20))
    account = Column(String(20), unique=True)
    currency = Column(String(50), nullable=False)
    entity_id = Column(Integer, ForeignKey('entities.id'))
    entity = relationship("Entity")
    balance = Column(Float, default=0)
    virtual_balance = Column(Float, default=0)
    user_id = Column(Integer, ForeignKey('users.id'))

    account_credential_params = relationship("AccountCredentialParam")

    @classmethod
    def get_by_account_id(cls, account_id):
        return db_session.query(cls).filter(cls.id == str(account_id)).first()

    @classmethod
    def get_or_create(cls, broker_name, account, user_id):
        account_id = str(account.account_id)
        instance = cls.get_by_account_id(account_id)  # type: Account
        entity_id = Entity.query.filter(func.lower(Entity.name) == broker_name).first().id

        if not instance:
            instance = Account()
            instance.name = account.name or broker_name
            instance.account = account_id
            instance.entity_id = entity_id
            instance.balance = account.balance or 0
            instance.virtual_balance = account.virtual_balance or 0
            db_session.add(instance)
        else:
            instance.virtual_balance = account.virtual_balance
            instance.name = account.name or broker_name
            instance.balance = account.balance

        db_session.flush([instance])

        return instance


class AccountCredentialParam(Base, CRUD):
    __tablename__ = 'account_credential_params'
    __table_args__ = (UniqueConstraint('credential_type_id', 'account_id', name='cred_type_account_uc'),)

    id = Column(Integer, primary_key=True)
    value = Column(String(250))
    credential_type_id = Column(Integer, ForeignKey('entity_credential_types.id'))
    credential_type = relationship("EntityCredentialType")

    account_id = Column(Integer, ForeignKey('accounts.id', ondelete="CASCADE"))
    account_type = Column(Unicode(255))
