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