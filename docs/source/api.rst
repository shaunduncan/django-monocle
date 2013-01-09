.. _api:

Module Documentation
====================
The Monocle API is relatively straightforward and largely follows the
`OEmbed <http://oembed.com>`_ spec.


:mod:`monocle.cache`
--------------------

.. automodule:: monocle.cache
   :members:


:mod:`monocle.consumers`
-------------------------

.. autoclass:: monocle.consumers.Consumer
   :members: devour, enrich
.. automodule:: monocle.consumers
   :members: HTMLConsumer, devour, prefetch


:mod:`monocle.fields`
---------------------

.. automodule:: monocle.fields
   :members:


:mod:`monocle.models`
---------------------

.. automodule:: monocle.models
   :members:


:mod:`monocle.providers`
------------------------

.. automodule:: monocle.providers
   :members:


:mod:`monocle.resources`
------------------------

.. automodule:: monocle.resources
   :members:


:mod:`monocle.settings`
-----------------------

.. autoclass:: monocle.settings.Settings
   :members:

   .. attribute:: RESOURCE_CHECK_INTERNAL_SIZE

      Bool if a warning should be raised if internal providers do not respect max width/height
      (default False)

   .. attribute:: RESOURCE_DEFAULT_DIMENSIONS

      Default dimensions for internal providers that don't specify sizes. Should be a list of
      integer two-tuples (default list (100, 100)...(1000, 1000))

   .. attribute:: RESOURCE_MIN_TTL

      Minimum TTL for :class:`Resource` objects to be considered fresh (in seconds, default 1hr)

   .. attribute:: RESOURCE_DEFAULT_TTL

      Default TTL for :class:`Resource` objects to be considered fresh (in seconds, default 1wk)

   .. attribute:: RESOURCE_URLIZE_INVALID

      Bool if invalid :class:`Resource` objects should be hyperlinked (default True)

   .. attribute:: CACHE_INTERNAL_PROVIDERS

      Bool if any subclass of :class:`InternalProvider` should be cached. (default False)

   .. attribute:: EXPOSE_LOCAL_PROVIDERS

      Bool if any subclass of :class:`InternalProvider` should be exposed via a URL endpoint.
      (default True)

   .. attribute:: HTTP_TIMEOUT

      Default timeout in seconds for any external OEmbed requests (default is 3)

   .. attribute:: TASK_QUEUE

      Named celery queue for external OEmbed requests (default 'monocle')

   .. attribute:: TASK_EXTERNAL_RETRY_DELAY

      Delay between retries for external request tasks (in seconds, default 1)

   .. attribute:: TASK_EXTERNAL_MAX_RETRIES

      Maximum of retries for external request tasks (default 3)

   .. attribute:: CACHE_KEY_PREFIX

      Prefix string for cached objects (default 'MONOCLE')

   .. attribute:: CACHE_AGE

      Default age objects should live in cache (in seconds, default 30d)


:mod:`monocle.signals`
----------------------

.. automodule:: monocle.signals


:mod:`monocle.tasks`
--------------------

.. automodule:: monocle.tasks
   :members:


:mod:`monocle.views`
--------------------

.. automodule:: monocle.views
   :members: oembed
