import json
import os
import unittest
import configparser
import warnings
import time

import sqlalchemy
from mylittlehelpers import time_elapsed
from termcolor import colored


class InterfaceConfigured(unittest.TestCase):

    def config_exists(self):
        """
        Tests to see that the region bullhorn_interface config file has configurations
        :return:
        """
        config_location = os.environ.get('INTERFACE_CONF_FILE')
        config_location = config_location if config_location else 'bullhorn_interface.conf'
        config_location = os.path.abspath(config_location)
        config = configparser.ConfigParser()
        config.read(config_location)
        return config

    def config_has_configurations(self):
        """
        Tests to see that the configuration file has each of the required keys and returns the vital ones.
        """
        config = self.config_exists()
        return {
            'token_handler': config.get('bullhorn_interface', 'TOKEN_HANDLER'),
            'client_id': config.get('bullhorn_interface', 'CLIENT_ID'),
            'client_secret': config.get('bullhorn_interface', 'CLIENT_SECRET'),
            'bullhorn_username': config.get('bullhorn_interface', 'bullhorn_username'),
            'bullhorn_password': config.get('bullhorn_interface', 'bullhorn_password'),
            'email_address': config.get('bullhorn_interface', 'email_address'),
            'email_password': config.get('bullhorn_interface', 'email_password'),
            'db_name': config.get('bullhorn_interface', 'db_name'),
            'db_host': config.get('bullhorn_interface', 'db_host'),
            'db_user': config.get('bullhorn_interface', 'db_user'),
            'db_password': config.get('bullhorn_interface', 'db_password'),
        }

    def test_vitals_configured(self):
        configurations = self.config_has_configurations()

        # Make sure token_handler is what it should be
        key = 'token_handler'
        self.assertIsInstance(configurations[key], str, f"{key} must be a string.")
        self.assertTrue(bool(configurations[key]), f"{key} cannot be none or empty.")
        self.assertTrue(configurations[key] in ['live', 'pg', 'sqlite'],
                        f"{key} must be one of 'live', 'pg', or 'sqlite'")
        # email configurations are never vital but they still must be strings
        non_vital_keys = ['email_address', 'email_password']
        for key in non_vital_keys:
            if not configurations[key]:
                warnings.warn("{key} is none or empty.")
            self.assertTrue(isinstance(configurations[key], str), f"{key} must be a string.")

        vital_keys = {*configurations.keys()} - {'token_handler', *non_vital_keys}

        # in the case of live none of the database configurations are important
        if configurations[key] == 'live':
            vital_keys = vital_keys - {*[key for key in tuple(vital_keys) if 'db' in key]}

        # in the case of sqlite db_name is vital but no other db configurations are vital
        elif configurations[key] == 'sqlite':
            vital_keys = vital_keys - {*[key for key in tuple(vital_keys) if 'db' in key]}
            vital_keys = {*vital_keys, 'db_name'}

        # make sure all vital keys are non-empty strings
        for key in vital_keys:
            self.assertTrue(bool(configurations[key]), f"{key} cannot be none or empty.")
            self.assertTrue(isinstance(configurations[key], str), f"{key} must be a string.")


# TODO: ensure that login() and get_api_token() do what we expect
class InterfaceFunctions(unittest.TestCase):
    from bullhorn_interface import api
    start = time.time()

    def __init__(self, *args):
        self.db_created = False
        self.full_coverage = os.environ.get('TEST_FULL_COVERAGE')
        os.environ['TESTING_BULLHORN_INTERFACE'] = '1'
        super(InterfaceFunctions, self).__init__(*args)

    def __str__(self):
        return f'{colored(self.__class__.__name__, "blue")}'

    def print(self, *args):
        print(time_elapsed(self.start).strip(), self, *args)

    def create_db(self):
        try:
            self.api.tokenbox.create_database()
            self.db_created = True
        except sqlalchemy.exc.ProgrammingError:
            pass

    def login_and_access(self):
        self.print(f"Testing {self.interface} Bullhorn Login")
        self.interface.login()
        self.print(f"Testing {self.interface} Getting API Token")
        self.interface.get_api_token()

    def basic_call(self):
        self.print(f"Testing {self.interface} Base Call")
        self.interface.api_call()

    def refresh_token(self):
        self.print(f"Testing {self.interface} Refresh Token")
        self.interface.refresh_token()

    def db_destroy(self):
        if self.db_created:
            self.api.tokenbox.destroy_database()

    def run_live_body(self):
        self.interface = self.api.LiveInterface(username=self.api.BULLHORN_USERNAME,
                                                password=self.api.BULLHORN_PASSWORD)
        self.login_and_access()
        self.basic_call()
        self.refresh_token()

    def run_stored_body(self):
        self.interface = self.api.StoredInterface(username=self.api.BULLHORN_USERNAME,
                                                  password=self.api.BULLHORN_PASSWORD)
        self.create_db()
        self.login_and_access()
        self.basic_call()
        self.refresh_token()
        self.db_destroy()

    def test_interface_functions(self):
        if (self.api.TOKEN_HANDLER == 'live') and (not self.full_coverage):
            self.run_live_body()
        elif (self.api.TOKEN_HANDLER in ['pg', 'sqlite']) and (not self.full_coverage):
            self.run_stored_body()
        elif self.full_coverage:
            self.run_live_body()
            self.run_stored_body()


class InterfaceErrorHandling(InterfaceFunctions):

    def __init__(self, *args):
        self.db_created = False
        self.full_coverage = os.environ.get('TEST_FULL_COVERAGE')
        os.environ['TESTING_BULLHORN_INTERFACE'] = '1'
        super(InterfaceFunctions, self).__init__(*args)

    def __str__(self):
        return f'{colored(self.__class__.__name__, "red")}'

    def print(self, *args):
        print(time_elapsed(self.start).strip(), self, *args)

    def login_and_access(self):
        self.print(f"Testing {self.interface} Bullhorn Login")
        self.interface.login()
        self.print(f"Testing {self.interface} Getting API Token")
        self.interface.get_api_token()

    def invoke_bad_login(self):
        self.print(f"Testing {self.interface} Bad Login Handling")
        with self.assertRaises(self.api.APICallError):
            self.interface.login(code=12)

    def invoke_expiration_handling(self):
        self.print(f"Testing {self.interface} Expiration Handling")
        self.interface.login_token['expiry'] = int(self.interface.login_token['expiry']) - 601
        self.interface.api_call()

    def invoke_missing_tokens(self):
        self.print(f"Testing {self.interface} Missing Tokens")
        self.interface.login_token = None
        self.interface.access_token = None
        self.interface.api_call()

    def invoke_api_error_response(self):
        self.print(f"Testing {self.interface} Error Response Handling")
        self.interface.access_token['bh_rest_token'] = '1'
        with self.assertRaises(self.api.APICallError):
            self.interface.api_call()

    def run_live_body(self):
        self.interface = self.api.LiveInterface(username=self.api.BULLHORN_USERNAME,
                                                password=self.api.BULLHORN_PASSWORD)
        self.invoke_bad_login()
        self.login_and_access()
        self.invoke_expiration_handling()
        self.invoke_missing_tokens()
        self.invoke_api_error_response()

    def run_stored_body(self):
        self.interface = self.api.StoredInterface(username=self.api.BULLHORN_USERNAME,
                                                  password=self.api.BULLHORN_PASSWORD)
        self.create_db()
        self.invoke_bad_login()
        self.login_and_access()
        self.invoke_expiration_handling()
        self.invoke_missing_tokens()
        self.invoke_api_error_response()
        self.db_destroy()


def run():
    unittest.main()


if __name__ == "__main__":
    run()




