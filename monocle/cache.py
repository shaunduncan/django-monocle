from django.core.cache import cache

from monocle.settings import (CACHE_KEY_PREFIX,
                              CACHE_PRIMER)


def make_key(*args):
    return '%s:%s' % (CACHE_KEY_PREFIX, ':'.join(args))


def get_or_prime(key, primer=CACHE_PRIMER):
    """
    Primes the cache if value does not exists. Returns
    cached and boolean if cache was primed
    """
    if cache.add(key, primer):
        return primer, True
    else:
        return cache.get(key), False
