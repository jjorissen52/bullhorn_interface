import json
import os

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String,
    desc)
from sqlalchemy.engine.reflection import Inspector
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
from bullhorn_interface.settings import settings


PG_CONFIG_DICT = {
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD,
        'host': 'localhost',
        'port': 5432,
}
PG_CONN_FORMAT = "postgresql://{user}:{password}@{host}:{port}/{database}"
SQLITE_CONN_FORMAT = "sqlite:///{database}.db"

BULLHORN_DB_NAME = 'bullhorn'


CONNECTION_STRINGS = {
    "PG_CONN_URI_DEFAULT": PG_CONN_FORMAT.format(database='postgres', **PG_CONFIG_DICT),
    "PG_CONN_URI_BULLHORN": PG_CONN_FORMAT.format(database=BULLHORN_DB_NAME, **PG_CONFIG_DICT),
    "SQLITE_CONN_URI": SQLITE_CONN_FORMAT.format(database=BULLHORN_DB_NAME)
}

metadata = MetaData()

table_definitions = {
    "login_token": Table("login_token", metadata,
        Column("login_token_pk", Integer, primary_key=True),
        Column('access_token', String(45), nullable=False),
        Column('expires_in', Integer, nullable=False),
        Column('refresh_token', String(45), nullable=False),
        Column('token_type', String(45), nullable=False),
        Column('expiry', Integer, nullable=False),
    ),
    "access_token": Table("access_token", metadata,
        Column("access_token_pk", Integer, primary_key=True),
        Column('bh_rest_token', String(45), nullable=False),
        Column('rest_url', String(60), nullable=False)
    )
}


def get_token(table_name):
    if settings.USE_FLAT_FILES:
        engine = create_engine(CONNECTION_STRINGS["SQLITE_CONN_URI"])
        data = MetaData(engine)
        table = Table(table_name, data, autoload=True)
        conn = engine.connect()
        result = table.select().order_by(desc(f'{table_name}_pk')).execute()
        conn.close()
        for item in result:
            return item
    else:
        engine = create_engine(CONNECTION_STRINGS["PG_CONN_URI_BULLHORN"], poolclass=NullPool)
        data = MetaData(engine)
        table = Table(table_name, data, autoload=True)
        conn = engine.connect()
        result = table.select().order_by(desc(f'{table_name}_pk')).execute()
        conn.close()
        for item in result:
            return item


def update_token(table_name, **kwargs):
    if settings.USE_FLAT_FILES:
        engine = create_engine(CONNECTION_STRINGS["SQLITE_CONN_URI"])
        if not table_name in Inspector.from_engine(engine).get_table_names():
            table_definitions[table_name].create(bind=engine)
            data = MetaData(engine)
            table = Table(table_name, data, autoload=True)
            conn = engine.connect()
            i = table.insert()
            i.execute(**kwargs)
            conn.close()
        else:
            data = MetaData(engine)
            table = Table(table_name, data, autoload=True)
            conn = engine.connect()
            i = table.update().where(table.c[f'{table_name}_pk'] == get_token(table_name)[f'{table_name}_pk'])
            i.execute(**kwargs)
            conn.close()
    else:
        engine = create_engine(CONNECTION_STRINGS["PG_CONN_URI_BULLHORN"], poolclass=NullPool)
        data = MetaData(engine)
        table = Table(table_name, data, autoload=True)
        conn = engine.connect()
        i = table.update().where(table.c[f'{table_name}_pk'] == get_token(table_name)[f'{table_name}_pk'])
        i.execute(**kwargs)
        conn.close()


def create_database():
    pg_engine_default = create_engine(CONNECTION_STRINGS["PG_CONN_URI_DEFAULT"])
    conn = pg_engine_default.connect()
    conn.execute("COMMIT")
    # Do not substitute user-supplied database names here.
    conn.execute("CREATE DATABASE %s" % BULLHORN_DB_NAME)
    conn.close()


def create_table():
    # Get a new engine for the just-created database and create a table.
    engine_new = create_engine(CONNECTION_STRINGS["PG_CONN_URI_BULLHORN"], poolclass=NullPool)
    conn = engine_new.connect()
    metadata.create_all(conn)
    conn.close()


def teardown_database():
    pg_engine_default = create_engine(CONNECTION_STRINGS["PG_CONN_URI_DEFAULT"])
    conn = pg_engine_default.connect()
    conn.execute("COMMIT")
    # Do not substitute user-supplied database names here.
    conn.execute("DROP DATABASE %s" % BULLHORN_DB_NAME)
    conn.close()