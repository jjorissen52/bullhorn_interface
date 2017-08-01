import time
from math import trunc

import os
# from bullhorn.settings.settings import EMAIL_ADDRESS, EMAIL_PASSWORD, SETTINGS_DIR

from settings.settings import EMAIL_ADDRESS, EMAIL_PASSWORD, PROJECT_DIR, SETTINGS_DIR


def send_email(recipient, subject, body, user=EMAIL_ADDRESS, pwd=EMAIL_PASSWORD):
    import smtplib

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
    with open(os.path.join(PROJECT_DIR, 'requirements.txt')) as requirements_file:
        req = map(lambda x: x.replace('\n', ''), requirements_file.readlines())
        return list(req)


def __except__(exception, replacement_function):
    def _try_wrap(function):
        def __try_wrap(*args, **kwargs):
            try:
                return function(*args, **kwargs)
            except exception as e:
                return replacement_function(*args, **kwargs)
        return __try_wrap
    return _try_wrap