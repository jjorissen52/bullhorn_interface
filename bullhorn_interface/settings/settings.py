import json
import os

from bullhorn_interface.helpers import __except__
from bullhorn_interface.tests import ImproperlyConfigured

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SETTINGS_DIR)


def create_conf():
    conf_dict = {
        "USE_FLAT_FILES": True,
        "SECRETS_LOCATION": "bullhorn_secrets.py"
    }
    with open(os.path.join(SETTINGS_DIR, 'conf.py'), 'w') as conf:
        conf.write(json.dumps(conf_dict, indent=4))
    return load_conf()


def create_secrets():
    secrets_dict = {
          "CLIENT_ID": "",
          "CLIENT_SECRET": "",
          "EMAIL_ADDRESS": "",
          "EMAIL_PASSWORD": "",
          "DB_USER": "",
          "DB_PASSWORD": ""
    }
    with open(os.path.join(SETTINGS_DIR, 'bullhorn_secrets.py'), 'w') as secrets:
        secrets.write(json.dumps(secrets_dict, indent=4))
    return load_secrets()


@__except__(FileNotFoundError, lambda: create_conf())
def load_conf():

    with open(os.path.join(SETTINGS_DIR, 'conf.py')) as conf:
        conf = json.load(conf)
    return conf


@__except__(FileNotFoundError, lambda: create_secrets())
def load_secrets():
    conf = load_conf()
    with open(conf['SECRETS_LOCATION']) as secrets:
        secrets = json.load(secrets)

    try:
        USE_FLAT_FILES = conf["USE_FLAT_FILES"]
        CLIENT_ID = secrets["CLIENT_ID"]
        CLIENT_SECRET = secrets["CLIENT_SECRET"]
        EMAIL_ADDRESS = secrets["EMAIL_ADDRESS"]
        EMAIL_PASSWORD = secrets["EMAIL_PASSWORD"]
        DB_USER = secrets["DB_USER"]
        DB_PASSWORD = secrets["DB_PASSWORD"]
    except KeyError as e:
        if "USE_FLAT_FILES" in e.args[0]:
            raise ImproperlyConfigured(f'{e.args[0]} not found in conf.py')
        else:
            raise ImproperlyConfigured(f'{e.args[0]} not found in {conf["SECRETS_LOCATION"]}')
    return secrets

secrets, conf = load_secrets(), load_conf()

USE_FLAT_FILES = conf["USE_FLAT_FILES"]
CLIENT_ID = secrets["CLIENT_ID"]
CLIENT_SECRET = secrets["CLIENT_SECRET"]
EMAIL_ADDRESS = secrets["EMAIL_ADDRESS"]
EMAIL_PASSWORD = secrets["EMAIL_PASSWORD"]
DB_USER = secrets["DB_USER"]
DB_PASSWORD = secrets["DB_PASSWORD"]