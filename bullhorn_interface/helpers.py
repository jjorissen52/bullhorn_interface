import getpass
import json
import os
import time
from math import trunc


# from bullhorn.settings.settings import EMAIL_ADDRESS, EMAIL_PASSWORD, SETTINGS_DIR

# from settings.settings import EMAIL_ADDRESS, EMAIL_PASSWORD, PROJECT_DIR


def send_email(recipient, subject, body, user=None, pwd=None):

    import smtplib
    from bullhorn_interface.settings.settings import EMAIL_ADDRESS, EMAIL_PASSWORD

    user = user if user else EMAIL_ADDRESS
    pwd = pwd if pwd else EMAIL_PASSWORD

    gmail_user = user
    gmail_pwd = pwd
    FROM = user
    TO = recipient if type(recipient) is list else [recipient]
    SUBJECT = subject
    TEXT = body

    # Prepare actual message
    message = """From: %s\nTo: %s\nSubject: %s\n\n%s
    """ % (FROM, ", ".join(TO), SUBJECT, TEXT)
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.ehlo()
        server.starttls()
        server.login(gmail_user, gmail_pwd)
        server.sendmail(FROM, TO, message)
        server.close()
        print('Email Sent.')
    except:
        print("failed to send mail")


def time_check(start):
    current_time = time.time()
    auto_refresh = False
    hours, rem = divmod(current_time - start, 3600)
    minutes, seconds = divmod(rem, 60)
    if minutes > 7:
        start = time.time()
        auto_refresh = True

    return start, auto_refresh


def print_duration(start):
    current_time = time.time()
    hours, rem = divmod(current_time - start, 3600)
    minutes, seconds = divmod(rem, 60)
    time_string = f'{trunc(hours):02d}:{trunc(minutes):02d}:{trunc(seconds):02d}'
    return f'{time_string:>12}'


def requirements():
    from bullhorn_interface.settings.settings import PROJECT_DIR
    with open(os.path.join(os.path.dirname(PROJECT_DIR), 'requirements.txt')) as requirements_file:
        req = map(lambda x: x.replace('\n', ''), requirements_file.readlines())
        return list(req)


def set_secrets():
    from bullhorn_interface.settings.settings import SETTINGS_DIR
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

    if create:
        SECRETS_LOCATION = input("1 selected. Please specify the full path containing your secrets file: "
                                      "(/path/containing/secrets/)").replace("\n", "")
    else:
        SECRETS_LOCATION = input("2 selected. Please specify the name of your secrets file "
                                      "(/path/to/secrets.json): ").replace("\n", "")

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
    refresh_settings()


def set_conf():
    from bullhorn_interface.settings.settings import SETTINGS_DIR
    use_flat_or_not = input("Would you like to store your access tokens and login tokens in flat files \n"
                            "or in a postgreSQL database? \n"
                            "\t1: PostgreSQL Database\n"
                            "\t2: Flat Files (Default)\n\n"
                            "Note: Flat files may experience concurrency problems when making simultaneous"
                            " API calls.\n")

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
    refresh_settings()


def refresh_settings():
    import bullhorn_interface.settings.settings as settings
    from bullhorn_interface.tests import ImproperlyConfigured

    conf, secrets = settings.load_conf(), settings.load_secrets()

    try:
        settings.USE_FLAT_FILES = conf["USE_FLAT_FILES"]
        settings.CLIENT_ID = secrets["CLIENT_ID"]
        settings.CLIENT_SECRET = secrets["CLIENT_SECRET"]
        settings.EMAIL_ADDRESS = secrets["EMAIL_ADDRESS"]
        settings.EMAIL_PASSWORD = secrets["EMAIL_PASSWORD"]
        settings.DB_USER = secrets["DB_USER"]
        settings.DB_PASSWORD = secrets["DB_PASSWORD"]
    except KeyError as e:
        if "USE_FLAT_FILES" in e.args[0]:
            raise ImproperlyConfigured(f'{e.args[0]} not found in conf.py')
        else:
            raise ImproperlyConfigured(f'{e.args[0]} not found in {conf["SECRETS_LOCATION"]}')
    return secrets


def __except__(exception, replacement_function):
    def _try_wrap(function):
        def __try_wrap(*__args, **__kwargs):
            try:
                return function(*__args, **__kwargs)
            except exception as e:
                return replacement_function(*__args, **__kwargs)
        return __try_wrap
    return _try_wrap