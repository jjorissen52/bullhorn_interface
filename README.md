
# Setup

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

<a id="configuration"></a>
## Configuration

There needs to be a file named `bullhorn_interface.conf` that looks like this somewhere on your system:


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
# this cannot be run in jupyter notebooks, sadly.
from bullhorn_interface import tests
tests.run()
```

If you changed your configuration file you must reload `bullhorn_interface` to make these changes propogate.


```python
import importlib
from bullhorn_interface import api, tests
importlib.reload(api)
importlib.reload(tests)
```




    <module 'bullhorn_interface.tests' from '/home/jjorissen/Projects/bullhorn_interface/bullhorn_interface/tests.py'>



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

# Interface Creation
`bullhorn_interface` interacts will Bullhorn's API using `Interface` objects. 
* [`LiveInterface`](#liveinterface) keeps tokens on itself. These guys should always be created as `independent`, as `LiveInterface` objects are capable of refreshing expired tokens only for themselves.
<a id="storedinterface_reasons"></a>
* [`StoredInterface`](#storedinterface) keeps tokens on itself and also checks tokens in the database before allowing a refresh to happen. This allows you to use the same token among many interfaces in case you need to have many running at once. 
    * Bullhorn doesn't seem to mind if you have numerous API logins running simultaneously, so there isn't much utility to the `StoredInterface` object. However, in the case where you are creating new `Interface` objects frequently, using an [`independent`](#independent_explanation) stored interface will keep you from having to wait on unnecessary `login()` calls. 

<a id="liveinterface"></a>
## Using LiveInterface

### Generate Login Token


```python
from bullhorn_interface import api
interface = api.LiveInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
interface.login()
```

        New Login Token


### Generate API Token
Once you've been granted a login token, you can get a token and url for the rest API.


```python
interface.get_api_token()
```

        New Access Token


### Make API Calls


```python
# Gets info of Cndidate with id:1
interface.api_call()
```




    {'count': 0, 'data': [], 'start': 0, 'total': 0}



If you got something that looks like the above then you are all configured. If you want to know what some queries with real data will look like feel free to play with the below:


```python
first, last = "John-Paul", "Jorissen"
qs = f"firstName:{first} AND lastName:{last}"
interface.api_call(query=qs)['data'][0]
```




    {'_score': 1.0,
     'comments': '',
     'firstName': 'John-Paul',
     'id': 425082,
     'lastName': 'Jorissen',
     'middleName': None,
     'notes': {'data': [], 'total': 0}}



## Using StoredInterface

If you for [some reason](#storedinterface_reasons) need (or want) to keep your tokens stored in a database, you can use the stored interface.


```python
interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
```

You interact with everything the same way as the `LiveInterface` setup.


```python
interface.login()
interface.get_api_token()
interface.refresh_token()
interface.api_call()
```

        New Login Token
        New Access Token





    {'count': 0, 'data': [], 'start': 0, 'total': 0}



<a id="independent_explanation"></a>
There is one difference here, however. You can make your `StoredInterface` objects independent. This means that they will not login or refresh tokens on their own; they will instead be relying on a lead `StoredInterface` to keep tokens fresh. For a demonstration run 1 and 2 in separate python command prompts.


```python
from bullhorn_interface import api
first, last = "John-Paul", "Jorissen"
qs = f"firstName:{first} AND lastName:{last}"
lead_interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
dependent_interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD, 
                                             independent=False)
lead_interface.login()
lead_interface.get_api_token()
# using the tokens that lead_interface aquired
dependent_interface.api_call(query=qs)
# forcing the dependent interface to think the token on its person has expired
dependent_interface.login_token['expiry'] = 0
# the interface will now check itself and find that it's token has expired. after the first failure, it will 
# check the database to see if an independent interface has put in a token that has not expired.
dependent_interface.api_call(query=qs)['data'][0]
```

        New Login Token
        New Access Token
        Token Expired. Attempt 1/10 failed.





    {'_score': 1.0,
     'comments': '',
     'firstName': 'John-Paul',
     'id': 425082,
     'lastName': 'Jorissen',
     'middleName': None,
     'notes': {'data': [], 'total': 0}}



# API Parameters
Now with your interfaces in order, you can make API calls. This will all be done with `interface.api_call`. You'll need to look over the Bullhorn API Reference Material to know what the heck everything below is about.

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

For testing purposes, `api_call()` with no passed arguments is equivalent to


```python
api_call(command="search", entity="Candidate", query="id:1",
         select_fields="id, firstName, middleName, lastName, comments, notes(*)",
         auto_refresh=True)
```

##### Get Candidate IDs (and comments) by first and last name


```python
first_name, last_name = "John-Paul", "Jorissen"

def get_candidate_id(first_name, last_name):
       return interface.api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                       query=f"firstName:{first_name} AND lastName:{last_name}")

candidate = get_candidate_id(first_name, last_name)['data']
print(list(filter(lambda x: x['id'] == 425084, candidate)))
```

    [{'id': 425084, 'comments': 'I am the old comment', '_score': 1.0}]


##### Update a Candidate's comments


```python
candidate_id = 425084
comments = 'I am the new comment'
body = {"comments": comments}
interface.api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")
```




    {'changeType': 'UPDATE',
     'changedEntityId': 425084,
     'changedEntityType': 'Candidate',
     'data': {'comments': 'I am the new comment'}}




```python
print(list(filter(lambda x: x['id'] == 425084, get_candidate_id(first_name, last_name)['data'])))
```

    [{'id': 425084, 'comments': 'I am the new comment', '_score': 1.0}]

