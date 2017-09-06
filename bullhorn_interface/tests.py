import json
import os
import unittest
import configparser
import warnings

import sqlalchemy
from mylittlehelpers import ImproperlyConfigured


class InterfaceConfigured(unittest.TestCase):

    def test_config_exists(self):
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

    def test_config_has_configurations(self):
        """
        Tests to see that the configuration file has each of the required keys and returns the vital ones.
        """
        config = self.test_config_exists()
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
        configurations = self.test_config_has_configurations()

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
class InterfaceCreation(unittest.TestCase):

    def test_database_and_authorization(self):
        from bullhorn_interface import api
        if api.TOKEN_HANDLER == 'live':
            interface = api.LiveInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
            print("Testing Bullhorn Login")
            interface.login()
            print("Testing Getting API Token")
            interface.get_api_token()
        elif api.TOKEN_HANDLER in ['pg', 'sqlite']:
            interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
            created = False
            try:
                api.tokenbox.create_database()
                created = True
            except sqlalchemy.exc.ProgrammingError:
                pass
            print("Testing Bullhorn Login")
            interface.login()
            print("Testing Getting API Token")
            interface.get_api_token()
            if created:
                api.tokenbox.destroy_database()
        else:
            raise ImproperlyConfigured("TOKEN_HANDLER must be set to 'live', 'pg', or 'sqlite' ")


if __name__ == "__main__":
    unittest.main()




