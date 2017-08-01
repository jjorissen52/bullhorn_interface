General Setup
=============

Secrets
=======

Make sure your secrets are setup properly. ``secrets.json`` should live
in the ``settings`` directory and house a json object sufficient to
populate ``settings.py`` which looks like:

::

    import json
    import os

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(BASE_DIR, 'secrets.json')) as secrets_file:
    secrets = json.load(secrets_file)

    # Uses postgreSQL database if False, otherwise houses tokens in json files in the settings directory
    USE_FLAT_FILES = False

    CLIENT_ID = secrets.get("CLIENT_ID")
    CLIENT_SECRET = secrets.get("CLIENT_SECRET")
    EMAIL_ADDRESS = secrets.get("EMAIL_ADDRESS")
    EMAIL_PASSWORD = secrets.get("EMAIL_PASSWORD")
    DB_USER = secrets.get("DB_USER")
    DB_PASSWORD = secrets.get("DB_PASSWORD")

Environment
===========

This project was developed using Anaconda3 and therefore can be deployed
on Windows, Linux, and Unix operating systems without much fuss. Below
are instructions on how to setup the virtual environment necessary to
run a development or production server.

Windows
-------

Create environment and activate it:

.. code:: angular2html

    conda env create --file /path/to/project_root/environment.yml
    activate bullhorn3.6 

Linux
-----

Create environment and activate it:

.. code:: angular2html

    conda create -n bullhorn3.6
    source activate derek_reports
    pip install -r /path/to/project_root/requirements.txt

Database Setup
==============

If you have ``USE_FLAT_FILES = True`` you can skip this part.

Your DB\_USER must have access to the 'postgres' database on your
postgreSQL server, and must have sufficient permissions to create and
edit databases.

To create a database to house your tokens:

::

    from bullhorn.alchemy.bullhorn_db import setup_module, create_table
    setup_module(db_name='bullhorn') # db_name defaults to 'bullhorn'
    create_table() # creates the 'access_token' and 'login_token' table

If you wish to drop that database:

::

    from bullhorn.alchemy.bullhorn_db import teardown_module
    teardown_module()

Generate Login Token
====================

Use ``login()`` and follow the resulting instructions (you will have to
use your own client id and code, don't try to just copy/paste the output
below).

.. code:: angular2html

    from bullhorn.api import login
    login()

Response:

::

    >Paste this URL into browser https://auth.bullhornstaffing.com/oauth/authorize?client_id={YOUR CLIENT ID}&response_type=code.
    Redirect URL will look like this: http://www.bullhorn.com/?code={YOUR CODE WILL BE RIGHT HERE}&client_id={client_id}.

.. code:: angular2html

    login(code="{YOUR CODE WILL BE RIGHT HERE}")

Response:

::

    >New Access Token: {YOUR ACCESS TOKEN}

If ``USE_FLAT_FILES = True``, your login token will be stored in
``bullhorn/settings/login_token.json``. Otherwise, it will be stored in
the database of your designation in the table ``login_token``.

Refresh Token
=============

You will need to refresh your Login Token at least every 10 minutes.
Valid tokens can be refreshed with valid refresh tokens indefinitely;
however, *once you refresh a token the old one will be invalidated, and
if you somehow lose the new token you will need to generate your login
token again.*

It is VERY IMPORTANT that no one with malicious intent can gain access
to your valid login\_token/refresh\_token combination. Take great care
to ensure that your tokens remain a secret.

To refresh:

.. code:: angular2html

    from bullhorn.api import refresh_token
    refresh_token()

Response:

.. code:: angular2html

    'New Access Token: {NEW ACCESS TOKEN}'

Generate API Token
==================

Once you've been granted a login token from the previous steps, you can
get a token and url for the rest API.

.. code:: angular2html

    from bullhorn.api import get_api_token
    get_api_token()

Response:

.. code:: angular2html

    >"bh_rest_token": "{YOUR BULLHORN REST TOKEN}",
    >"rest_url": "https://rest32.bullhornstaffing.com/rest-services/{CORP ID}/"

Note: you may only generate an API Token with a given Login Token once. If your API Token expires, refresh your login token before attempting to generate another API Token.
----------------------------------------------------------------------------------------------------------------------------------------------------------------------------

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
-------------

By default, ``api_call()`` will do a search on the candidate
corresponding to ``id:1`` and return the API response object. It will
refresh your tokens automatically.

For testing purposes, ``api_call()`` is equivalent to

.. code:: angular2html

    api_call(command="search", entity="Candidate", query="id:1",
             select_fields=["id", "firstName", "middleName", "lastName", "comments", "notes(*)"],
             auto_refresh=True)

``api_call()`` is a good way to test whether your setup was successful.

.. code:: angular2html

    from bullhorn.api import api_call
    api_call()

Response:

::

    >Refreshing Access Tokens
    >{'total': 1, 'start': 0, 'count': 1, 'data': [{'id': 424804, 'firstName': 'John-Paul', 'middleName': 'None', 'lastName': 'Jorissen', 'comments': 'I am a comment to be appended.', 'notes': {'total': 0, 'data': []}, '_score': 1.0}]}

Candidate ID (and comments) by first and last name
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: angular2html

    first_name, last_name = "John-Paul", "Jorissen"

    def get_candidate_id(first_name, last_name, auto_refresh=True):
           return api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                           query=f"firstName:{first_name} AND lastName:{last_name}", auto_refresh=auto_refresh)

    candidate = get_candidate_id(first_name, last_name, auto_refresh=True)['data']
    print(candidate)

Response:

::

    [{'id': 424804, 'comments': 'I am a comment to be appended.', '_score': 1.0}, {'id': 425025, 'comments': '', '_score': 1.0}]

Update a Candidate's comments
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: angular2html

    candidate_id = candidate[0]['id']
    comments = 'I am the new comment'
    body = {"comments": comments}
    api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")

Response:

.. code:: angular2html

    >Refreshing Access Tokens
    >{'changedEntityType': 'Candidate', 'changedEntityId': 424804, 'changeType': 'UPDATE', 'data': {'comments': 'I am the new comment'}}

.. code:: angular2html

    print(get_candidate_id(first_name, last_name, auto_refresh=True)['data'])

Response:

::

    Refreshing Access Tokens
    [{'id': 425025, 'comments': '', '_score': 1.0}, {'id': 424804, 'comments': 'I am the new comment', '_score': 1.0}]