
Setup
=====

Environment
===========

Linux
-----

Create environment and activate it:

conda create -n bullhorn3.6
source activate bullhorn3.6
pip install -r /path/to/project_root/requirements.txt

Windows
=======

Same as above, but you will need to perform

conda install psycopg2
conda install sqlalchemy

afterwards.

Configuration and Secrets
=========================

Configuration and secrets files by the names of ``conf.py`` and
``bullhorn_secrets.py`` already exist in
``/bullhorn_interface/settings/``, and they are capable of passing
``bullhorn_interface.tests.valid_conf_test()``. These initial
configurations will allow you to:

::

    1) Login
    2) Store Login and Access Tokens
    3) Make API calls one at a time

However, the default configurations will not allow you to:

::

    1) Make multiple concurrent API calls
    2) Send emails using `bullhorn_interface.helpers.send_email()`

Let's do some tests to make sure things are behaving how they are
supposed to.

.. code:: ipython3

    import os
    from bullhorn_interface import tests

.. code:: ipython3

    tests.valid_conf_test()


.. parsed-literal::

    Test Passed.


If your test passed,that means your ``conf.py`` and
``bullhorn_secrets.py`` files are being read without issue.If your use
case allows your to proceed with the stated limitations of the default
configurations, you can skip straight to the section about usage.

Now lets modify our configuration and secrets files. If we want the
ability the make multiple concurrent API calls, we need to tell the conf
to use a database and will need to set up a PostgreSQL database to store
our Login and Access Tokens.

.. code:: ipython3

    from bullhorn_interface import helpers, settings
    helpers.set_conf()


.. parsed-literal::

    Would you like to store your access tokens and login tokens in flat files
    or in a postgreSQL database?
    	1: PostgreSQL Database
    	2: Flat Files (Default)

    Note: Flat files may experience concurrency problems when making simultaneous API calls.
    1
    1 selected.


We will also have to modify our secrets file.

.. code:: ipython3

    os.getcwd()




.. parsed-literal::

    '/home/jjorissen'



.. code:: ipython3

    helpers.set_secrets()


.. parsed-literal::

    Would you like to:
    	1: Create a new file named bullhorn_secrets.py and store it in a specified path?
    	2: Specify the full path of an existing secrets file?
    1
    1 selected. Please specify the full path containing your secrets file: (/path/containing/secrets/)/home/jjorissen
    Please input your Bullhorn Client ID for API development: IAMYOURBULLHORNID
    Bullhorn Client Secret: ········
    Default gmail address for Bullhorn API Interface used in helpers.send_mail(): youremail@gmail.com
    Default gmail passwrd for Bullhorn API Interface used in helpers.send_mail(): ········
    PostgreSQL database login role username. (Database used to store access and API tokens): your_postgres_user
    PostgreSQL database login role password. (Database used to store access and API tokens): ········


Let's quickly check those configurations.

.. code:: ipython3

    settings.settings.load_conf()




.. parsed-literal::

    {'SECRETS_LOCATION': '/home/jjorissen/bullhorn_secrets.json',
     'USE_FLAT_FILES': False}



.. code:: ipython3

    settings.settings.load_secrets()




.. parsed-literal::

    {'CLIENT_ID': 'IAMYOURBULLHORNID',
     'CLIENT_SECRET': 'sasdjfhalksjdflaksjd',
     'DB_PASSWORD': 'asdflkjahsdflkjhalsjdk',
     'DB_USER': 'your_postgres_user',
     'EMAIL_ADDRESS': 'youremail@gmail.com',
     'EMAIL_PASSWORD': 'alsdjhfalskjhlakjshfd'}



Now we will need to reload all of the modules so that the changed
configurations will propogate.

.. code:: ipython3

    import importlib
    from bullhorn_interface.settings import settings
    from bullhorn_interface import api, helpers, tests
    from bullhorn_interface.alchemy import bullhorn_db
    importlib.reload(settings)
    importlib.reload(api)
    importlib.reload(helpers)
    importlib.reload(tests)
    importlib.reload(bullhorn_db)




.. parsed-literal::

    <module 'bullhorn_interface.alchemy.bullhorn_db' from '/home/jjorissen/anaconda3/envs/bullhorn3.6/lib/python3.6/site-packages/bullhorn_interface/alchemy/bullhorn_db.py'>



We can check to see if this worked by looking at the database connection
string in ``bullhorn_db``.

.. code:: ipython3

    bullhorn_db.DB_CONN_URI_NEW




.. parsed-literal::

    'postgresql://your_postgres_user:asdflkjahsdflkjhalsjdk@localhost:5432/bullhorn'



Database Setup
==============

If you have ``USE_FLAT_FILES = True`` you can skip this part.

Your ``DB_USER`` must have access to the 'postgres' database on your
postgreSQL server, and must have sufficient permissions to create and
edit databases.

To create a database to house your tokens:

import importlib
from bullhorn_interface.settings import settings
from bullhorn_interface import api, helpers, tests
from bullhorn_interface.alchemy import bullhorn_db
bullhorn_db.setup_module() # creates a new database named bullhorn
bullhorn_db.create_table() # creates the 'access_token' and 'login_token' table

If you wish to drop that database:

.. code:: ipython3

    bullhorn2.teardown_module()

Generate Login Token
====================

Use ``login()`` and follow the resulting instructions (you will have to
use your own client id and code, don't try to just copy/paste the output
below).

.. code:: ipython3

    api.login()


.. parsed-literal::

    Paste this URL into browser https://auth.bullhornstaffing.com/oauth/authorize?client_id=IAMYOURBULLHORNID&response_type=code.
    Redirect URL will look like this: http://www.bullhorn.com/?code={YOUR CODE WILL BE RIGHT HERE}&client_id=IAMYOURBULLHORNID.



api.login(code="{YOUR CODE WILL BE RIGHT HERE}")

'New Access Token: {NEW ACCESS TOKEN}'

Generate API Token
==================

Once you've been granted a login token from the previous steps, you can
get a token and url for the rest API.

api.get_api_token()

"bh\_rest\_token": "{YOUR BULLHORN REST TOKEN}",

"rest\_url": "https://rest32.bullhornstaffing.com/rest-services/{CORP
ID}/"

Note: you may only generate an API Token with a given Login Token once. If your API Token expires, refresh your login token before attempting to generate another API Token.
============================================================================================================================================================================

Usage
=====

Now with all of your tokens in order, you can make API calls. This will
all be done with ``api_call``. ``api_call`` uses the url formulation
outlined in the following documentation and handles the
requests/responses for you. Bullhorn API Reference Material.

-  `API Reference <http://bullhorn.github.io/rest-api-docs/>`__
-  `Entity
   Guide <http://bullhorn.github.io/rest-api-docs/entityref.html>`__

``api_call`` key-word arguments:

-  ``command`` (``str``) designates which Bullhorn API command type is
   being used. Valid options are

   -  ``command="search"``

      -  Will return default fields unless ``select_fields`` is set

   -  ``command="query"``

      -  Will return default fields unless ``select_fields`` is set
      -  Must designate a where clause using
         ``kwargs={'where': WHERE_CLAUSE}``
      -  Can designate other API parameters using ``kwargs`` such as
         ``kwargs={. . ., 'orderBy': 'id'}``

   -  ``command="entity"``

      -  Must be used in conjunction with approprate ``method``,
         ``entity``, and ``query`` or ``entity_id``.

-  ``query`` (``str``) allows you to designate an SQL style ``WHERE``
   clause when using ``command="search"``.
-  ``entity`` (``str``) designates which `type of
   entity <http://bullhorn.github.io/rest-api-docs/entityref.html>`__
   will be selected, created, or updated.

   -  Must use ``method="CREATE"`` or ``method="UPDATE"`` or
      ``method="GET"``.

-  ``method`` (``str``) designates which HTTP method will be used to
   carry out the request. ``"UPDATE"`` corresponds to ``POST``,
   ``"CREATE"`` corresponds to ``PUT``, and ``"GET"`` corresponds to
   ``GET``. It is unnecessary to specify ``method`` for
   ``command="seach"`` or ``command="query"``, but it is necessary to
   specify ``method`` for ``command="entity"``.
-  ``entity_id`` (``str``) designates the id of the desired entity if
   ``query`` is not set.
-  ``select_fields`` (``str`` or ``list``) designates which bullhorn
   fields will be present in the API response.
-  ``body`` allows you to pass a request body. This is necessary when
   updating or creating an entity, for example.
-  ``auto_refresh`` (``bool``) defaults to ``True``. This argument
   designates whether or you wish to update your Login Token and API
   Token before carrying out the API call. If you set this to ``False``
   (because refreshing tokens is time consuming), you will need to
   implement your own logic to ensure that your tokens are being
   refreshed at least every ten minutes.
-  ``kwargs`` (``dict``) allows you to pass any additional necessary API
   parameters when making an API call.

Example Usage
=============

By default, ``api_call()`` will do a search on the candidate
corresponding to ``id:1`` and return the API response object. It will
refresh your tokens automatically.

For testing purposes, ``api_call()`` is equivalent to

api_call(command="search", entity="Candidate", query="id:1",
         select_fields=["id", "firstName", "middleName", "lastName", "comments", "notes(*)"],
         auto_refresh=True)

``api_call()`` is a good way to test whether your setup was successful.

api.api_call()

Refreshing Access Tokens

{'total': 1, 'start': 0, 'count': 1, 'data': [{'id': 424804,
'firstName': 'John-Paul', 'middleName': 'None', 'lastName': 'Jorissen',
'comments': 'I am a comment to be appended.', 'notes': {'total': 0,
'data': []}, '\_score': 1.0}]}

Candidate ID (and comments) by first and last name
==================================================

first_name, last_name = "John-Paul", "Jorissen"

def get_candidate_id(first_name, last_name, auto_refresh=True):
       return api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                       query=f"firstName:{first_name} AND lastName:{last_name}", auto_refresh=auto_refresh)

candidate = get_candidate_id(first_name, last_name, auto_refresh=True)['data']
print(candidate)

[{'id': 424804, 'comments': 'I am a comment to be appended.', '\_score':
1.0}, {'id': 425025, 'comments': '', '\_score': 1.0}]

Update a Candidate's comments
=============================

candidate_id = candidate[0]['id']
comments = 'I am the new comment'
body = {"comments": comments}
api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")

Refreshing Access Tokens {'changedEntityType': 'Candidate',
'changedEntityId': 424804, 'changeType': 'UPDATE', 'data': {'comments':
'I am the new comment'}}

print(get_candidate_id(first_name, last_name, auto_refresh=True)['data'])

Refreshing Access Tokens

[{'id': 425025, 'comments': '', '\_score': 1.0}, {'id': 424804,
'comments': 'I am the new comment', '\_score': 1.0}]