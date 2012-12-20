from mock import Mock, patch
from unittest2 import TestCase

from monocle.cache import cache
from monocle.consumers import Consumer, HTMLConsumer
from monocle.signals import (cache_miss,
                             cache_hit,
                             pre_consume,
                             post_consume)


def mock_receiver():
    return Mock(wraps=lambda *args, **kwargs: None)


class CacheSignalTestCase(TestCase):

    def test_cache_miss_signal(self):
        cb = mock_receiver()
        cache_miss.connect(cb)

        cache.delete('foo')
        cached, primed = cache.get_or_prime('foo', 'bar')

        self.assertTrue(primed)
        self.assertTrue(cb.called)

    def test_cache_hit_signal(self):
        cb = mock_receiver()
        cache_hit.connect(cb)

        cache.set('foo', 'bar')
        cached, primed = cache.get_or_prime('foo', 'bar')

        self.assertFalse(primed)
        self.assertTrue(cb.called)


class ConsumerSignalTestCase(TestCase):

    def setUp(self):
        self.consumer = Consumer('')
        self.html_consumer = HTMLConsumer('')

    @patch('monocle.consumers.registry')
    def test_base_consumer_signal(self, registry):
        pre_cb = mock_receiver()
        post_cb = mock_receiver()

        pre_consume.connect(pre_cb)
        post_consume.connect(post_cb)

        self.consumer.devour('')

        self.assertTrue(pre_cb.called)
        self.assertTrue(post_cb.called)

    @patch('monocle.consumers.registry')
    def test_html_consumer_signals_once(self, registry):
        pre_cb = mock_receiver()
        post_cb = mock_receiver()

        pre_consume.connect(pre_cb)
        post_consume.connect(post_cb)

        self.consumer.devour('')

        self.assertEqual(pre_cb.call_count, 1)
        self.assertEqual(post_cb.call_count, 1)
