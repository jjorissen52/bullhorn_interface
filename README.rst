
    ::


        ########:: ##:::: ##: ##::::::: ##::::::: ##:::: ##:: #######:: ########:: ##::: ##:::::::::::::
        ##.... ##: ##:::: ##: ##::::::: ##::::::: ##:::: ##:'##.... ##: ##.... ##: ###:: ##:::::::::::::
        ##:::: ##: ##:::: ##: ##::::::: ##::::::: ##:::: ##: ##:::: ##: ##:::: ##: ####: ##:::::::::::::
        ########:: ##:::: ##: ##::::::: ##::::::: #########: ##:::: ##: ########:: ## ## ##:::::::::::::
        ##.... ##: ##:::: ##: ##::::::: ##::::::: ##.... ##: ##:::: ##: ##.. ##::: ##. ####:::::::::::::
        ##:::: ##: ##:::: ##: ##::::::: ##::::::: ##:::: ##: ##:::: ##: ##::. ##:: ##:. ###:::::::::::::
        ########::. #######:: ########: ########: ##:::: ##:. #######:: ##:::. ##: ##::. ##:::::::::::::
        ........::::.......:::........::........::..:::::..:::.......:::..:::::..::..::::..::::::::::::::
        :::::::::'####:'##::: ##:'########:'########:'########::'########::::'###:::::'######::'########:
        :::::::::. ##:: ###:: ##:... ##..:: ##.....:: ##.... ##: ##.....::::'## ##:::'##... ##: ##.....::
        :::::::::: ##:: ####: ##:::: ##:::: ##::::::: ##:::: ##: ##::::::::'##:. ##:: ##:::..:: ##:::::::
        :::::::::: ##:: ## ## ##:::: ##:::: ######::: ########:: ######:::'##:::. ##: ##::::::: ######:::
        :::::::::: ##:: ##. ####:::: ##:::: ##...:::: ##.. ##::: ##...:::: #########: ##::::::: ##...::::
        :::::::::: ##:: ##:. ###:::: ##:::: ##::::::: ##::. ##:: ##::::::: ##.... ##: ##::: ##: ##:::::::
        ::::::::::####: ##::. ##:::: ##:::: ########: ##:::. ##: ##::::::: ##:::: ##:. ######:: ########:
        ::::::::::....::..::::..:::::..:::::........::..:::::..::..::::::::..:::::..:::......:::........::

Description
===========

This package facilitates the usage of Bullhorn's developer API. This package has full documentation available at `<https://jjorissen52.github.io/bullhorn_interface/index.html>`__ .

Features
--------

-  Handles Authorization

   -  Stored Credentials Optional

-  Handles Tokens

   -  Granting
   -  Storing
   -  Auto Refresh Expired Tokens

-  Facilitates Simple Concurrency
-  Works in Windows (Please no flash photography)


Environment Setup
=================

Linux
-----

Create environment using anaconda or whatever and activate it:

.. code:: python

    conda create -n bullhorn3.6
    source activate bullhorn3.6
    pip install -r /path/to/project_root/requirements.txt

Windows (Anaconda)
==================

Same as above, but you will need to perform

.. code:: python

    conda install psycopg2
    conda install sqlalchemy

afterwards, as there are some dependencies that Anaconda has to work out
to make these packages work on Windows. I highly recommend you use
Anaconda in windows, as it will handle all the nasty c bits that
numerous python packages require.

 ## Configuration

There needs to be a file named ``bullhorn_interface.conf`` that looks
like this somewhere on your system:

.. code:: python

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

If this file lives in your working directory you are good to go. If not,
you will need to set an environment variable to the full path of this
file. Note that you can leave each of these lines blank if you are not
comfortable storing items in plaintext, but none of the test will pass
if vital items are left blank. See `here <#no_plaintext>`__ about how to
use the interface without storing credentials in plain text.

Linux
=====

.. code:: python

    export INTERFACE_CONF_FILE=/home/jjorissen/interface_secrets.conf

Windows
=======

.. code:: python

    set INTERFACE_CONF_FILE=/full/path/to/bullhorn_secrets.conf

Python

.. code:: python

    import os
    os.environ['INTERFACE_CONF_FILE'] = '/home/jjorissen/interface_secrets.conf'

To test your current configuration you can do:

.. code:: python

    # this cannot be run in jupyter notebooks, sadly.
    from bullhorn_interface import tests
    tests.run()

If you want to run a full coverage test (for even the features you
aren't configured for) you can set the below environment variable first.

.. code:: python

    export TEST_FULL_COVERAGE=1 # it's actually not quite full coverage, sorry.

Developers, you can run the below to test the coverage.

.. code:: python

    sudo apt-get install coverage
    coverage run -m unittest discover -s bullhorn_interface/
    #inline summary
    coverage report -m
    # generate browser navigable summary
    coverage html




Using Postgres or SQLite
========================

Database Setup
-------------------

Note: If you are using PG, your ``DB_USER`` must have access to the 'postgres' database on your postgreSQL server, and must have sufficient permissions to create and edit databases.


To create a database to house your tokens:

.. code:: python

    from bullhorn_interface.api import tokenbox
    tokenbox.create_database() 


.. parsed-literal::

    bullhorn_box created successfully.


If you wish to drop that database for some reason:

.. code:: python

    tokenbox.destroy_database()


.. parsed-literal::

    Database named bullhorn_box will be destroyed in 5...4...3...2...1...0
    bullhorn_box dropped successfully.


It's that easy. The necessary tables will be created automatically when
the tokens are generated for the first time, so don't sweat anything!
For more information on using ``tokenbox``, visit the
`repo <https://github.com/jjorissen52/tokenbox>`__

Interface Explanation
===================

``bullhorn_interface`` interacts will Bullhorn's
API using ``Interface`` objects.

- ``LiveInterface``  keeps tokens on itself. These guys should always be created as ``independent``, as ``LiveInterface`` objects are capable of refreshing expired tokens only for themselves.
- ``StoredInterface`` keeps tokens on itself and also checks tokens in the database before allowing a refresh to happen. This allows you to use the same token among many interfaces in case you need to have many running at once. \* Bullhorn doesn't seem to mind if you have numerous API logins running simultaneously, so there isn't much utility to the ``StoredInterface``. However, in the case where you are creating new ``Interface`` objects frequently, using an ```independent`` stored interface will keep you from having to wait on unnecessary ``login()`` calls.

Using LiveInterface
====================


Generate Login Token
------------------------

.. code:: python

    from bullhorn_interface import api
    interface = api.LiveInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)
    interface.login()


.. parsed-literal::

        New Login Token


Generate API Token
-------------------

Once you've been granted a login token, you can get a token and url for the rest API.

.. code:: python

    interface.get_api_token()


.. parsed-literal::

        New Access Token


Make API Calls
-------------------

.. code:: python

    import pandas
    # equivalent to query="lastName:Jorissen AND firstName:John-Paul"
    df = pandas.DataFrame(interface.api_search(entity='Candidate', lastName="Jorissen", firstName="John-Paul")['data'])
    # df = pandas.DataFrame(interface.api_search(entity='Candidate', query="lastName:Jorissen AND firstName:John-Paul")['data'])
    df[['lastName', 'firstName']].head(2)


.. parsed-literal::

        New Login Token
        New Access Token
        Refreshing API Token




.. raw:: html

    <div>
    <style>
        .dataframe thead tr:only-child th {
            text-align: right;
        }
    
        .dataframe thead th {
            text-align: left;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>lastName</th>
          <th>firstName</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>Jorissen</td>
          <td>John-Paul</td>
        </tr>
        <tr>
          <th>1</th>
          <td>Jorissen</td>
          <td>John-Paul</td>
        </tr>
      </tbody>
    </table>
    </div>



If you can get a candidate by name like above, everything is setup
properly.

Using StoredInterface
=====================

If you for `some reason <#storedinterface_reasons>`__ need (or want) to
keep your tokens stored in a database, you can use the stored interface.

.. code:: python

    interface = api.StoredInterface(username=api.BULLHORN_USERNAME, password=api.BULLHORN_PASSWORD)

You interact with everything the same way as the ``LiveInterface``
setup.

.. code:: python

    interface.login()
    interface.get_api_token()
    # there is never a reason to manually invoke refresh_token(); api_call() will handle expired tokens for you. 
    interface.refresh_token()
    df = pandas.DataFrame(interface.api_search(entity='Candidate', lastName="Jorissen", firstName="John-Paul")['data'])


.. parsed-literal::

        New Login Token
        New Access Token


.. code:: python

    df[['lastName', 'firstName']].head(2)




.. raw:: html

    <div>
    <style>
        .dataframe thead tr:only-child th {
            text-align: right;
        }
    
        .dataframe thead th {
            text-align: left;
        }
    
        .dataframe tbody tr th {
            vertical-align: top;
        }
    </style>
    <table border="1" class="dataframe">
      <thead>
        <tr style="text-align: right;">
          <th></th>
          <th>lastName</th>
          <th>firstName</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th>0</th>
          <td>Jorissen</td>
          <td>John-Paul</td>
        </tr>
        <tr>
          <th>1</th>
          <td>Jorissen</td>
          <td>John-Paul</td>
        </tr>
      </tbody>
    </table>
    </div>



 There is one difference here, however. You can make your
``StoredInterface`` objects independent. This means that they will not
login or refresh tokens on their own; they will instead be relying on a
lead ``StoredInterface`` to keep tokens fresh. For a demonstration run 1
and 2 in separate python command prompts.

.. code:: python

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


.. parsed-literal::

        New Login Token
        New Access Token
        Token Expired. Attempt 1/10 failed.




.. parsed-literal::

    {'_score': 1.0,
     'comments': '',
     'firstName': 'John-Paul',
     'id': 425082,
     'lastName': 'Jorissen',
     'middleName': None,
     'notes': {'data': [], 'total': 0}}



Avoiding Plaintext Passwords
==============================

If you are a bit squeamish about storing your Bullhorn login credentials
in plaintext somewhere on your filesystem there is a workaround for you.

.. code:: python

    import os
    os.environ['INTERFACE_CONF_FILE'] = '/home/jjorissen/bullhorn_secrets.conf'
    from bullhorn_interface import api
    # don't give the interface your password in the config file (leave that field blank)
    interface = api.LiveInterface(username="", password="")
    # run login and get the url that will generate a login code for you. YOU MUST RUN IT YOURSELF; VISITING
    # THE URL FROM THIS TUTORIAL WILL NOT WORK FOR YOU.
    interface.login()

::

    Credentials not provided. Provide a username/password combination or follow the procedure below: 
    Paste this URL into browser https://auth.bullhornstaffing.com/oauth/authorize?client_id=YOUCLIENTID&response_type=code 
    Redirect URL will look like this: http://www.bullhorn.com/?code=YOUR%CODE%WILL%BE%RIGHT%HERE&client_id=YOURCLIENTID.

.. code:: python

    # you can only login with this code once.
    interface.login(code="YOUR%CODE%WILL%BE%RIGHT%HERE")


.. parsed-literal::

        New Login Token


You can also avoiding storing any other sensitive information in
plaintext by omitting them from your configurations (leave the key
empty) file and manually adding it to the ``Interface`` and
``api.tokenbox`` like shown below:

.. code:: python

    from tokenbox import TokenBox
    api.tokenbox = TokenBox('username', 'password', 'db_name', api.metadata, db_host='localhost', 
                            use_sqlite=True, **api.table_definitions)
    interface.client_id = "I%am%your%client%ID"
    interface.client_secret = "I%am%your%client%secret"
    interface.login()

API Guides
==============

Now with your interfaces in order, you can make API calls. This will all
be done with ``interface.api_call`` and numerous other helper methods.
You'll need to look over the Bullhorn API Reference Material if you
haven't already to familiarize yourself with the entities and how they
related to one another.

-  `Bullhorn API Reference <http://bullhorn.github.io/rest-api-docs/>`__
-  `Bullhorn Entity
   Guide <http://bullhorn.github.io/rest-api-docs/entityref.html>`__
-  `bullhorn_interface API documentation <https://jjorissen52.github.io/bullhorn_interface/source/bullhorn_interface.html#module-bullhorn_interface.api>`__

Get Candidate IDs (and comments) by first and last name

.. code:: python

    first_name, last_name = "John-Paul", "Jorissen"
    
    def get_candidate_id(first_name, last_name):
           return interface.api_call(command="search", entity="Candidate", select_fields=["id", "comments"],
                           query=f"firstName:{first_name} AND lastName:{last_name}")
    
    candidate = get_candidate_id(first_name, last_name)['data']
    print(list(filter(lambda x: x['id'] == 425084, candidate)))


.. parsed-literal::

    [{'id': 425084, 'comments': 'I am the old comment', '_score': 1.0}]


Update a Candidate's comments

.. code:: python

    candidate_id = 425084
    comments = 'I am the new comment'
    body = {"comments": comments}
    interface.api_call(command="entity", entity="Candidate", entity_id=candidate_id, body=body, method="UPDATE")




.. parsed-literal::

    {'changeType': 'UPDATE',
     'changedEntityId': 425084,
     'changedEntityType': 'Candidate',
     'data': {'comments': 'I am the new comment'}}



.. code:: python

    print(list(filter(lambda x: x['id'] == 425084, get_candidate_id(first_name, last_name)['data'])))


.. parsed-literal::

    [{'id': 425084, 'comments': 'I am the new comment', '_score': 1.0}]


Questions
=========

Feel free to contact me with questions and suggestions of improvements.
Contributions are greatly appreciated.

`jjorissen52@gmail.com <mailto:jjorissen52@gmail.com>`__
