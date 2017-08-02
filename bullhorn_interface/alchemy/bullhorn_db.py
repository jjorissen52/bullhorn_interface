import json
import os

from sqlalchemy import (
    create_engine,
    MetaData,
    Table,
    Column,
    Integer,
    String
)
from sqlalchemy.pool import NullPool
from bullhorn_interface.settings import settings


DB_CONFIG_DICT = {
        'user': settings.DB_USER,
        'password': settings.DB_PASSWORD,
        'host': 'localhost',
        'port': 5432,
}
DB_CONN_FORMAT = "postgresql://{user}:{password}@{host}:{port}/{database}"
DB_CONN_URI_DEFAULT = (DB_CONN_FORMAT.format(
    database='postgres',
    **DB_CONFIG_DICT))
engine_default = create_engine(DB_CONN_URI_DEFAULT)
NEW_DB_NAME = 'bullhorn'
DB_CONN_URI_NEW = (DB_CONN_FORMAT.format(
    database=NEW_DB_NAME,
    **DB_CONFIG_DICT))
metadata = MetaData()
class LoginToken:
    table_name = 'login_token'
    table_name_id = table_name + '_pk'
    table = Table(table_name, metadata,
        Column(table_name_id, Integer, primary_key=True),
        Column('access_token', String(45), nullable=False),
        Column('expires_in', Integer, nullable=False),
        Column('refresh_token', String(45), nullable=False),
        Column('token_type', String(45), nullable=False),
        Column('expiry', Integer, nullable=False),
    )
class AccessToken:
    table_name = 'access_token'
    table_name_id = table_name + '_pk'
    table = Table(table_name, metadata,
        Column(table_name_id, Integer, primary_key=True),
        Column('bh_rest_token', String(45), nullable=False),
        Column('rest_url', String(60), nullable=False)
    )


def select_token(table_name):
    if settings.USE_FLAT_FILES:
        print(settings.USE_FLAT_FILES)
        with open(os.path.join(settings.SETTINGS_DIR, f'{table_name}.json')) as token_file:
            token = json.load(token_file)
            token_file.close()
            return [token]
    else:
        engine = create_engine(DB_CONN_URI_NEW, poolclass=NullPool)
        data = MetaData(engine)
        table = Table(table_name, data, autoload=True)
        conn = engine.connect()
        result = table.select().order_by(table_name + "_pk desc").execute()
        conn.close()
        return result

def insert_token(table, kwargs):
    if settings.USE_FLAT_FILES:
        with open(os.path.join(settings.SETTINGS_DIR, f'{table}.json'), 'w') as token_file:
            json.dump(kwargs, token_file, indent=2, sort_keys=True)
            token_file.close()
    else:
        engine = create_engine(DB_CONN_URI_NEW, poolclass=NullPool)
        data = MetaData(engine)
        table = Table(table, data, autoload=True)
        conn = engine.connect()
        i = table.insert()
        i.execute(**kwargs)
        conn.close()


def setup_module(db_name=NEW_DB_NAME):
    conn = engine_default.connect()
    conn.execute("COMMIT")
    # Do not substitute user-supplied database names here.
    conn.execute("CREATE DATABASE %s" % db_name)
    conn.close()

def create_table():
    # Get a new engine for the just-created database and create a table.
    engine_new = create_engine(DB_CONN_URI_NEW, poolclass=NullPool)
    conn = engine_new.connect()
    metadata.create_all(conn)
    conn.close()


def teardown_module(db_name=NEW_DB_NAME):
    conn = engine_default.connect()
    conn.execute("COMMIT")
    # Do not substitute user-supplied database names here.
    conn.execute("DROP DATABASE %s" % db_name)
    conn.close()