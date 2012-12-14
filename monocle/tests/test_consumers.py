import re

from mock import Mock, patch
from unittest2 import TestCase

from BeautifulSoup import BeautifulSoup

from monocle.consumers import Consumer, HTMLConsumer


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
        self.consumer = Consumer(TEXT_CONTENT)

    def test_get_urls(self):
        urls = self.consumer.get_urls(TEXT_CONTENT)
        expected = [
            'http://foo.com',
            'http://bar.com',
            'http://baz.com/foo?a=b&x=y'
        ]

        self.assertEqual(expected, urls)

    @patch('monocle.consumers.registry')
    def test_devour(self, registry):
        provider = Mock()
        provider.get_resource.return_value = provider
        provider.render.return_value = 'RESOURCE'

        registry.match.return_value = provider

        result = self.consumer.devour(TEXT_CONTENT)

        self.assertIn('RESOURCE, RESOURCE, and (RESOURCE)', result)


class HTMLConsumerTestCase(TestCase):

    def setUp(self):
        self.consumer = HTMLConsumer(HTML_CONTENT)

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
