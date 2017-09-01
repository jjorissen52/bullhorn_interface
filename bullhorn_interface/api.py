import datetime
import time
import moment
import json
import requests
import urllib
import configparser
import os
import sys
from operator import xor

from sqlalchemy import Table, Column, Integer, String, MetaData
from tokenbox import TokenBox
from mylittlehelpers import ImproperlyConfigured, __except__


class APICallError(BaseException):
    pass

config = configparser.ConfigParser()
interface_conf_file = os.environ.get('INTERFACE_CONF_FILE')
interface_conf_file = interface_conf_file if interface_conf_file else 'bullhorn_interface.conf'
config.read(os.path.abspath(interface_conf_file))

try:
    TOKEN_HANDLER = config.get('bullhorn_interface', 'TOKEN_HANDLER')
except configparser.NoSectionError:
    raise ImproperlyConfigured('No configuration file found. See the documentation on configuring the interface'
                               ' for more information.')

CLIENT_ID = config.get('bullhorn_interface', 'CLIENT_ID')
CLIENT_SECRET = config.get('bullhorn_interface', 'CLIENT_SECRET')
BULLHORN_USERNAME = config.get('bullhorn_interface', 'BULLHORN_USERNAME')
BULLHORN_PASSWORD = config.get('bullhorn_interface', 'BULLHORN_PASSWORD')
EMAIL_ADDRESS = config.get('bullhorn_interface', 'EMAIL_ADDRESS')
EMAIL_PASSWORD = config.get('bullhorn_interface', 'EMAIL_PASSWORD')
DB_NAME = config.get('bullhorn_interface', 'DB_NAME')
DB_HOST = config.get('bullhorn_interface', 'DB_HOST')
DB_USER = config.get('bullhorn_interface', 'DB_USER')
DB_PASSWORD = config.get('bullhorn_interface', 'DB_PASSWORD')

if TOKEN_HANDLER == 'pg':
    USE_FLAT_FILES = False
else:
    USE_FLAT_FILES = True

metadata = MetaData()

table_definitions = {
    "login_token": Table("login_token", metadata,
        Column("login_token_pk", Integer, primary_key=True),
        Column('access_token', String(45), nullable=False),
        Column('expires_in', Integer, nullable=False),
        Column('refresh_token', String(45), nullable=False),
        Column('token_type', String(45), nullable=False),
        Column('expiry', Integer, nullable=False),
    ),
    "access_token": Table("access_token", metadata,
        Column("access_token_pk", Integer, primary_key=True),
        Column('bh_rest_token', String(45), nullable=False),
        Column('rest_url', String(60), nullable=False)
    )
}

tokenbox = TokenBox(DB_USER, DB_PASSWORD, DB_NAME, metadata, use_sqlite=USE_FLAT_FILES, db_host=DB_HOST,
                    **table_definitions)


class Interface:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    def __init__(self, username="", password="", max_connection_attempts=5, max_refresh_attempts=10):

        self.username = username
        self.password = password
        self.login_token = {}
        self.access_token = {}
        self.max_connection_attempts = max_connection_attempts
        self.max_refresh_attempts = max_refresh_attempts

    def self_has_tokens(self):
        has_tokens = self.login_token and self.access_token
        return has_tokens

    def expired(self):
        return moment.unix(self.login_token['expiry']) < moment.now()

    def get_token(self, *args):
        raise NotImplementedError

    def update_token(self, *args, **kwargs):
        raise NotImplementedError

    def grab_tokens(self):
        raise NotImplementedError

    def fresh(self, independent=False, attempt=1, max_attempts=10):
        # different behavior based on if the Interface is independent
        if independent:
            # gets tokens if the instance doesn't have them already
            if not self.self_has_tokens():
                self.grab_tokens()
            if self.expired():
                self.login()
                sys.stdout.write('Refreshing API Token\n')
                self.get_api_token()
            return True

        else:
            if not self.self_has_tokens():
                self.grab_tokens()
            if self.expired():
                if attempt <= max_attempts:
                    sys.stdout.write(f'Token Expired. Attempt {attempt}/{max_attempts} failed.\n')
                    time.sleep(6)
                    self.grab_tokens()
                    return self.fresh(independent, attempt=attempt + 1, max_attempts=max_attempts)
                else:
                    sys.stdout.write(f'Token was not refreshed in time.\n')
                    return False
            else:
                return True

    def login(self, code="", attempt=0):
        base_url = "https://auth.bullhornstaffing.com/oauth"
        example_redirect_url = ["http://www.bullhorn.com/?code=",
                                "{YOUR CODE WILL BE RIGHT HERE}",
                                f"&client_id={self.client_id}"]

        if not code and not (self.username and self.password):
            sys.stdout.write(f"Credentials not provided. Provide a username/password combination or follow the procedure below: \n"
                  f"Paste this URL into browser {base_url}/authorize?client_id={self.client_id}&response_type=code \n"
                  f"Redirect URL will look like this: {''.join(example_redirect_url)}.\n")

        elif code:
            try:
                params = {
                    "client_secret": self.client_secret,
                    "client_id": self.client_id,
                    "grant_type": "authorization_code",
                }
                url = f"{base_url}/token?code={code}"
                response = requests.post(url, params=params)
                self.login_token = json.loads(response.text)
                self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
                self.update_token('login_token', **self.login_token)
                sys.stdout.write(f"New Access Token: {self.login_token['access_token']}\n")
            except KeyError:
                sys.stdout.write(f'Response from API: {self.login_token}')
                sys.stdout.write(f'Is your token expired? Are your secrets properly configured?\n')

        elif xor(bool(self.username), bool(self.password)):
            sys.stdout.write("You must provide both a username and a password.\n")

        else:
            params = {
                "client_id": self.client_id,
                "response_type": "code",
                "username": self.username,
                "password": self.password,
                "action": "Login",
            }
            url = f"{base_url}/authorize"
            response = requests.post(url, params=params)
            url_params = requests.utils.urlparse(response.url).query
            code = urllib.parse.parse_qs(url_params).get("code")
            try:
                params = {
                    "client_secret": self.client_secret,
                    "client_id": self.client_id,
                    "grant_type": "authorization_code",
                    "code": code
                }
                url = f"{base_url}/token"

                try:
                    response = requests.post(url, params=params, timeout=5)
                except requests.exceptions.ConnectTimeout:
                    sys.stdout.write(f'Connection timed out during login. '
                                     f'Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
                    if attempt < self.max_connection_attempts:
                        return self.login(code, attempt + 1)
                    else:
                        raise APICallError('interface could not establish a connection to make the API call.')

                self.login_token = json.loads(response.text)
                self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
                self.update_token('login_token', **self.login_token)
                sys.stdout.write(f"New Access Token: {self.login_token['access_token']}\n")
            except KeyError:
                sys.stdout.write(f'Response from API: {self.login_token}\n')
                sys.stdout.write(f'Is your token expired? Are your secrets properly configured?\n')

    def refresh_token(self, attempt=0):
        if not self.login_token:
            self.login_token = self.get_token('login_token')
        url = "https://auth.bullhornstaffing.com/oauth/token?grant_type=refresh_token"
        url = url + f"&refresh_token={self.login_token['refresh_token']}&client_id={self.client_id}"
        url = url + f"&client_secret={self.client_secret}"
        try:
            response = requests.post(url, timeout=5)
        except requests.exceptions.ConnectTimeout:
            sys.stdout.write(f'Connection timed out during refresh_token. '
                             f'Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
            if attempt < self.max_connection_attempts:
                return self.refresh_token(attempt + 1)
            else:
                raise APICallError('interface could not establish a connection to make the API call.')

        self.login_token = json.loads(response.text)
        self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
        self.update_token('login_token', **self.login_token)
        sys.stdout.write(f"New Access Token: {self.login_token['access_token']}\n")

    def get_api_token(self, attempt=0):
        if not self.login_token:
            self.login_token = self.get_token('login_token')
        url = f"https://rest.bullhornstaffing.com/rest-services/login?version=*&access_token={self.login_token['access_token']}"

        try:
            response = requests.get(url)
        except requests.exceptions.ConnectTimeout:
            sys.stdout.write(f'Connection timed out during get_api_token. Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
            if attempt < self.max_connection_attempts:
                return self.get_api_token(attempt + 1)
            else:
                raise APICallError('interface could not establish a connection to make the API call.')

        temp_token = json.loads(response.text)
        self.access_token = {"bh_rest_token": temp_token["BhRestToken"], "rest_url": temp_token["restUrl"]}
        self.update_token('access_token', **self.access_token)
        sys.stdout.write(f'{json.dumps(self.access_token, indent=2, sort_keys=True)}\n')

    def api_call(self, command="search", method="", entity="", entity_id="",
                 select_fields="", query="", body="", independent=True, attempt=0, **kwargs):

        if not self.fresh(independent, max_attempts=self.max_refresh_attempts):
            raise APICallError("Token could not be refreshed. Did you establish an independent Interface to run "
                               "alongside your dependent Interfaces?")

        if command == "search" or command == "query":
            # defaults for easy testing
            if not entity:
                entity = "Candidate"
            if not entity_id and not query:
                query = "id:1"
            if not select_fields:
                select_fields = ["id", "firstName", "middleName", "lastName", "comments", "notes(*)"]
            request_func = requests.get

        elif command == "entity":
            if method == "UPDATE":
                request_func = requests.post
            elif method == "CREATE":
                request_func = requests.put
            elif method == "GET":
                request_func = requests.get

        rest_url = self.access_token['rest_url']
        rest_token = self.access_token['bh_rest_token']

        entity_id_str = f"/{entity_id}" if entity_id else ""
        url = f"{rest_url}/{command}/{entity}{entity_id_str}?BhRestToken={rest_token}"

        if select_fields:
            if type(select_fields) is str:
                url += f"&fields={select_fields}"
            elif type(select_fields) is list:
                url += f"&fields={','.join(select_fields)}"
            else:
                raise TypeError('select_fields must be a str or list object.')

        if query:
            url += f"&query={query}"

        for key in kwargs.keys():
            url += f"&{key}={kwargs[key]}"

        try:
            response = request_func(url, json=body, timeout=5)
        except requests.exceptions.ConnectTimeout:
            sys.stdout.write(f'Connection timed out during API call. Attempt {attempt+1}/{self.max_connection_attempts}'
                             f' failed.\n')
            if attempt < self.max_connection_attempts:
                return self.api_call(command, method, entity, entity_id, select_fields, query, body, independent,
                                     attempt+1, **kwargs)
            else:
                raise APICallError('interface could not establish a connection to make the API call.')

        return json.loads(response.text)


class StoredInterface(Interface):

    def update_token(self, *args, **kwargs):
        # put the new token in the tokenbox
        tokenbox.update_token(*args, **kwargs)

    def get_token(self, *args, **kwargs):
        # get the token from the tokenbox
        tokenbox.get_token(*args, **kwargs)

    def grab_tokens(self):
        # grab both tokens from the tokenbox
        self.login_token = tokenbox.get_token('login_token')
        self.access_token = tokenbox.get_token('access_token')

    def api_call(self, command="search", method="", entity="", entity_id="",
                 select_fields="", query="", body="", independent=True, attempt=0, **kwargs):
        super(StoredInterface, self).api_call(command="search", method="", entity="", entity_id="",
                                              select_fields="", query="", body="", independent=False,
                                              attempt=0, **kwargs)


class LiveInterface(Interface):

    def update_token(self, *args, **kwargs):
        self.__setattr__(args[0], kwargs)

    def get_token(self, *args, **kwargs):
        return self.__getattribute__(args[0])

    def grab_tokens(self):
        self.login()
        self.get_api_token()

    def api_call(self, command="search", method="", entity="", entity_id="",
                 select_fields="", query="", body="", independent=True, attempt=0, **kwargs):
        super(LiveInterface, self).api_call(command="search", method="", entity="", entity_id="",
                                            select_fields="", query="", body="", independent=True,
                                            attempt=0, **kwargs)
