"""
Misc settings that can be overridden
"""
from django.conf import settings


# Resource Settings
RESOURCE_TYPES = ('link', 'photo', 'rich', 'video')
RESOURCE_CHOICES = [(x, x.capitalize()) for x in RESOURCE_TYPES]
RESOURCE_REQUIRED_ATTRS = {
    'link': (),
    'photo': ('url', 'width', 'height'),
    'rich': ('html', 'width', 'height'),
    'video': ('html', 'width', 'height')
}

RESOURCE_OPTIONAL_ATTRS = ('title', 'author_name', 'author_url', 'cache_age',
                           'provider_name', 'provider_url', 'thumbnail_url',
                           'thumbnail_width', 'thumbnail_height')


# Provider Settings
CACHE_LOCAL_PROVIDERS = getattr(settings, 'MONOCLE_CACHE_LOCAL_PROVIDERS', False)


# HTTP/Network settings
HTTP_TIMEOUT = getattr(settings, 'MONOCLE_HTTP_TIMEOUT', 3)  # 3 sec default


# Task Settings
TASK_QUEUE = getattr(settings, 'MONOCLE_TASK_QUEUE', 'monocle')
TASK_EXTERNAL_RETRY_DELAY = getattr(settings, 'MONOCLE_TASK_EXTERNAL_RETRY_DELAY', 1)  # 1 sec default
TASK_EXTERNAL_MAX_RETRIES = getattr(settings, 'MONOCLE_TASK_EXTERNAL_MAX_RETRIES', 3)


# Cache Settings
CACHE_KEY_PREFIX = getattr(settings, 'MONOCLE_CACHE_KEY_PREFIX', 'MONOCLE')
