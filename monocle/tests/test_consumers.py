import re

from mock import Mock, patch
from unittest2 import TestCase

from BeautifulSoup import BeautifulSoup

from monocle.consumers import Consumer, HTMLConsumer, prefetch


TEXT_CONTENT = """
    There are three URLs in this content:
    http://foo.com, http://bar.com, and (http://baz.com/foo?a=b&x=y)!
"""

HTML_CONTENT = """
<html>
    <body>
        <p>URL content http://foo.com</p>
        <p>URL content http://foo.com, http://bar.com, and (http://baz.com/foo?a=b&x=y)</p>
        <p>Link content <a>http://foo.com</a></p>
    </body>
</html>
"""


class ConsumerTestCase(TestCase):

    def setUp(self):
        self.consumer = Consumer()

    def test_url_regex(self):
        urls = self.consumer.url_regex.findall(TEXT_CONTENT)
        expected = [
            'http://foo.com',
            'http://bar.com',
            'http://baz.com/foo?a=b&x=y'
        ]

        self.assertEqual(expected, urls)

    @patch('monocle.consumers.registry')
    def test_enrich(self, registry):
        provider = Mock()
        provider.get_resource.return_value = provider
        provider.render.return_value = 'RESOURCE'

        registry.match.return_value = provider

        result = self.consumer.enrich(TEXT_CONTENT)

        self.assertIn('RESOURCE, RESOURCE, and (RESOURCE)', result)


class HTMLConsumerTestCase(TestCase):

    def setUp(self):
        self.consumer = HTMLConsumer()

    def test_is_hyperlinked(self):
        soup = BeautifulSoup('NOTLINK <a>LINKED</a>')
        nodes = soup.findAll(text=re.compile(r'LINK'))

        self.assertFalse(self.consumer._is_hyperlinked(nodes[0]))
        self.assertTrue(self.consumer._is_hyperlinked(nodes[1]))

    @patch('monocle.consumers.registry')
    def test_devour(self, registry):
        provider = Mock()
        provider.get_resource.return_value = provider
        provider.render.return_value = 'RESOURCE'

        registry.match.return_value = provider

        result = self.consumer.devour(HTML_CONTENT)

        self.assertIn('<p>URL content RESOURCE</p>', result)
        self.assertIn('<p>URL content RESOURCE, RESOURCE, and (RESOURCE)</p>', result)
        self.assertIn('<p>Link content <a>http://foo.com</a>', result)


class PrefetchTestCase(TestCase):

    def mock_provider_and_registry(self, registry):
        provider = Mock()
        provider.get_resource.return_value = provider
        provider.render.return_value = 'RESOURCE'

        registry.match.return_value = provider

        return provider, registry

    @patch('monocle.consumers.registry')
    @patch.object(Consumer, 'enrich')
    def test_prefetch_no_sizes(self, enrich_fn, registry):
        provider, registry = self.mock_provider_and_registry(registry)
        prefetch(TEXT_CONTENT)

        enrich_fn.assert_called_once_with(TEXT_CONTENT, maxwidth=None, maxheight=None)

    @patch('monocle.consumers.registry')
    @patch.object(Consumer, 'enrich')
    def test_prefetch_tuple_sizes(self, enrich_fn, registry):
        provider, registry = self.mock_provider_and_registry(registry)
        prefetch(TEXT_CONTENT, sizes=[(100, 200), (300, 400)])

        self.assertEqual(enrich_fn.call_count, 3)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=None, maxheight=None)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=100, maxheight=200)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=300, maxheight=400)

    @patch('monocle.consumers.registry')
    @patch.object(Consumer, 'enrich')
    def test_prefetch_int_sizes(self, enrich_fn, registry):
        provider, registry = self.mock_provider_and_registry(registry)
        prefetch(TEXT_CONTENT, sizes=[100])

        self.assertEqual(enrich_fn.call_count, 4)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=None, maxheight=None)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=100, maxheight=None)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=None, maxheight=100)
        enrich_fn.assert_any_call(TEXT_CONTENT, maxwidth=100, maxheight=100)
