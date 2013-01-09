==================================
Monocle: Rich Content using OEmbed
==================================

![Like A Sir](http://i.imgur.com/WzjGo.png)

Monocle is a Django app built for rich content embedding using [OEmbed](http://oembed.com)
that is built with scalability and performance in mind


Requirements
------------
- BeautifulSoup
- Celery


Documentation
-------------
Full documentation can be built via tox::

    $ tox -e docs
    $ cd .tox/docs/build/html


Key Points and Features
---------------------------
- Flexible OEmbed provider system/mixins
  - External providers: resources fetched asynchronously
  - Internal providers: no external requests made. Direct resource building
- Custom oembeddable content fields that prefetch any external or cached internal oembed content
- Non-blocking asynchronous external content retrieval
- Custom template tags and filters for oembedding content
- Cached oembed resources using Django cache backend
  - Configurable cache expiration
  - TTL utilization: automatic cache refresh of stale content
- Database stored, configurable external providers
- Providers configurable to be exposed via URL endpoint


TODO
----
- Support embed.ly which introduces API credentials to the provider
- Management command to pre-populate third party providers from embed.ly
- Expose format=xml from oembed endpoint
- Pre-configured provider fixtures
- Allow callback= in JSON oembed endpoint requests
- Support multiple URL requests from oembed endpoint
- Better exception handling/custom error reporting
- Expose list of exposed oembed providers via URL
- Limited access to Django exposed oembed providers (same domain or API key)
- Configurable allow https url schemes
- Optional URL kwargs for provider endpoints
- External providers configurable to handle XML or JSON
- Non-specific instance check in provider registry (handle contrib external providers)


Contribution and License
------------------------
Developed by Shaun Duncan <shaun.duncan@gmail.com> at
[CMG, Digital and Strategy](http://cmgdigital.com/) and is licensed under the
terms of a MIT license.
