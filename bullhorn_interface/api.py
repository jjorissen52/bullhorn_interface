import datetime
import json
import requests
import urllib
import configparser
import os
from operator import xor

from sqlalchemy import Table, Column, Integer, String, MetaData
from tokenbox import TokenBox

config = configparser.ConfigParser()
interface_conf_file = os.environ.get('INTERFACE_CONF_FILE')
interface_conf_file = interface_conf_file if interface_conf_file else 'bullhorn_interface.conf'
config.read(interface_conf_file)

TOKEN_HANDLER = config.get('bullhorn_interface', 'TOKEN_HANDLER')
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

tokenbox = TokenBox(DB_USER, DB_PASSWORD, DB_NAME, metadata, use_sqlite=USE_FLAT_FILES, **table_definitions)


def login(username="", password="", client_id=CLIENT_ID, client_secret=CLIENT_SECRET, code=""):
    base_url = "https://auth.bullhornstaffing.com/oauth"
    example_redirect_url = ["http://www.bullhorn.com/?code=",
                            "{YOUR CODE WILL BE RIGHT HERE}",
                            f"&client_id={client_id}"]

    if not code and not (username and password):
        print(f"Credentials not provided. Provide a username/password combination or follow the procedure below: \n"
              f"Paste this URL into browser {base_url}/authorize?client_id={client_id}&response_type=code \n"
              f"Redirect URL will look like this: {''.join(example_redirect_url)}.\n")

    elif code:
        try:
            params = {
                "client_secret": client_secret,
                "client_id": client_id,
                "grant_type": "authorization_code",
            }
            url = f"{base_url}/token?code={code}"
            response = requests.post(url, params=params)
            login_token = json.loads(response.text)
            login_token['expiry'] = datetime.datetime.now().timestamp() + login_token["expires_in"]
            tokenbox.update_token('login_token', **login_token)
            print(f"New Access Token: {login_token['access_token']}")
        except KeyError:
            print(f'Response from API: {login_token}')
            print(f'Is your token expired? Are your secrets properly configured?')

    elif xor(bool(username), bool(password)):
        print("You must provide both a username and a password.")

    else:
        params = {
            "client_id": client_id,
            "response_type": "code",
            "username": username,
            "password": password,
            "action": "Login",
        }
        url = f"{base_url}/authorize"
        response = requests.post(url, params=params)
        url_params = requests.utils.urlparse(response.url).query
        code = urllib.parse.parse_qs(url_params).get("code")
        try:
            params = {
                "client_secret": client_secret,
                "client_id": client_id,
                "grant_type": "authorization_code",
                "code": code
            }
            url = f"{base_url}/token"
            response = requests.post(url, params=params)
            login_token = json.loads(response.text)
            login_token['expiry'] = datetime.datetime.now().timestamp() + login_token["expires_in"]
            tokenbox.update_token('login_token', **login_token)
            print(f"New Access Token: {login_token['access_token']}")
        except KeyError:
            print(f'Response from API: {login_token}')
            print(f'Is your token expired? Are your secrets properly configured?')


def refresh_token():
    token = tokenbox.get_token('login_token')
    url = "https://auth.bullhornstaffing.com/oauth/token?grant_type=refresh_token"
    url = url + f"&refresh_token={token['refresh_token']}&client_id={CLIENT_ID}"
    url = url + f"&client_secret={CLIENT_SECRET}"
    response = requests.post(url)
    login_token = json.loads(response.text)
    login_token['expiry'] = datetime.datetime.now().timestamp() + login_token["expires_in"]
    tokenbox.update_token('login_token', **login_token)
    return f"New Access Token: {login_token['access_token']}"


def get_api_token():
    login_token = tokenbox.get_token('login_token')
    url = f"https://rest.bullhornstaffing.com/rest-services/login?version=*&access_token={login_token['access_token']}"
    response = requests.get(url)
    temp_token = json.loads(response.text)
    access_token = {"bh_rest_token": temp_token["BhRestToken"], "rest_url": temp_token["restUrl"]}
    tokenbox.update_token('access_token', **access_token)
    return json.dumps(access_token, indent=2, sort_keys=True)


def api_call(command="search", method="", entity="", entity_id="",
             select_fields=[], query="",
             auto_refresh=True, body="", **kwargs):

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

    if auto_refresh:
        print('Refreshing Access Tokens')
        refresh_token()
        get_api_token()

    access_token = tokenbox.get_token('access_token')

    rest_url = access_token['rest_url']
    rest_token = access_token['bh_rest_token']

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

    response = request_func(url, json=body)

    # print(url)
    # print(response.text)

    return json.loads(response.text)


class LiveInterface:
    client_id = CLIENT_ID
    client_secret = CLIENT_SECRET

    def __init__(self, username="", password=""):
        self.username = username
        self.password = password

    def login(self, code=""):
        base_url = "https://auth.bullhornstaffing.com/oauth"
        example_redirect_url = ["http://www.bullhorn.com/?code=",
                                "{YOUR CODE WILL BE RIGHT HERE}",
                                f"&client_id={self.client_id}"]

        if not code and not (self.username and self.password):
            print(f"Credentials not provided. Provide a username/password combination or follow the procedure below: \n"
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
                login_token = json.loads(response.text)
                login_token['expiry'] = datetime.datetime.now().timestamp() + login_token["expires_in"]
                tokenbox.update_token('login_token', **login_token)
                print(f"New Access Token: {login_token['access_token']}")
            except KeyError:
                print(f'Response from API: {login_token}')
                print(f'Is your token expired? Are your secrets properly configured?')

        elif xor(bool(self.username), bool(self.password)):
            print("You must provide both a username and a password.")

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
                response = requests.post(url, params=params)
                self.login_token = json.loads(response.text)
                self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
                print(f"New Access Token: {self.login_token['access_token']}")
            except KeyError:
                print(f'Response from API: {self.login_token}')
                print(f'Is your token expired? Are your secrets properly configured?')

    def refresh_token(self):
        url = "https://auth.bullhornstaffing.com/oauth/token?grant_type=refresh_token"
        url = url + f"&refresh_token={self.login_token['refresh_token']}&client_id={self.client_id}"
        url = url + f"&client_secret={self.client_secret}"
        response = requests.post(url)
        self.login_token = json.loads(response.text)
        self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
        return f"New Access Token: {self.login_token['access_token']}"

    def get_api_token(self):
        url = f"https://rest.bullhornstaffing.com/rest-services/login?version=*&access_token={self.login_token['access_token']}"
        response = requests.get(url)
        temp_token = json.loads(response.text)
        self.access_token = {"bh_rest_token": temp_token["BhRestToken"], "rest_url": temp_token["restUrl"]}
        return json.dumps(self.access_token, indent=2, sort_keys=True)

    def api_call(self, command="search", method="", entity="", entity_id="",
                 select_fields=[], query="",
                 auto_refresh=True, body="", **kwargs):

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

        if auto_refresh:
            print('Refreshing Access Tokens')
            self.refresh_token()
            self.get_api_token()

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

        response = request_func(url, json=body)

        # print(url)
        # print(response.text)

        return json.loads(response.text)