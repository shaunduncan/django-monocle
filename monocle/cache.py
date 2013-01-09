"""
This module provides a single cache wrapper instance that can be used as follows::

    from monocle.cache import cache
"""
import logging

from django.core.cache import cache as _cache

from monocle.settings import settings
from monocle.signals import cache_miss, cache_hit


logger = logging.getLogger(__name__)


class Cache(object):
    """
    A minimal wrapper around ``django.core.cache.cache`` that both ensures
    proper timeouts and key structure
    """

    def make_key(self, *args):
        """
        Returns a consistent cache key that is the result of prefixing
        ``CACHE_KEY_PREFIX`` from :mod:`monocle.settings` with method args
        joined by a colon.

        For example

        >>> make_key('foo', 'bar')
        "MONOCLE:foo:bar"
        """
        return '%s:%s' % (settings.CACHE_KEY_PREFIX, ':'.join(args))

    def get_or_prime(self, key, primer=''):
        """
        Gets an object from cache or primes the cache with a specified primer
        if the specified key does not exist in cache.

        :param string key: Cache key to retrieve
        :param primer: Specific value to prime the cache with if no key exists
        :returns: Two-tuple (value, primed) where primed indicates if cache was primed
        """
        key = self.make_key(key)

        if _cache.add(key, primer, timeout=settings.CACHE_AGE):
            logger.debug('Primed cache key %s with %s for age %s' % (key, primer, settings.CACHE_AGE))
            cache_miss.send(sender=self, key=key)
            return primer, True
        else:
            cache_hit.send(sender=self, key=key)
            return _cache.get(key), False

    def set(self, key, value):
        """
        Wrapper for ``cache.set()`` to ensure that the cache key is properly
        formatted and setting value ``CACHE_AGE`` is specified as a timeout

        :param string key: Cache key
        :param value: Cache value
        :returns: Result of Django ``cache.set()``
        """
        _cache.set(self.make_key(key), value, timeout=settings.CACHE_AGE)

    def get(self, key):
        """
        Retrieves an object from cache ensuring the specified key is properly formatted.
        Calls to this method will send either ``cache_miss`` or ``cache_hit`` signals
        depeding on whether the result of django ``cache.get()`` is None or not respectively.``

        :param string key: Cache key to retrieve
        :returns: Result of Django ``cache.get()``
        """
        key = self.make_key(key)
        val = _cache.get(key)

        # Django cache backend explicitly returns `None` on a miss
        if val is None:
            cache_miss.send(sender=self, key=key)

        return val

    def delete(self, key):
        return _cache.delete(self.make_key(key))


cache = Cache()
