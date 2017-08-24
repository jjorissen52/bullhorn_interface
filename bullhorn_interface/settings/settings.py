import getpass
import json
import os

from bullhorn_interface.helpers import __except__, refresh_settings
from bullhorn_interface.tests import ImproperlyConfigured

SETTINGS_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(SETTINGS_DIR)


def gather_secrets_location(create, designate):
    if create:
        secrets_location = input("1 selected. Please specify the full path containing your secrets file: "
                                      "(/path/containing/secrets/)")\
                            .replace("\n", "").replace("\\", "/").replace("//", "/")
        try:
            file = open(os.path.join(secrets_location, 'bullhorn_secrets.json'), 'w')
            file.close()

        except FileNotFoundError:
            print("Could not create secrets at that location. Please check your input and try again.\n\n")
            return gather_secrets_location(create, designate)

    elif designate:
        secrets_location = input("2 selected. Please specify the name of your secrets file "
                                      "(/path/to/secrets.json): ").replace("\n", "")
        try:
            file = open(os.path.join(secrets_location), 'r')
            file.close()

        except FileNotFoundError:
            print("Could not find secrets at that location. Please check your input and try again.\n\n")
            return gather_secrets_location(create, designate)
    else:
        raise Exception("1 or 2 expected as input.")

    return secrets_location


def set_secrets():
    create, designate = False, False
    create_or_designate = str(input('Would you like to: \n'
                   '\t1: Create a new file named bullhorn_secrets.py and store it in a specified path?\n'
                   '\t2: Specify the full path of an existing secrets file?\n'))
    if '1' in create_or_designate:
        create = True
    elif '2' in create_or_designate:
        designate = True
    else:
        print('Please specify option 1 or 2 by typing 1 or 2.')
        return

    SECRETS_LOCATION = gather_secrets_location(create, designate)

    if create:
        with open(os.path.join(SETTINGS_DIR, 'conf.py')) as conf:
            USE_FLAT_FILES = json.load(conf)['USE_FLAT_FILES']
        SECRETS_LOCATION = os.path.join(SECRETS_LOCATION, 'bullhorn_secrets.json')
        secrets = {
            "CLIENT_ID": input("Please input your Bullhorn Client ID for API development: "),
            "CLIENT_SECRET": getpass.getpass("Bullhorn Client Secret: "),
            "EMAIL_ADDRESS": input("Default gmail address for Bullhorn API Interface used in helpers.send_mail(): "),
            "EMAIL_PASSWORD": getpass.getpass("Default gmail passwrd for Bullhorn API Interface used in helpers.send_mail(): "),
            "DB_USER": input("PostgreSQL database login role username. (Database used to store access and API tokens): "),
            "DB_PASSWORD": getpass.getpass("PostgreSQL database login role password. (Database used to store access and API tokens): "),
        }
        with open(os.path.join(SETTINGS_DIR, 'conf.py'), 'w') as new_conf:
            new_conf_dict = {"USE_FLAT_FILES": USE_FLAT_FILES, "SECRETS_LOCATION": SECRETS_LOCATION}
            new_conf.write(json.dumps(new_conf_dict, indent=4))
        with open(os.path.join(SECRETS_LOCATION), 'w') as new_secrets:
            new_secrets.write(json.dumps(secrets, indent=4))

    elif designate:
        with open(os.path.join(SETTINGS_DIR, 'conf.py')) as conf:
            USE_FLAT_FILES = json.load(conf)['USE_FLAT_FILES']
        with open(os.path.join(SETTINGS_DIR, 'conf.py'), 'w') as new_conf:
            new_conf_dict = {"USE_FLAT_FILES": USE_FLAT_FILES, "SECRETS_LOCATION": SECRETS_LOCATION}
            new_conf.write(json.dumps(new_conf_dict, indent=4))


def set_conf():
    use_flat_or_not = input("Would you like to use an SQLite or PostgreSQL database for token storage? \n"
                            "\t1: PostgreSQL Database\n"
                            "\t2: SQLite Database (Default)\n\n"
                            "Note: PostgreSQL is really only necessary for high concurrency; SQLite will suffice in "
                            "most use cases.\n")

    if '1' in use_flat_or_not:
        flat = False
    else:
        flat = True

    print(f'{2 if flat else 1} selected.')

    with open(os.path.join(SETTINGS_DIR, 'conf.py')) as conf:
        SECRETS_LOCATION = json.load(conf).get('SECRETS_LOCATION')
    with open(os.path.join(SETTINGS_DIR, 'conf.py'), 'w') as new_conf:
        new_conf_dict = {"USE_FLAT_FILES": flat, "SECRETS_LOCATION": SECRETS_LOCATION}
        new_conf.write(json.dumps(new_conf_dict, indent=4))


def create_conf():
    print('creating conf')
    conf_dict = {
        "USE_FLAT_FILES": True,
        "SECRETS_LOCATION": "bullhorn_secrets.py"
    }
    with open(os.path.join(SETTINGS_DIR, 'conf.py'), 'w') as conf:
        conf.write(json.dumps(conf_dict, indent=4))
    return load_conf()


def create_secrets():
    set_conf()
    set_secrets()
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