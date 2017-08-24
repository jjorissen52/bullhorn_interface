import datetime
import json
import requests
import urllib
from operator import xor

from bullhorn_interface.alchemy.bullhorn_db import insert_token, select_token
from bullhorn_interface.settings.settings import CLIENT_ID, CLIENT_SECRET


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
            insert_token('login_token', login_token, )
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
            insert_token('login_token', login_token, )
            print(f"New Access Token: {login_token['access_token']}")
        except KeyError:
            print(f'Response from API: {login_token}')
            print(f'Is your token expired? Are your secrets properly configured?')


def refresh_token():

    for row in select_token('login_token'):
        tokens = row
        break

    url = "https://auth.bullhornstaffing.com/oauth/token?grant_type=refresh_token"
    url = url + f"&refresh_token={tokens['refresh_token']}&client_id={CLIENT_ID}"
    url = url + f"&client_secret={CLIENT_SECRET}"
    response = requests.post(url)
    login_token = json.loads(response.text)
    login_token['expiry'] = datetime.datetime.now().timestamp() + login_token["expires_in"]
    insert_token('login_token', login_token, )
    return f"New Access Token: {login_token['access_token']}"


def get_api_token():

    for row in select_token('login_token'):
        login_token = row
        break

    url = f"https://rest.bullhornstaffing.com/rest-services/login?version=*&access_token={login_token['access_token']}"
    response = requests.get(url)
    temp_token = json.loads(response.text)
    access_token = {"bh_rest_token": temp_token["BhRestToken"], "rest_url": temp_token["restUrl"]}
    insert_token('access_token', access_token, )
    return json.dumps(access_token, indent=2, sort_keys=True)


def api_call(command="search", method="", entity="", entity_id="",
             select_fields=[], query="",
             auto_refresh=True, body="", kwargs={}):

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

    for row in select_token('access_token'):
        access_token = row
        break

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