import json
import os

from bullhorn_interface.helpers import __except__


class ImproperlyConfigured(BaseException):
    pass

def missing_conf():
    return ImproperlyConfigured('\n\nMissing conf.py or bullhorn_secrets.py. \n'
                               'Make sure that your conf.py file exists in '
                               '/bullhorn_interface/settings/ and designates a "SECRETS_LOCATION".')


def missing_conf_location():
    return ImproperlyConfigured('SECRETS_LOCATION not found in conf.py')


@__except__(FileNotFoundError, lambda: (_ for _ in ()).throw(missing_conf()))
@__except__(KeyError, lambda: (_ for _ in ()).throw(missing_conf_location()))
def conf_exists_test():
    from bullhorn_interface.settings.settings import SETTINGS_DIR
    with open(os.path.join(SETTINGS_DIR, 'conf.py')) as conf:
        conf = json.load(conf)
        with open(os.path.join(SETTINGS_DIR, conf['SECRETS_LOCATION'])) as secrets:
            return json.load(secrets), conf


def valid_conf_test():
    secrets, conf = conf_exists_test()
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
    print('Test Passed.')