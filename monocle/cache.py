from django.core.cache import cache as _cache

from monocle.settings import settings


class Cache(object):
    """
    Wrapper around the configured django cache to ensure timeouts and
    proper cache key structure
    """

    def make_key(self, *args):
        return '%s:%s' % (settings.CACHE_KEY_PREFIX, ':'.join(args))

    def get_or_prime(self, key, primer=''):
        """
        Primes the cache if value does not exists. Returns
        cached and boolean if cache was primed
        """
        key = self.make_key(key)

        if _cache.add(key, primer, timeout=settings.CACHE_AGE):
            return primer, True
        else:
            return _cache.get(key), False

    def set(self, key, value):
        """
        Wraps django cache.set() so that we can apply CACHE_AGE setting
        and transparently ensure a properly prefixed cache key
        """
        _cache.set(self.make_key(key), value, timeout=settings.CACHE_AGE)

    def get(self, key):
        return _cache.get(self.make_key(key))

    def delete(self, key):
        return _cache.delete(self.make_key(key))


cache = Cache()
