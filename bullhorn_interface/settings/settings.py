import json
import os

from bullhorn_interface.helpers import __except__, ImproperlyConfigured

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SETTINGS_DIR)


def missing_conf():
    return ImproperlyConfigured('\n\nMissing bullhorn_interface.conf or bullhorn_secrets.json. \n'
                               'Make sure that your bullhorn_interface.conf file exists in '
                               '/bullhorn_interface/settings/ and designates a "SECRETS_LOCATION".')


def missing_conf_location():
    return ImproperlyConfigured('SECRETS_LOCATION not found in bullhorn_interface.conf')


@__except__(FileNotFoundError, lambda: (_ for _ in ()).throw(missing_conf()))
@__except__(KeyError, lambda: (_ for _ in ()).throw(missing_conf_location()))
def get_conf():
    with open(os.path.join(SETTINGS_DIR, 'bullhorn_interface.conf')) as conf:
        conf = json.load(conf)
        with open(os.path.join(SETTINGS_DIR, conf['SECRETS_LOCATION'])) as secrets:
            return json.load(secrets), conf

secrets, conf = get_conf()

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
        raise ImproperlyConfigured(f'{e.args[0]} not found in bullhorn_interface.conf')
    else:
        raise ImproperlyConfigured(f'{e.args[0]} not found in {conf["SECRETS_LOCATION"]}')