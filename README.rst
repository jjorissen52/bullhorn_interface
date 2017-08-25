
Setup
=====

Environment
===========

I prefer to use Anaconda for all of my python needs as it does a good
job of handling packages and virtual environments for you. You can use
whatever you like, of course.

Linux
-----

Create environment and activate it:

.. code:: ipython3

    conda create -n bullhorn3.6
    source activate bullhorn3.6
    pip install -r /path/to/project_root/requirements.txt

Windows
=======

Same as above, but you will need to perform

.. code:: ipython3

    conda install psycopg2
    conda install sqlalchemy

afterwards, as there are some dependencies that Anaconda has to work out
to make these packages work on Windows.

Configuration and Secrets
=========================

Configuration and secrets files by the names of ``conf.py`` and
``bullhorn_secrets.py`` already exist in
``/bullhorn_interface/settings/``, and they are capable of passing
``bullhorn_interface.tests.valid_conf_test()``. However, to use any
functionality of the API, you must change the default configuration.

The first time you ever import the package, you will be asked to provide
configuration.

.. code:: ipython3

    import bullhorn_interface


.. parsed-literal::

    Would you like to use an SQLite or PostgreSQL database for token storage? 
    	1: PostgreSQL Database
    	2: SQLite Database (Default)
    
    Note: PostgreSQL is really only necessary for high concurrency; SQLite will suffice in most use cases.
    1
    1 selected.
    Would you like to: 
    	1: Create a new file named secrets.json and store it in a specified path?
    	2: Specify the full path of an existing secrets file?
    2
    2 selected. Please specify the name of your secrets file (/path/to/secrets.json): /home/jjorissen/bullhorn_secrets.json


You can modify these configurations at any time.

.. code:: ipython3

    from bullhorn_interface.settings import settings
    settings.InterfaceSettings.set_conf()


.. parsed-literal::

    Would you like to use an SQLite or PostgreSQL database for token storage? 
    	1: PostgreSQL Database
    	2: SQLite Database (Default)
    
    Note: PostgreSQL is really only necessary for high concurrency; SQLite will suffice in most use cases.
    1
    1 selected.


.. code:: ipython3

    settings.InterfaceSettings.set_secrets()


.. parsed-literal::

    Would you like to: 
    	1: Create a new file named secrets.json and store it in a specified path?
    	2: Specify the full path of an existing secrets file?
    2
    2 selected. Please specify the name of your secrets file (/path/to/secrets.json): /home/jjorissen/bullhorn_secrets.json


Let's quickly check those configurations.

.. code:: ipython3

    from bullhorn_interface.settings import settings
    settings.InterfaceSettings.load_conf()




.. parsed-literal::

    {'SECRETS_LOCATION': '/home/jjorissen/bullhorn_secrets.json',
     'USE_FLAT_FILES': True}



.. code:: ipython3

    settings.InterfaceSettings.load_secrets()




.. parsed-literal::

    {'CLIENT_ID': 'IAMYOURBULLHORNID',
     'CLIENT_SECRET': 'sasdjfhalksjdflaksjd',
     'DB_PASSWORD': 'asdflkjahsdflkjhalsjdk',
     'DB_USER': 'your_postgres_user',
     'EMAIL_ADDRESS': 'youremail@gmail.com',
     'EMAIL_PASSWORD': 'alsdjhfalskjhlakjshfd'}



Start a new python console or reload all of the modules so that the
changed configurations will propogate.

.. code:: ipython3

    import importlib
    from bullhorn_interface.settings import settings
    from bullhorn_interface import api, tests
    importlib.reload(settings)
    importlib.reload(api)
    importlib.reload(tests)




.. parsed-literal::

    <module 'bullhorn_interface.tests' from '/home/jjorissen/anaconda3/envs/bullhorn3.6/lib/python3.6/site-packages/bullhorn_interface/tests.py'>



We can check to see if this worked by looking at the database connection
string in ``bullhorn_db``.

.. code:: ipython3

    from bullhorn_interface.api import tokenbox
    tokenbox.connection_strings["pg_conn_uri_new"]




.. parsed-literal::

    'postgresql://jjorissen:the-str0ng35t-0v-p455w0rd5@localhost:5432/bullhorn'



Database Setup
==============

If you are configured for SQLite you can skip this bit.

Your ``DB_USER`` must have access to the 'postgres' database on your
postgreSQL server, and must have sufficient permissions to create and
edit databases. To create a database to house your tokens:

.. code:: ipython3

    from bullhorn_interface.api import tokenbox
    tokenbox.create_database() # creates a new database named bullhorn_box


.. parsed-literal::

    bullhorn_box created successfully.


If you wish to drop that database for some reason:

.. code:: ipython3

    tokenbox.destroy_database()


.. parsed-literal::

    Database named bullhorn_box will be destroyed in 5...4...3...2...1...0
    bullhorn_box dropped successfully.


It's that easy. The necessary tables will be created automatically when
the tokens are generated for the first time, so don't sweat anything!
For more information on using ``tokenbox``, visit the `repo
page <https://github.com/jjorissen52/tokenbox>`__.

Generate Login Token
====================

Simply call ``login()`` with a valid username/password combination.

.. code:: ipython3

    from bullhorn_interface import api
    api.login(username="valid_username", password="valid_password")

.. code:: ipython3

    'New Access Token: {NEW ACCESS TOKEN}'

If you don't want to store your credentials in a script or text file,
use ``login()`` and follow the resulting instructions (you will have to
use your own client id and code, don't try to just copy/paste the output
below).

.. code:: ipython3

    api.login()


.. parsed-literal::

    Paste this URL into browser https://auth.bullhornstaffing.com/oauth/authorize?client_id=IAMYOURBULLHORNID&response_type=code. 
    Redirect URL will look like this: http://www.bullhorn.com/?code={YOUR CODE WILL BE RIGHT HERE}&client_id=IAMYOURBULLHORNID.
    


.. code:: ipython3

    api.login(code="{YOUR CODE WILL BE RIGHT HERE}")

.. code:: ipython3

    'New Access Token: {NEW ACCESS TOKEN}'

Generate API Token
==================

Once you've been granted a login token from the previous steps, you can
get a token and url for the rest API.

.. code:: ipython3

    api.get_api_token()

.. code:: ipython3

    "bh_rest_token": "{YOUR BULLHORN REST TOKEN}",
    
    "rest_url": "https://rest32.bullhornstaffing.com/rest-services/{CORP ID}/"

Note: you may only generate an API Token with a given Login Token once. If your API Token expires, you must login again before attempting to generate another API Token
=======================================================================================================================================================================

Test Your Configuration (Drumroll...)
=====================================

.. code:: ipython3

    from bullhorn_interface import api
    api.api_call()


.. parsed-literal::

    Refreshing Access Tokens




.. parsed-literal::

    {'count': 0, 'data': [], 'start': 0, 'total': 0}



If you got something that looks like the above or some actual data then
you are all configured! Now you can use the API for whatever you need.

Usage
=====

Now with all of your tokens in order, you can make API calls. This will
all be done with ``api.api_call``. You'll need to look over the Bullhorn
API Reference Material to know what the heck everything below is about.

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

   -  ``select_fields=["id", "firstName", "middleName", "lastName", "comments", "notes(*)"]``
   -  ``select_fields="id, firstName, middleName, lastName, comments, notes(*)"``

-  ``body`` allows you to pass a request body. This is necessary when
   updating or creating an entity, for example.
-  ``auto_refresh`` (``bool``) defaults to ``True``. This argument
   designates whether or you wish to extend the lifetime of your tokens
   before carrying out the API call. If you set this to ``False``
   (because refreshing tokens is time consuming), you will need to
   implement your own logic to ensure that your tokens are being
   refreshed at least every ten minutes.

Any other keyword arguemnts will be passed as API parameters when making
an API call.

Example Usage
=============

By default, ``api_call()`` will do a search on the candidate
corresponding to ``id:1`` and return the API response object. It will
refresh your tokens automatically.

For testing purposes, ``api_call()`` is equivalent to

.. code:: ipython3

    api_call(command="search", entity="Candidate", query="id:1",
             select_fields="id, firstName, middleName, lastName, comments, notes(*)",
             auto_refresh=True)

``api_call()`` is a good way to test whether your setup was successful.

.. code:: ipython3

    api.api_call()

.. code:: ipython3

    Refreshing Access Tokens
    
    {'total': 1, 'start': 0, 'count': 1, 'data': [{'id': 424804, 'firstName': 'John-Paul', 'middleName': 'None', 'lastName': 'Jorissen', 'comments': 'I am a comment to be appended.', 'notes': {'total': 0, 'data': []}, '_score': 1.0}]}

Get Candidate IDs (and comments) by first and last name
=======================================================

.. code:: ipython3

    first_name, last_name = "John-Paul", "Jorissen"
    
    def get_candidate_id(first_name, last_name, auto_refresh=True):
           return api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                           query=f"firstName:{first_name} AND lastName:{last_name}", auto_refresh=auto_refresh)
    
    candidate = get_candidate_id(first_name, last_name, auto_refresh=True)['data']
    print(candidate)

.. code:: ipython3

    [{'id': 424804, 'comments': 'I am a comment to be appended.', '_score': 1.0}, {'id': 425025, 'comments': '', '_score': 1.0}]

Update a Candidate's comments
=============================

.. code:: ipython3

    candidate_id = candidate[0]['id']
    comments = 'I am the new comment'
    body = {"comments": comments}
    api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")

.. code:: ipython3

    Refreshing Access Tokens
    {'changedEntityType': 'Candidate', 'changedEntityId': 424804, 'changeType': 'UPDATE', 'data': {'comments': 'I am the new comment'}}

.. code:: ipython3

    print(get_candidate_id(first_name, last_name, auto_refresh=True)['data'])

.. code:: ipython3

    Refreshing Access Tokens
    
    [{'id': 425025, 'comments': '', '_score': 1.0}, {'id': 424804, 'comments': 'I am the new comment', '_score': 1.0}]

