
# Setup

# Version 2 Is Undocumented. The information below refers to the distribution released before version 2 to install version this documentation refers to:

```
pip install bullhorn_interface==1.3.0.dev0
```

## Environment

#### Linux
Create environment using anaconda or whatever and activate it:


```python
conda create -n bullhorn3.6
source activate bullhorn3.6
pip install -r /path/to/project_root/requirements.txt
```


#### Windows (Anaconda)
Same as above, but you will need to perform


```python
conda install psycopg2
conda install sqlalchemy
```

afterwards, as there are some dependencies that Anaconda has to work out to make these packages work on Windows. I highly recommend you use Anaconda in windows, as it will handle all the nasty c bits that numerous python packages require.

## Configuration and Secrets

There should be a file named `bullhorn_interface.conf` that looks like this somewhere on your system:


```python
[bullhorn_interface]
TOKEN_HANDLER = [pick from 'live', 'pg', or 'sqlite']
CLIENT_ID = client_id
CLIENT_SECRET = client_secret
BULLHORN_USERNAME = username
BULLHORN_PASSWORD = password
EMAIL_ADDRESS = email@email.com
EMAIL_PASSWORD = password
DB_NAME = bullhorn_box
DB_HOST = localhost
DB_USER = db_user
DB_PASSWORD = password
```

If this file lives in your working directory you are good to go. If not, you will need to set an environment variable to the full path of this file.

#### Linux


```python
export INTERFACE_CONF_FILE=/home/jjorissen/bullhorn_secrets.conf
```

#### Windows


```python
set INTERFACE_CONF_FILE=/full/path/to/bullhorn_secrets.conf
```

To test your configuration you can do:
##### Note: you should visit the Database Setup section first if you are using Postgres


```python
from bullhorn_interface import tests
tests.api_test()
```

If you changed your configuration file you must reload `bullhorn_interface` to make these changes propogate.


```python
import importlib
from bullhorn_interface import api, tests
importlib.reload(api)
importlib.reload(tests)
```

We can check to see if this worked by looking at the database connection string in `bullhorn_db`.


```python
from bullhorn_interface.api import tokenbox
tokenbox.connection_strings["pg_conn_uri_new"]
```




    'postgresql://jjorissen:the-str0ng35t-0v-p455w0rd5@localhost:5432/bullhorn'



# Using Postgres or SQLite

## Database Setup
#### Note: If you are using PG, your `DB_USER` must have access to the 'postgres' database on your postgreSQL server, and must have sufficient permissions to create and edit databases. 
To create a database to house your tokens:


```python
from bullhorn_interface.api import tokenbox
tokenbox.create_database() 
```

    bullhorn_box created successfully.


If you wish to drop that database for some reason:


```python
tokenbox.destroy_database()
```

    Database named bullhorn_box will be destroyed in 5...4...3...2...1...0
    bullhorn_box dropped successfully.


It's that easy. The necessary tables will be created automatically when the tokens are generated for the first time, so don't sweat anything! For more information on using `tokenbox`, visit the [repo](https://github.com/jjorissen52/tokenbox).

## Generate Login Token
Simply call `login()` with a valid username/password combination.


```python
from bullhorn_interface import api
api.login(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
```


```python
'New Access Token: {NEW ACCESS TOKEN}'
```

If you don't want to store your credentials in a script or text file, use `login()` and follow the resulting instructions (you will have to use your own client id and code,
don't try to just copy/paste the output below).


```python
api.login()
```

    Paste this URL into browser https://auth.bullhornstaffing.com/oauth/authorize?client_id=IAMYOURBULLHORNID&response_type=code. 
    Redirect URL will look like this: http://www.bullhorn.com/?code={YOUR CODE WILL BE RIGHT HERE}&client_id=IAMYOURBULLHORNID.
    



```python
api.login(code="{YOUR CODE WILL BE RIGHT HERE}")
```


```python
'New Access Token: {NEW ACCESS TOKEN}'
```

## Generate API Token
Once you've been granted a login token from the previous steps, you can get a token and url for the rest API.


```python
api.get_api_token()
```


```python
"bh_rest_token": "{YOUR BULLHORN REST TOKEN}",

"rest_url": "https://rest32.bullhornstaffing.com/rest-services/{CORP ID}/"
```

##### Note: you may only generate an API Token with a given Login Token once. If your API Token expires, you must login again before attempting to generate another API Token

## Test Your Configuration


```python
from bullhorn_interface import api
api.api_call()
```

    Refreshing Access Tokens





    {'count': 0, 'data': [], 'start': 0, 'total': 0}



If you got something that looks like the above or some actual data then you are all configured! Now you can use the API for whatever you need.

# Using Live

If you have no need to store your tokens in a database, you can just store your tokens in an object temporarily.


```python
interface = api.LiveInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
```

Everything works the same as the database setup except now you are calling the API function as methods from the `LiveInterface` object. Keep this in mind when you are reading the `Usage` section below.


```python
interface.login()
interface.get_api_token()
interface.refresh_token()
print(interface.api_call())
```

# Usage
Now with all of your tokens in order, you can make API calls. This will all be done with `api.api_call`. You'll need to look over the Bullhorn API Reference Material to know what the heck everything below is about.

* [API Reference](http://bullhorn.github.io/rest-api-docs/)
* [Entity Guide](http://bullhorn.github.io/rest-api-docs/entityref.html)

`api_call` key-word arguments:

* `command` (`str`) designates which Bullhorn API command type is being used. Valid options are
	* `command="search"` 
		* Will return default fields unless `select_fields` is set
	* `command="query"`
		* Will return default fields unless `select_fields` is set
		* Must designate a where clause using `kwargs={'where': WHERE_CLAUSE}`
		* Can designate other API parameters using `kwargs` such as `kwargs={. . ., 'orderBy': 'id'}`
	* `command="entity"`
		* Must be used in conjunction with approprate `method`, `entity`, and `query` or `entity_id`.
* `query` (`str`) allows you to designate an SQL style `WHERE` clause when using `command="search"`.
* `entity` (`str`) designates which [type of entity](http://bullhorn.github.io/rest-api-docs/entityref.html) will be selected, created, or updated.
	* Must use `method="CREATE"` or `method="UPDATE"` or `method="GET"`.
* `method` (`str`) designates which HTTP method will be used to carry out the request. `"UPDATE"` corresponds to `POST`, `"CREATE"` corresponds to `PUT`, and `"GET"` corresponds to `GET`. It is unnecessary to specify `method` for `command="seach"` or `command="query"`, but it is necessary to specify `method` for `command="entity"`.
* `entity_id` (`str`) designates the id of the desired entity if `query` is not set.
* `select_fields` (`str` or `list`) designates which bullhorn fields will be present in the API response.
    * `select_fields=["id", "firstName", "middleName", "lastName", "comments", "notes(*)"]`
    * `select_fields="id, firstName, middleName, lastName, comments, notes(*)"`
* `body` allows you to pass a request body. This is necessary when updating or creating an entity, for example.
*  `auto_refresh` (`bool`) defaults to `True`. This argument designates whether or you wish to extend the lifetime of your tokens before carrying out the API call. If you set this to `False` (because refreshing tokens is time consuming), you will need to implement your own logic to ensure that your tokens are being refreshed at least every ten minutes.

Any other keyword arguemnts will be passed as API parameters when making an API call.


## Example Usage
By default, `api_call()` will do a search on the candidate corresponding to `id:1` and return the API response object. It will refresh your tokens automatically.

For testing purposes, `api_call()` is equivalent to


```python
api_call(command="search", entity="Candidate", query="id:1",
         select_fields="id, firstName, middleName, lastName, comments, notes(*)",
         auto_refresh=True)
```

`api_call()` is a good way to test whether your setup was successful.


```python
api.api_call()
```


```python
Refreshing Access Tokens

{'total': 1, 'start': 0, 'count': 1, 'data': [{'id': 424804, 'firstName': 'John-Paul', 'middleName': 'None', 'lastName': 'Jorissen', 'comments': 'I am a comment to be appended.', 'notes': {'total': 0, 'data': []}, '_score': 1.0}]}
```

##### Get Candidate IDs (and comments) by first and last name


```python
first_name, last_name = "John-Paul", "Jorissen"

def get_candidate_id(first_name, last_name, auto_refresh=True):
       return api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                       query=f"firstName:{first_name} AND lastName:{last_name}", auto_refresh=auto_refresh)

candidate = get_candidate_id(first_name, last_name, auto_refresh=True)['data']
print(candidate)
```


```python
[{'id': 424804, 'comments': 'I am a comment to be appended.', '_score': 1.0}, {'id': 425025, 'comments': '', '_score': 1.0}]
```

##### Update a Candidate's comments


```python
candidate_id = candidate[0]['id']
comments = 'I am the new comment'
body = {"comments": comments}
api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")
```


```python
Refreshing Access Tokens
{'changedEntityType': 'Candidate', 'changedEntityId': 424804, 'changeType': 'UPDATE', 'data': {'comments': 'I am the new comment'}}
```


```python
print(get_candidate_id(first_name, last_name, auto_refresh=True)['data'])
```


```python
Refreshing Access Tokens

[{'id': 425025, 'comments': '', '_score': 1.0}, {'id': 424804, 'comments': 'I am the new comment', '_score': 1.0}]
```
