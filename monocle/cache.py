import logging

from django.core.cache import get_cache

from monocle.settings import settings
from monocle.signals import cache_miss, cache_hit


logger = logging.getLogger(__name__)


class Cache(object):
    """
    Wrapper around the configured django cache to ensure timeouts and
    proper cache key structure
    """
    def __init__(self):
        # Explicitly use django's CACHE_BACKEND. Celery might be different
        self._cache = get_cache(settings.CACHE_BACKEND)

    def make_key(self, *args):
        return '%s:%s' % (settings.CACHE_KEY_PREFIX, ':'.join(args))

    def get_or_prime(self, key, primer=''):
        """
        Primes the cache if value does not exists. Returns
        cached and boolean if cache was primed. Hit/Miss are sent here
        """
        key = self.make_key(key)

        if self._cache.add(key, primer, timeout=settings.CACHE_AGE):
            logger.debug('Primed cache key %s with %s for age %s' % (key, primer, settings.CACHE_AGE))
            cache_miss.send(sender=self, key=key)
            return primer, True
        else:
            cache_hit.send(sender=self, key=key)
            return self._cache.get(key), False

    def set(self, key, value):
        """
        Wraps django cache.set() so that we can apply CACHE_AGE setting
        and transparently ensure a properly prefixed cache key
        """
        self._cache.set(self.make_key(key), value, timeout=settings.CACHE_AGE)

    def get(self, key):
        key = self.make_key(key)
        val = self._cache.get(key)

        # Django cache backend explicitly returns `None` on a miss
        if val is None:
            cache_miss.send(sender=self, key=key)

        return val

    def delete(self, key):
        return self._cache.delete(self.make_key(key))


cache = Cache()
