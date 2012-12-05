"""
Misc settings that can be overridden
"""
from django.conf import settings


# HTTP/Network settings
HTTP_TIMEOUT = getattr(settings, 'MONOCLE_HTTP_TIMEOUT', 3)  # 3 sec default


# Task Settings
TASK_QUEUE = getattr(settings, 'MONOCLE_TASK_QUEUE', 'monocle')
TASK_EXTERNAL_RETRY_DELAY = getattr(settings, 'MONOCLE_TASK_EXTERNAL_RETRY_DELAY', 1)  # 1 sec default
TASK_EXTERNAL_MAX_RETRIES = getattr(settings, 'MONOCLE_TASK_EXTERNAL_MAX_RETRIES', 3)


# Cache Settings
CACHE_KEY_PREFIX = getattr(settings, 'MONOCLE_CACHE_KEY_PREFIX', 'MONOCLE')
CACHE_PRIMER = getattr(settings, 'MONOCLE_CACHE_PRIMER', u'')
