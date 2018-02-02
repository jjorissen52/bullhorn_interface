import datetime
import time
import base64
import json
import requests
import urllib
import configparser
import os
import sys
from operator import xor
from functools import wraps
from termcolor import colored

from sqlalchemy import Table, Column, Integer, String, MetaData
from tokenbox import TokenBox

from . helpers import APICallError, ImproperlyConfigured
from . wrappers import depaginate_query, depaginate_search, log_parameters, no_such_table_handler

config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
interface_conf_file = os.environ.get('INTERFACE_CONF_FILE')
interface_conf_file = interface_conf_file if interface_conf_file else 'bullhorn_interface.conf'
config.read(os.path.abspath(interface_conf_file))

try:
    TOKEN_HANDLER = config.get('bullhorn_interface', 'TOKEN_HANDLER')
except configparser.NoSectionError:
    raise ImproperlyConfigured('No configuration file found. See the documentation on configuring the interface'
                               ' for more information.')

PRINT_SPACING = 8 if os.environ.get('TESTING_BULLHORN_INTERFACE') else 4
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
    def __init__(self, username="", password="", max_connection_attempts=5, max_refresh_attempts=10, independent=True,
                 debug="", serialize=False):

        self.username = username if username else BULLHORN_USERNAME
        self.password = password if password else BULLHORN_PASSWORD
        self.login_token = {}
        self.access_token = {}
        self.max_connection_attempts = max_connection_attempts
        self.max_refresh_attempts = max_refresh_attempts
        self.independent = independent
        self.client_id = CLIENT_ID
        self.client_secret = CLIENT_SECRET
        self._debug = debug
        self._serialize = serialize

    def self_has_tokens(self):
        """
        Inspect Interface instance for tokens, usually before attempting to access them.

        :return: (bool)
        """
        has_tokens = self.login_token and self.access_token
        return has_tokens

    def expired(self):
        """
        Sees if the login token of the Interface instance has expired.

        :return: (bool)
        """
        return int(float(self.login_token['expiry'])) < time.time()

    def get_token(self, *args):
        """
        Method to retrieve auth or api token. Implementation varies with interface type.

        :param args:
        :return:
        """
        raise NotImplementedError

    def update_token(self, *args, **kwargs):
        """
        Method to update auth or api token. Implementation varies with interface type.

        :param args:
        :param kwargs:
        :return:
        """
        raise NotImplementedError

    def grab_tokens(self):
        """
        Method to get both auth and api tokens. Implementation varies with interface type.

        :return:
        """
        raise NotImplementedError

    def fresh(self, independent=False, attempt=1, max_attempts=10):
        """
        Keeps auth tokens and API tokens from getting stale. Behavior varies with interface type.

        :param independent: (bool) indicates whether the Interface object is in charge of refreshing its own tokens
        :param attempt: (int) nth attempt, passed to any login or refresh method
        :param max_attempts: (int) number of attempts before fresh stops attempting to login or refresh the token
        :return: (bool) whether or not the token(s) is/are fresh
        """

        if independent:
            # gets tokens if the instance doesn't have them already
            if not self.self_has_tokens():
                self.grab_tokens()
            if self.expired():
                if self.username and self.password:
                    self.login()
                else:
                    self.refresh_token()
                self.get_api_token()
                sys.stdout.write(f'{" "*PRINT_SPACING}Refreshing API Token\n')
            return True

        else:
            if not self.self_has_tokens():
                self.grab_tokens()
            if self.expired():
                if attempt <= max_attempts:
                    sys.stdout.write(f'{" "*PRINT_SPACING}Token Expired. Attempt {attempt}/{max_attempts} failed.\n')
                    time.sleep(6)
                    self.grab_tokens()
                    return self.fresh(independent, attempt=attempt + 1, max_attempts=max_attempts)
                else:
                    sys.stdout.write(f'{" "*PRINT_SPACING}Token was not refreshed in time.\n')
                    return False
            else:
                return True

    def login(self, code="", attempt=0):
        """
        Grants an auth token to valid credentials or provides a method to manually login

        :param code: (str) (sometimes optional) auth code for authenticating through the browser
        :param attempt: (int) nth login attempt
        :return:
        """
        base_url = "https://auth.bullhornstaffing.com/oauth"
        example_redirect_url = ["http://www.bullhorn.com/?code=",
                                "YOUR%CODE%WILL%BE%RIGHT%HERE",
                                f"&client_id={self.client_id}"]

        if not code and not (self.username and self.password):
            sys.stdout.write(f"Credentials not provided. Provide a username/password combination or follow the "
                             f"procedure below: \n"
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
                sys.stdout.write(f'{" "*PRINT_SPACING}New Login Token\n')
            except KeyError:
                raise APICallError(f'API Call resulted in an error: \n {self.login_token} \n Is your Bullhorn Client '
                                   f'information properly configured?')

        elif xor(bool(self.username), bool(self.password)):
            sys.stdout.write('You must provide both a username and a password.\n')

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
                except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
                    sys.stdout.write(f'{" "*PRINT_SPACING}Connection timed out during login. '
                                     f'{" "*PRINT_SPACING}Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
                    if attempt < self.max_connection_attempts:
                        return self.login(code, attempt + 1)
                    else:
                        raise APICallError(f'{" "*PRINT_SPACING}interface could not establish a connection to '
                                           'make the API call.')

                self.login_token = json.loads(response.text)
                self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
                self.update_token('login_token', **self.login_token)
                sys.stdout.write(f'{" "*PRINT_SPACING}New Login Token\n')
            except KeyError:
                raise APICallError(f'API Call resulted in an error: \n {self.login_token} \n Is your Bullhorn Client '
                                   f'information properly configured?')

    def refresh_token(self, attempt=0):
        """
        Refreshes an existing API token

        :param attempt: (int) nth attempt at refreshing token
        :return:
        """
        if not self.login_token:
            self.login_token = self.get_token('login_token')
        url = "https://auth.bullhornstaffing.com/oauth/token?grant_type=refresh_token"
        url = url + f"&refresh_token={self.login_token['refresh_token']}&client_id={self.client_id}"
        url = url + f"&client_secret={self.client_secret}"
        try:
            response = requests.post(url, timeout=5)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            sys.stdout.write(f'{" "*PRINT_SPACING}Connection timed out during refresh_token. '
                             f'Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
            if attempt < self.max_connection_attempts:
                return self.refresh_token(attempt + 1)
            else:
                raise APICallError(f'interface could not establish a connection to make the '
                                   'API call.')

        self.login_token = json.loads(response.text)
        self.login_token['expiry'] = datetime.datetime.now().timestamp() + self.login_token["expires_in"]
        self.update_token('login_token', **self.login_token)
        if not 'TESTING_BULLHORN_INTERFACE':
            sys.stdout.write(f'{" "*PRINT_SPACING}New Access Token\n')
            sys.stdout.flush()

    def get_api_token(self, attempt=0):
        """
        Uses auth token to get an API access token and url which are required to query the REST API

        :param attempt: (int) nth attempt
        :return:
        """
        if not self.login_token:
            self.login_token = self.get_token('login_token')
        url = f"https://rest.bullhornstaffing.com/rest-services/login?version=*&access_token={self.login_token['access_token']}"

        try:
            response = requests.get(url, timeout=5)
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            sys.stdout.write(f'{" "*PRINT_SPACING}Connection timed out during get_api_token. '
                             f'Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
            if attempt < self.max_connection_attempts:
                return self.get_api_token(attempt + 1)
            else:
                raise APICallError(f'interface could not establish a connection to make the '
                                   f'API call.')

        temp_token = json.loads(response.text)
        self.access_token = {"bh_rest_token": temp_token["BhRestToken"], "rest_url": temp_token["restUrl"]}
        self.update_token('access_token', **self.access_token)
        if 'errorMessage' in self.access_token:
            raise APICallError(f'API Call resulted in an error: \n '
                               f'{json.dumps(self.access_token, indent=PRINT_SPACING, sort_keys=True)}')
        else:
            sys.stdout.write(f'{" "*PRINT_SPACING}New Access Token\n')

    @log_parameters
    def api_call(self, command="", method="", entity="", entity_id="",
                 select_fields="*", query="", body="", attempt=0, **kwargs):
        """
        Serves as an abstract Python API layer for Bullhorns REST API

        :param command: (str) command that bullhorn accepts (see bullhorn api reference material)
        :param method: (str) HTTP verbs telling the API how you want to interact with the data ("GET", "POST", "UPDATE", "DELETE)
        :param entity: (str) Bullhorn entity that you wish to interact with
        :param entity_id: (int, str) (sometimes optional) numeric id corresponding to the desired entity, required for all POST and UPDATE commands
        :param select_fields: (str, list) fields desired in response from API call
        :param query: (str) SQL style query string (only used when command="search" and command="query")
        :param body: (dict) dictionary of items to be posted during "UPDATE" or "POST" (when command="entity" or command="entityFiles")
        :param attempt: (int) nth attempt at the api_call, after 10 attempts it will stop attempting the call
        :param kwargs: (kwargs) additional parameters to be passed to the request URL (count=100 becomes &count=100)
        :return: hopefully a dict with the key "data" with a  list of the searched, queried, added, or updated data
        """

        if not command:
            raise APICallError(f'Command must be specified.')

        if command == "search" or command == "query":
            if not entity_id and not query:
                query = "id:1"

        if not entity:
            raise APICallError(f'Entity must be specified.')

        methods = {
            "": lambda *_args, **_kwargs: (_ for _ in ()).throw(APICallError('You must provide a method.')),
            "GET": requests.get,
            "UPDATE": requests.post,
            "DELETE": requests.delete,
            "CREATE": requests.put
        }

        if not self.fresh(self.independent, max_attempts=self.max_refresh_attempts):
            raise APICallError(f'Token could not be refreshed. Did you establish an '
                               "independent Interface to run alongside your dependent Interfaces?")

        rest_url = self.access_token['rest_url']
        rest_token = self.access_token['bh_rest_token']

        entity_id_str = f"/{entity_id}" if entity_id else ""
        url = f"{rest_url}/{command}/{entity}{entity_id_str}?BhRestToken={rest_token}&useV2=true"

        if select_fields:
            if type(select_fields) is str:
                url += f"&fields={select_fields.replace(' ','')}"
            elif type(select_fields) is list:
                url += f"&fields={','.join(select_fields)}"
            else:
                raise TypeError(f'{" "*PRINT_SPACING}select_fields must be a str or list object.')

        if query:
            url += f"&query={query}"

        for key in kwargs.keys():
            url += f"&{key}={kwargs[key]}"

        try:
            response = methods[method.upper()](url, json=body, timeout=5)
            if 'url' in self._debug:
                ##################################################################
                ################LOOOOOOOOOOOOOOKKKKKKKKKKKKKK HHHEEEEEEEEEERRRRRRRREEEEEEEEE
                ######################################################################
                logger.warning(f'response url: {response.url}\n\n')
        except (requests.exceptions.ConnectTimeout, requests.exceptions.ReadTimeout):
            sys.stdout.write(f'{" "*PRINT_SPACING}Connection timed out during API call. '
                             f'Attempt {attempt+1}/{self.max_connection_attempts} failed.\n')
            if attempt < self.max_connection_attempts:
                return self.api_call(command, method, entity, entity_id, select_fields, query, body,
                                     attempt + 1, **kwargs)
            else:
                raise APICallError(f'{" "*PRINT_SPACING}interface could not establish a connection to make the '
                                   'API call.')

        response_dict = json.loads(response.text)
        if 'errorMessage' in response_dict.keys():
            raise APICallError(f'API Call resulted in an error: \n'
                               f'{response_dict}')
        else:
            return response_dict

    @depaginate_search
    def api_search(self, entity="", entity_id="", query="", sort="", select_fields="*", count=500, start=0, **kwargs):
        """
        Conducts an API search with the given parameters passed to api_call

        :param entity: (str) Bullhorn Entity that is being searched
        :param entity_id: (str, int) optional numeric id corresponding to the desired entity
        :param query: (str) string describing SQL style query, overrides entity_id
        :param select_fields: (str, list) fields returned by API response
        :param count: (str, int) number of records returned by API call, is ignored if greater than 500
        :param kwargs: (kwargs) values to be passed with AND to the query (supports equivalence only)
            * example: interface.api_search(entity="ClientCorporation", id=44) will have query="id:44"
            * example: interface.api_search(entity="ClientCorporation", query="numOffices IN [1 TO 100]", status='"Active Account"') will have query='numOffices IN [1 TO 100] AND status:"Active Account"'
        :return: (dict) hopefully a dictionary with a key called 'data' in it with a list of your desired results
        """
        if not query and entity_id:
            query = f"id:{entity_id}"

        for key, kwarg in kwargs.items():
            if '__to' in key:
                key = key.split('__to')[0]
                query += f'{" AND " if query else ""} {key}:[{kwarg[0]} TO {kwarg[1]}]'
            else:
                query += f'{" AND " if query else ""} {key}:{kwarg}'

        return self.api_call(entity=entity, select_fields=select_fields, attempt=0,
                             command="search", method="GET", query=query, count=count, start=start, sort=sort)

    @depaginate_query
    def api_query(self, entity="", where="", orderBy="", select_fields="*", **kwargs):
        """
        Conducts a Query using SQL style where clauses with the given parameters passed to api_call

        :param entity: (str) Bullhorn Entity that is being queried
        :param where: (SQL str) SQL style where clause for query
        :param select_fields: (list, str) list of fields to be selected in query
        :param kwargs: (kwargs) additional kwargs to be passed to api_call
        :return: (dict) hopefully a dictionary with a key called 'data' in it with a list of your desired results
        """
        return self.api_call(command="query", entity=entity, method="GET", select_fields=select_fields, where=where,
                             orderBy=orderBy, **kwargs)

    def api_create(self, entity="", select_fields="*", **kwargs):
        """
        Creates an entity of the specified type with the specified passed kwargs.

        :param entity: (str) desired entity type to be created
        :param select_fields: (list, str) SELECT fields to be returned by the API call
        :param kwargs: (kwarg) attributes that the created entity will have
            *ex: interface.api_create(entity="Candidate", lastName="Doe", firstName="John", name="John Doe")
        :return: (dict) hopefully a dictionary with a key called 'data' in it with info about the newly created entity
        """
        body = {**kwargs}
        return self.api_call(command="entity", entity=entity, method="CREATE", select_fields=select_fields, body=body)

    def api_delete(self, entity="", entity_id=""):
        """
        Deletes the specified entity with the specified entity_id.

        :param entity: (str) Bullhorn entity type to be deleted
        :param entity_id: (int, str) Bullhorn ID of entity to be deleted
        :return: tells you if it worked or gives an error message
        """
        if not entity_id:
            raise APICallError('You must specify an entity_id or a list of entity ids.')
        else:
            return self.api_call(command="entity", entity=entity, entity_id=f"{entity_id}", method="DELETE")

    def api_update(self, entity="", entity_id="", select_fields="*", **kwargs):
        """
        Updates the specified entity with the specified entity_id and the parameters passed as keyword objects.

        :param entity: (str) Bullhorn entity type to be updated
        :param entity_id: (int, str) Bullhorn ID of entity to be updated
        :param select_fields: (list, str) SELECT fields to be returned by the API call
        :param kwargs: attributes that the updated entity will have
            *ex: interface.api_update(entity="Candidate", entity_id=1, phone="555-555-5555")
        :return:
        """
        if not entity_id:
            raise APICallError('You must specify an entity_id or a list of entity ids.')
        body = {**kwargs}
        return self.api_call(command="entity", entity=entity, entity_id=entity_id, method="UPDATE",
                             select_fields=select_fields, body=body)

    def get_file_info(self, entity="", entity_id="", select_fields="*"):
        """

        :param entity: (str) Bullhorn entity type corresponding to the desired files
        :param entity_id: (str, int) numeric id corresponding to the desired entity
        :param select_fields: (str, list) (default is "*") fields to be returned from api_call
        :return: hopefully a dict with the key "data" with a list of a single member corresponding to the desired entityFiles
        """

        if not (entity and entity_id):
            raise APICallError('You must specify an entity type and entity id.')

        return self.api_call(entity=entity, entity_id=entity_id, select_fields=select_fields, attempt=0,
                             command="entityFiles", method="GET")

    def save_file_from_url(self, url="", path=""):
        """
        Save a file stored in bullhorn from the specified url (url can be retrieved using get_file_info)

        :param url: url pointing to desired file
        :param path: fully qualified path or file name (use forward slashes regardless of os)
            * example: path='/path/to/file.png' stores in /path/to/file.png
            * example: path='file.png' stores in /current/working/directory/file.png
        :return: None
        """
        url_format = "https://{rest_url}/file/{entity}/{entity_id}/{file_id}"
        if not url:
            raise APICallError(f"You must specify a url ({url_format}) to retrieve the file from.")

        if not path:
            path = "outfile"

        path = os.path.abspath(path)

        self.fresh()

        split_url = url.split(self.access_token["rest_url"])
        if len(split_url) == 1:
            raise APICallError(f"The rest url of the passed url string does not match the current access token. You may"
                               f"need to retrieve the url corresponding to the file again before proceeding.")
        url_identifier = url.split(self.access_token["rest_url"])[1]

        if "file" in url_identifier:
            entity = url_identifier.split("/")[1]
            entity_id = '/'.join(url_identifier.split("/")[2:])

        else:
            raise APICallError("The passed url is not in the correct format. Are you sure this URL points to a file?")

        file_content = self.api_call(command="file", entity=entity, entity_id=entity_id, method="GET")["File"][
            "fileContent"]

        with open(path, "wb") as fh:
            fh.write(base64.decodebytes(file_content.encode('utf-8')))


class LiveInterface(Interface):
    def __init__(self, *args, **kwargs):
        super(LiveInterface, self).__init__(*args, **kwargs)

    def __str__(self):
        return f'{colored(self.__class__.__name__, "green")}'

    def update_token(self, *args, **kwargs):
        self.__setattr__(args[0], kwargs)

    def get_token(self, *args, **kwargs):
        return self.__getattribute__(args[0])

    def grab_tokens(self):
        self.login()
        self.get_api_token()


class StoredInterface(Interface):
    def __init__(self, *args, **kwargs):
        super(StoredInterface, self).__init__(*args, **kwargs)

    def __str__(self):
        return f'{colored(self.__class__.__name__, "magenta")}'

    def update_token(self, *args, **kwargs):
        # put the new token in the tokenbox
        tokenbox.update_token(*args, **kwargs)

    @no_such_table_handler
    def get_token(self, *args, **kwargs):
        # get the token from the tokenbox
        token = {**tokenbox.get_token(*args, **kwargs)}
        return token

    @no_such_table_handler
    def grab_tokens(self):
        # grab both tokens from the tokenbox
        self.login_token = {**tokenbox.get_token('login_token')}
        self.access_token = {**tokenbox.get_token('access_token')}


def AND(*args, **kwargs):
    """
    Facilitates building of queries for use with api_search and api_query

    :param args: (args) query strings to be combined with AND
    :param kwargs: (kwargs) key/value pairs to be combined with AND
    :return:
    """
    qs = ''
    for arg in args:
        qs += f'{arg}'
    for key, item in kwargs.items():
        qs += f'{" AND " if qs else ""} {key}:{item}'
    qs = f'({qs})'
    return qs


def OR(*args, **kwargs):
    """
    Facilitates building of queries for use with api_search and api_query

    :param args: (args) query strings to be combined with OR
    :param kwargs: (kwargs) key/value pairs to be combined with OR
    :return:
    """
    qs = ''
    for arg in args:
        qs += f'{arg}'
        print(qs)
    for key, item in kwargs.items():
        qs += f'{" OR " if qs else ""} {key}:{item}'
    qs = f'({qs})'
    return qs


def TO(**kwargs):
    """
    Facilitates building of queries for use with api_search and api_query

    :param args: (args) query strings to be combined with OR
    :param kwargs: (kwargs) key/value pairs to be combined with OR
    :return:
    """
    qs = ''
    for key, item in kwargs.items():
        qs = f'{" AND " if qs else ""} {key}:[{item[0]} TO {item[1]}]'
    return f'({qs})'