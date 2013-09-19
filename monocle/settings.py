"""
Configurable settings for Monocle. Interaction should occur via the single
instance of :class:`Settings`::

    from monocle.settings import settings
"""
from django.conf import settings as _settings


class Settings(object):
    """
    Django settings proxy used by monocle in such a way that value retrieval
    is performed on-demand. Most settings are entirely configurable via
    ``DJANGO_SETTINGS_MODULE`` and should be prefixed with ``MONOCLE_``. For example
    ``RESOURCE_DEFAULT_TTL`` can be customized with setting ``MONOCLE_RESOURCE_DEFAULT_TTL``.
    """
    _SETTINGS_PREFIX = 'MONOCLE_'
    _DEFAULTS = {
        # Raise warning if internal providers do not respect max width/height
        'RESOURCE_CHECK_INTERNAL_SIZE': False,

        # Default dimensions for internal providers that don't specify sizes
        'RESOURCE_DEFAULT_DIMENSIONS': [(x, x) for x in xrange(100, 1000, 100)],

        # Minimum TTL for OEmbed resource to be considered fresh (in seconds)
        'RESOURCE_MIN_TTL': 60*60,

        # Default TTL for OEmbed resource to be considered fresh (in seconds)
        'RESOURCE_DEFAULT_TTL': 60*60*24*7,

        # Should rendered resources be URLized if they are invalid
        'RESOURCE_URLIZE_INVALID': True,

        # Should local provider resources be cached
        'CACHE_INTERNAL_PROVIDERS': False,

        # Should local providers be exposed by default
        'EXPOSE_LOCAL_PROVIDERS': True,

        # Default timeout in seconds for external HTTP requests
        'HTTP_TIMEOUT': 3,

        # Celery queue for monocle tasks
        'TASK_QUEUE': 'monocle',

        # Delay between retries for async external request tasks
        'TASK_EXTERNAL_RETRY_DELAY': 1,

        # Max number of retries for async external request tasks
        'TASK_EXTERNAL_MAX_RETRIES': 3,

        # Prefix string for monocle cached objects
        'CACHE_KEY_PREFIX': 'MONOCLE',

        # Default cache age
        'CACHE_AGE': 60*60*24*30,

        # Default user-agent for requests to external providers
        'USER_AGENT': 'Mozilla/5.0',
    }

    def __getattr__(self, attr):
        """
        Django settings access with fallback to preconfigured defaults.
        """
        if attr in self._DEFAULTS:
            django_key = '%s%s' % (self._SETTINGS_PREFIX, attr)
            return getattr(_settings, django_key, self._DEFAULTS[attr])
        else:
            raise AttributeError('%s is not a valid setting' % attr)

    @property
    def RESOURCE_TYPES(self):
        """
        Valid OEmbed Resource Types. This is a tuple of the strings

        * link
        * photo
        * rich
        * video

        .. note::
           This settings is **NOT** configurable
        """
        return ('link', 'photo', 'rich', 'video')

    @property
    def RESOURCE_REQUIRED_ATTRS(self):
        """
        Resource attributes that are required by resource type. Resources
        of type `link` require no additional attributes. Others do:

        * ``photo`` types

            * ``url``
            * ``width``
            * ``height``

        * ``rich`` and ``video`` types

            * ``html``
            * ``width``
            * ``height``

        .. note::
           This settings is **NOT** configurable
        """
        return {
            'link': (),
            'photo': ('url', 'width', 'height'),
            'rich': ('html', 'width', 'height'),
            'video': ('html', 'width', 'height')
        }

    @property
    def RESOURCE_OPTIONAL_ATTRS(self):
        """
        Full list of OEmbed resource attributes that are considered optional as
        per the `OEmbed Spec <http://oembed.com>`_.

        * ``title``
        * ``author_name``
        * ``author_url``
        * ``cache_age``
        * ``provider_name``
        * ``provider_url``
        * ``thumbnail_url``
        * ``thumbnail_height``
        * ``thumbnail_width``

        .. note::
           This settings is **NOT** configurable
        """
        return (
            'title', 'author_name', 'author_url', 'cache_age', 'provider_name',
            'provider_url', 'thumbnail_url', 'thumbnail_width', 'thumbnail_height'
        )


settings = Settings()
