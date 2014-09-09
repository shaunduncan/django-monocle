Monocle: Rich Content using OEmbed
==================================

.. image:: _static/sir.jpg

Monocle is a Django application that handles rich content embedding using
`OEmbed <http://oembed.com>`_, built specifically with scalability and performance in
mind.

:Authors: Shaun Duncan
:Contact: shaun.duncan@gmail.com
:Version: 0.0.6
:License: MIT


Requirements
------------

Currently, Monocle requires the following dependencies:

* BeautifulSoup
* Celery


Key Points and Features
-----------------------

* Flexible OEmbed provider system/mixins

  * External providers: resources fetched asynchronously
  * Internal providers: no external requests made. Direct resource building

* Custom oembeddable content fields that prefetch any external or cached internal oembed content
* Non-blocking asynchronous external content retrieval
* Custom template tags and filters for oembedding content
* Cached oembed resources using Django cache backend

  * Configurable cache expiration
  * TTL utilization: automatic cache refresh of stale content

* Database stored, configurable external providers
* Providers configurable to be exposed via URL endpoint


Demo Application
----------------

A small example django app is available in ``example`` that demonstrates much of
the features and asynchronous nature of Monocle.

First, install the required python packages (best done within a virtualenv)::

    $ pip install -r example/requirements.txt

You will need to ensure your local machine has memcached and sqlite3 installed.

To set up the application for a small test, perform the following::

    $ cd /path/to/monocle/example
    $ export PYTHONPATH=/path/to/monocle
    $ ./manage.py syncdb
    
Once you have run ``syncdb``, you will need to start memcached, followed by the monocle
celery worker, followed by the development server::

    $ memcached -p 11211 -d
    $ ./manage.py celeryd -Q monocle --no-execv
    $ ./manage.py runserver


TODO
----

* Support embed.ly which introduces API credentials to the provider
* Management command to pre-populate third party providers from embed.ly
* Expose format=xml from oembed endpoint
* Pre-configured provider fixtures
* Allow callback= in JSON oembed endpoint requests
* Support multiple URL requests from oembed endpoint
* Better exception handling/custom error reporting
* Expose list of exposed oembed providers via URL
* Limited access to Django exposed oembed providers (same domain or API key)
* Configurable allow https url schemes
* Optional URL kwargs for provider endpoints
* External providers configurable to handle XML or JSON
* Non-specific instance check in provider registry (handle contrib external providers)


Contents
--------

.. toctree::
   :maxdepth: 2

   api
   changelog


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

