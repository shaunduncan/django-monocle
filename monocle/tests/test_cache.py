from unittest2 import TestCase

from monocle.cache import cache


class TestCache(TestCase):

    def test_get_or_prime_primes(self):
        cache.delete('foo')

        # Check that we primed
        cached, primed = cache.get_or_prime('foo', primer='bar')
        assert primed
        assert cached == 'bar'

        # Subsequent call should not prime
        cached, primed = cache.get_or_prime('foo', primer='baz')
        assert not primed
        assert cached == 'bar'

    def test_get_or_prime_does_not_prime(self):
        cache.set('foo', 'bar')

        cached, primed = cache.get_or_prime('foo', primer='baz')
        assert not primed
        assert cached == 'bar'
