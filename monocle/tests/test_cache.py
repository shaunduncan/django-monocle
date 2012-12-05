from unittest2 import TestCase

from django.core.cache import cache

from monocle.cache import get_or_prime


class TestCache(TestCase):

    def test_get_or_prime_primes(self):
        cache.delete('foo')

        cached, primed = get_or_prime('foo', primer='bar')

        assert primed
        assert cached == 'bar'

    def test_get_or_prime_does_not_prime(self):
        cache.set('foo', 'bar')

        cached, primed = get_or_prime('foo', primer='baz')

        assert not primed
        assert cached != 'baz'
