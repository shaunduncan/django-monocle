from django.core.cache import cache

from monocle.settings import CACHE_KEY_PREFIX


def make_key(*args):
    return '%s:%s' % (CACHE_KEY_PREFIX, ':'.join(args))


def get_or_prime(key, primer=''):
    """
    Primes the cache if value does not exists. Returns
    cached and boolean if cache was primed
    """
    if cache.add(key, primer):
        return primer, True
    else:
        return cache.get(key), False
