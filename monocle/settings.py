from django.conf import settings as _settings


class Settings(object):
    """
    Monocle settings exposed as object properties to allow for dynamic
    settings support
    """

    @property
    def RESOURCE_TYPES(self):
        """Valid OEmbed Resource Types"""
        return ('link', 'photo', 'rich', 'video')

    @property
    def RESOURCE_REQUIRED_ATTRS(self):
        """Resource attributes that are required by resource type"""
        return {
            'link': (),
            'photo': ('url', 'width', 'height'),
            'rich': ('html', 'width', 'height'),
            'video': ('html', 'width', 'height')
        }

    @property
    def RESOURCE_OPTIONAL_ATTRS(self):
        """Full list of OEmbed resource attributes that are considered optional"""
        return (
            'title', 'author_name', 'author_url', 'cache_age', 'provider_name',
            'provider_url', 'thumbnail_url', 'thumbnail_width', 'thumbnail_height'
        )

    @property
    def RESOURCE_CHECK_INTERNAL_SIZE(self):
        """
        Checks internal provider returned data to ensure maxwidth/maxheight respected.
        Raises a warning if they are not respected.
        """
        return getattr(_settings, 'MONOCLE_RESOURCE_CHECK_INTERNAL_SIZE', False)

    @property
    def RESOURCE_DEFAULT_DIMENSIONS(self):
        """
        Default dimensions for internal providers if implementations do not
        define valid sizes.
        """
        return [(x, x) for x in xrange(100, 1000, 100)]

    @property
    def RESOURCE_MIN_TTL(self):
        """Minimum TTL for OEmbed resource to be considered fresh (in seconds)"""
        # 1 Hour Default
        return getattr(_settings, 'MONOCLE_CACHE_MINIMUM_TTL', 60*60)

    @property
    def RESOURCE_DEFAULT_TTL(self):
        """Default TTL for OEmbed resource to be considered fresh (in seconds)"""
        # 1 Week Default
        return getattr(_settings, 'MONOCLE_CACHE_DEFAULT_TTL', 60*60*24*7)

    @property
    def RESOURCE_URLIZE_INVALID(self):
        """Should rendered resources bet URLized if they are invalid"""
        return getattr(_settings, 'MONOCLE_RESOURCE_URLIZE_INVALID', True)

    @property
    def CACHE_INTERNAL_PROVIDERS(self):
        """Setting to indicate if local providers should cache resources"""
        return getattr(_settings, 'MONOCLE_CACHE_INTERNAL_PROVIDERS', False)

    @property
    def EXPOSE_LOCAL_PROVIDERS(self):
        """Should local providers be exposed to external consumers"""
        return getattr(_settings, 'MONOCLE_EXPOSE_LOCAL_PROVIDERS', True)

    @property
    def HTTP_TIMEOUT(self):
        """Default timeout in seconds for external HTTP requests"""
        # 3 Second Default
        return getattr(_settings, 'MONOCLE_HTTP_TIMEOUT', 3)

    @property
    def TASK_QUEUE(self):
        """Celery queue to use for monocle tasks"""
        return getattr(_settings, 'MONOCLE_TASK_QUEUE', 'monocle')

    @property
    def TASK_EXTERNAL_RETRY_DELAY(self):
        """Delay between retries for async external request task"""
        # 1 Seconds Default
        return getattr(_settings, 'MONOCLE_TASK_EXTERNAL_RETRY_DELAY', 1)

    @property
    def TASK_EXTERNAL_MAX_RETRIES(self):
        """Maximum number of retries for async external request task"""
        return getattr(_settings, 'MONOCLE_TASK_EXTERNAL_MAX_RETRIES', 3)

    @property
    def CACHE_KEY_PREFIX(self):
        """Prefix string for monocle cached objects"""
        return getattr(_settings, 'MONOCLE_CACHE_KEY_PREFIX', 'MONOCLE')

    @property
    def CACHE_AGE(self):
        # 30 Day Default
        return getattr(_settings, 'MONOCLE_CACHE_AGE', 60*60*24*30)


settings = Settings()
