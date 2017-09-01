import json
import os

from mylittlehelpers import ImproperlyConfigured


def api_test():
    from . import api
    if api.TOKEN_HANDLER == 'live':
        interface = api.LiveInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
        interface.login()
        interface.get_api_token()
        interface.refresh_token()
        print(interface.api_call())
    elif api.TOKEN_HANDLER in ['pg', 'sqlite']:
        interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
        api.tokenbox.create_database()
        interface.login()
        interface.get_api_token()
        print(interface.api_call())
        api.tokenbox.destroy_database()
    else:
        raise ImproperlyConfigured("TOKEN_HANDLER must be set to 'live', 'pg', or 'sqlite' ")


