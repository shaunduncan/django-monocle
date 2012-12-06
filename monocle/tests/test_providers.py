from mock import Mock, patch
from unittest2 import TestCase
from urllib import urlencode

from django.conf import settings

from monocle.providers import Provider, InternalProvider
from monocle.resources import Resource


class ProviderTestCase(TestCase):

    def setUp(self):
        self.resource_url = 'http://example.com/resource'

        self.provider = Provider(self.resource_url)
        self.provider.api_endpoint = 'http://foo.com/oembed'

    def test_get_request_url(self):
        request_url = self.provider.get_request_url()

        self.assertIn(self.provider.api_endpoint, request_url)
        self.assertIn(urlencode({'url': self.resource_url}), request_url)
        self.assertIn('format=json', request_url)

    @patch('monocle.providers.request_external_oembed')
    @patch('monocle.providers.cache')
    def test_get_resource_stale_calls_task(self, mock_cache, mock_task):
        resource = Resource(self.resource_url)
        resource.created = resource.created.replace(year=1984)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        mock_task.apply_async = mock_task

        self.assertTrue(resource.is_stale)
        resource = self.provider.get_resource()
        self.assertFalse(resource.is_stale)
        self.assertTrue(mock_task.called)

    @patch('monocle.providers.request_external_oembed')
    @patch('monocle.providers.cache')
    def test_get_resource_primed_calls_task(self, mock_cache, mock_task):
        resource = Resource(self.resource_url)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, True)
        mock_task.apply_async = mock_task

        self.assertFalse(resource.is_stale)
        resource = self.provider.get_resource()
        self.assertTrue(mock_task.called)

    @patch('monocle.providers.request_external_oembed')
    @patch('monocle.providers.cache')
    def test_get_resource_no_task(self, mock_cache, mock_task):
        resource = Resource(self.resource_url)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        mock_task.apply_async = mock_task

        self.provider.get_resource()
        self.assertFalse(mock_task.called)


class InternalProviderTestCase(TestCase):

    def setUp(self):
        self.resource_url = 'http://example.com/resource'
        self.provider = InternalProvider(self.resource_url)

    def test_data_attribute_raises_required(self):
        self.provider.foo = None

        with self.assertRaises(NotImplementedError):
            self.provider._data_attribute('foo', required=True)

    def test_data_attribute_does_not_raise(self):
        self.provider.foo = None
        result = self.provider._data_attribute('foo')
        self.assertIsNone(result)

    def test_data_attribute_calls_callable(self):
        self.provider.foo = Mock()
        self.provider.foo.return_value = 'foo'
        result = self.provider._data_attribute('foo')
        self.assertEqual('foo', result)

    def test_data_attribute_property(self):
        self.provider.foo = 'foo'
        result = self.provider._data_attribute('foo')
        self.assertEqual('foo', result)

    def test_build_resource_undefined_type(self):
        # Setup for some type not defined - nothing should break
        self.provider.resource_type = 'flash'
        self.provider.html = 'HTML'
        self.provider.foo = 'foo'
        self.provider.author_name = 'John Galt'

        resource = self.provider._build_resource()

        # Base things
        self.assertEqual('1.0', resource['version'])
        self.assertEqual('flash', resource['type'])

        # Should skip
        self.assertNotIn('html', resource)

        # Not an OEmbed param
        self.assertNotIn('foo', resource)

        # Optional param
        self.assertEqual(resource['author_name'], self.provider.author_name)

    def test_build_resource_valid_type(self):
        # Ensure that we do the right thing for types we know about
        self.provider.resource_type = 'video'
        self.provider.html = 'FooBar'
        self.provider.width = 100
        self.provider.height = 100
        self.provider.author_name = 'John Galt'

        resource = self.provider._build_resource()

        # Base things
        self.assertEqual('1.0', resource['version'])
        self.assertEqual('video', resource['type'])

        self.assertEqual('FooBar', resource['html'])
        self.assertEqual(100, resource['width'])
        self.assertEqual(100, resource['height'])

        # Optional param
        self.assertEqual('John Galt', resource['author_name'])

    @patch('monocle.providers.cache')
    def test_get_resource_cached_is_stale(self, mock_cache):
        # Update django settings
        setattr(settings, 'MONOCLE_CACHE_LOCAL_PROVIDERS', True)

        resource = Resource(self.resource_url)
        resource.created = resource.created.replace(year=1984)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        self.provider._build_resource = Mock(return_value=resource)

        self.assertTrue(resource.is_stale)
        resource = self.provider.get_resource()
        self.assertFalse(resource.is_stale)
        self.assertTrue(self.provider._build_resource.called)

    @patch('monocle.providers.cache')
    def test_get_resource_cached_is_primed(self, mock_cache):
        # Update django settings
        setattr(settings, 'MONOCLE_CACHE_LOCAL_PROVIDERS', True)

        resource = Resource(self.resource_url)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, True)
        self.provider._build_resource = Mock(return_value=resource)

        self.assertFalse(resource.is_stale)
        resource = self.provider.get_resource()
        self.assertFalse(resource.is_stale)
        self.assertTrue(self.provider._build_resource.called)
