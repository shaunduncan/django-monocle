from mock import Mock, patch
from unittest2 import TestCase
from urllib import urlencode

from django.conf import settings

from monocle.models import ThirdPartyProvider, URLScheme
from monocle.providers import Provider, InternalProvider, ProviderRegistry
from monocle.resources import Resource


class ProviderTestCase(TestCase):

    def setUp(self):
        self.resource_url = 'http://example.com/resource'

        self.provider = Provider()
        self.provider.api_endpoint = 'http://foo.com/oembed'

    def test_get_request_url(self):
        params = {'url': self.resource_url, 'format': 'json'}
        request_url = self.provider.get_request_url(params)

        self.assertIn(self.provider.api_endpoint, request_url)
        self.assertIn(urlencode({'url': self.resource_url}), request_url)
        self.assertIn('format=json', request_url)

    def test_get_request_url_filters_zeros(self):
        params = {
            'url': self.resource_url,
            'format': 'json'
        }

        params.update({'maxwidth': '0', 'maxheight': 100})
        request_url = self.provider.get_request_url(params)
        self.assertNotIn('maxwidth', request_url)

        params.update({'maxwidth': 100, 'maxheight': None})
        request_url = self.provider.get_request_url(params)
        self.assertNotIn('maxheight', request_url)

    @patch('monocle.providers.request_external_oembed')
    @patch('monocle.providers.cache')
    def test_get_resource_stale_calls_task(self, mock_cache, mock_task):
        resource = Resource(self.resource_url)
        resource.created = resource.created.replace(year=1984)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        mock_task.apply_async = mock_task

        self.assertTrue(resource.is_stale)
        resource = self.provider.get_resource(self.resource_url)
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
        resource = self.provider.get_resource(self.resource_url)
        self.assertTrue(mock_task.called)

    @patch('monocle.providers.request_external_oembed')
    @patch('monocle.providers.cache')
    def test_get_resource_no_task(self, mock_cache, mock_task):
        resource = Resource(self.resource_url)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        mock_task.apply_async = mock_task

        self.provider.get_resource(self.resource_url)
        self.assertFalse(mock_task.called)

    def test_match_provides(self):
        self.provider.url_schemes = ['http://*.foo.com/bar']
        self.assertTrue(self.provider.match('http://sub.blah.foo.com/bar'))

    def test_match_does_not_provide(self):
        self.provider.url_schemes = ['http://*.foo.com/bar']
        self.assertFalse(self.provider.match('http://youtube.com/video'))


class InternalProviderTestCase(TestCase):

    def setUp(self):
        self.resource_url = 'http://example.com/resource'
        self.provider = InternalProvider()

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

        resource = self.provider._build_resource(**{'url': self.resource_url})

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
        self.provider._params['maxwidth'] = 100
        self.provider._params['maxheight'] = 100
        self.provider.author_name = 'John Galt'

        resource = self.provider._build_resource(**{'url': self.resource_url})

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
        setattr(settings, 'MONOCLE_CACHE_INTERNAL_PROVIDERS', True)

        resource = Resource(self.resource_url)
        resource.created = resource.created.replace(year=1984)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, False)
        self.provider._build_resource = Mock(return_value=resource)

        self.assertTrue(resource.is_stale)
        resource = self.provider.get_resource(self.resource_url)
        self.assertFalse(resource.is_stale)
        self.assertTrue(self.provider._build_resource.called)

    @patch('monocle.providers.cache')
    def test_get_resource_cached_is_primed(self, mock_cache):
        # Update django settings
        setattr(settings, 'MONOCLE_CACHE_INTERNAL_PROVIDERS', True)

        resource = Resource(self.resource_url)

        mock_cache.get_or_prime = mock_cache
        mock_cache.return_value = (resource, True)
        self.provider._build_resource = Mock(return_value=resource)

        self.assertFalse(resource.is_stale)
        resource = self.provider.get_resource(self.resource_url)
        self.assertFalse(resource.is_stale)
        self.assertTrue(self.provider._build_resource.called)

    def test_nearest_allowed_size_returns_original_size(self):
        self.provider.DIMENSIONS = [(50, 50), (100, 100), (200, 200)]
        self.assertEqual((25, 25), self.provider.nearest_allowed_size(25, 25))

    def test_nearest_allowed_size_returns_requested_max(self):
        self.provider.DIMENSIONS = [(150, 150), (200, 200)]

        nearest = self.provider.nearest_allowed_size(100, 100, maxwidth=50, maxheight=50)

        self.assertEqual((50, 50), nearest)

    def test_nearest_allowed_size_gets_nearest_size(self):
        self.provider.DIMENSIONS = [(50, 50), (100, 100), (200, 200)]

        nearest = self.provider.nearest_allowed_size(100, 100, maxwidth=500, maxheight=500)

        self.assertEqual((100, 100), nearest)


class TestInternalProvider(InternalProvider):
    url_schemes = ['http://test.biz/*']

    @classmethod
    def get_object(cls, url):
        return cls()


class ProviderRegistryTestCase(TestCase):

    def setUp(self):
        self.external = Provider()
        self.registry = ProviderRegistry()
        self.stored = self.make_provider()

    def tearDown(self):
        self.stored.delete()

    def make_provider(self):
        provider = ThirdPartyProvider.objects.create(api_endpoint='http://youtube.com/oembed',
                                                     resource_type='video')
        URLScheme.objects.create(scheme='http://*.youtube.com', provider=provider)
        return provider

    def test_provider_type_internal(self):
        self.assertEqual('internal', self.registry._provider_type(TestInternalProvider))

    def test_provider_type_external(self):
        self.assertEqual('external', self.registry._provider_type(self.external))

    def test_ensure_adds_stored(self):
        self.registry.ensure()
        self.assertIn(self.stored, self.registry)

    def test_update_adds_missing_from_signal(self):
        provider = ThirdPartyProvider(api_endpoint='http://example.com',
                                      resource_type='photo')
        self.assertNotIn(provider, self.registry)

        # Signal updates
        provider.save()

        self.assertIn(provider, self.registry)

    def test_update_adds_missing_internal(self):
        self.registry.clear()
        self.assertNotIn(TestInternalProvider, self.registry)
        self.registry.update(TestInternalProvider)
        self.assertIn(TestInternalProvider, self.registry)

    def test_update(self):
        self.registry.clear()
        self.registry.ensure()

        self.stored.foo = 'FOO'
        self.registry.update(self.stored)

        self.assertEqual(getattr(self.registry._providers['external'][0], 'foo', None), 'FOO')

    def test_unregister(self):
        self.registry.ensure()
        self.assertIn(self.stored, self.registry)
        self.registry.unregister(self.stored)

        self.assertNotIn(self.stored, self.registry._providers['internal'])
        self.assertNotIn(self.stored, self.registry._providers['external'])

    def test_register(self):
        self.registry.clear()
        self.assertNotIn(TestInternalProvider, self.registry)
        self.registry.register(TestInternalProvider)
        self.assertIn(TestInternalProvider, self.registry)

    def test_match_prefers_internal(self):
        self.registry.clear()
        self.registry.ensure()
        self.registry.register(TestInternalProvider)

        self.assertTrue(isinstance(self.registry.match('http://test.biz/foo'), TestInternalProvider))

    def test_match_has_no_match(self):
        self.assertIsNone(self.registry.match('FOO'))
