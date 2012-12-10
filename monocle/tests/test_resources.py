from unittest2 import TestCase

from django.conf import settings as _settings

from monocle.resources import Resource
from monocle.settings import settings


class ResourceTestCase(TestCase):

    def setUp(self):
        self.resource_url = 'http://example.com'
        self.resource = Resource(self.resource_url)

    def _set_ttl_settings(self, min=100, default=1000):
        setattr(_settings, 'MONOCLE_RESOURCE_MIN_TTL', min)
        setattr(_settings, 'MONOCLE_RESOURCE_DEFAULT_TTL', default)

    def test_get_ttl_uses_min_ttl(self):
        self._set_ttl_settings()
        self.resource['cache_age'] = 1
        self.assertEqual(settings.RESOURCE_MIN_TTL, self.resource.get_ttl())

    def test_get_ttl_uses_default_ttl(self):
        if 'cache_age' in self.resource:
            del self.resource._data['cache_age']
        self._set_ttl_settings()
        self.assertEqual(settings.RESOURCE_DEFAULT_TTL, self.resource.get_ttl())

    def test_get_ttl_uses_default_ttl_on_error(self):
        self._set_ttl_settings()
        self.resource['cache_age'] = 'FOO'
        self.assertEqual(settings.RESOURCE_DEFAULT_TTL, self.resource.get_ttl())

    def test_set_ttl_uses_min_ttl(self):
        self._set_ttl_settings()
        self.resource.set_ttl(settings.RESOURCE_MIN_TTL - 1)
        self.assertEqual(self.resource.ttl, settings.RESOURCE_MIN_TTL)

    def test_set_ttl_uses_default_ttl_on_error(self):
        self._set_ttl_settings()
        self.resource.set_ttl('FOO')
        self.assertEqual(self.resource.ttl, settings.RESOURCE_DEFAULT_TTL)

    def test_is_stale(self):
        self.resource.ttl = 3600
        self.assertFalse(self.resource.is_stale)

        # Make it stale
        self.resource.created = self.resource.created.replace(year=1984)
        self.assertTrue(self.resource.is_stale)

    def test_is_valid_has_required_attrs(self):
        self.resource._data = {
            'type': 'video',
            'html': 'foo',
            'width': 100,
            'height': 100
        }
        self.assertTrue(self.resource.is_valid)

    def test_is_valid_missing_required(self):
        self.resource._data = {
            'type': 'video',
            'html': 'foo',
        }
        self.assertFalse(self.resource.is_valid)

    def test_is_valid_invalid_type(self):
        self.resource._data = {
            'type': 'flash'
        }
        self.assertFalse(self.resource.is_valid)

    def test_render_urlizes(self):
        setattr(_settings, 'MONOCLE_RESOURCE_URLIZE_INVALID', True)
        self.assertIn('href="%s"' % self.resource.url, self.resource.render())

    def test_render_does_not_urlize(self):
        setattr(_settings, 'MONOCLE_RESOURCE_URLIZE_INVALID', False)
        self.assertEqual(self.resource.url, self.resource.render())

    def test_render_correct_for_type(self):
        # Photo render <img/>
        self.resource._data = {
            'type': 'photo',
            'url': 'http://foo.com/test.jpg',
            'width': 100,
            'height': 200
        }
        self.assertIn('<img src="http://foo.com/test.jpg"', self.resource.render())

        # Rich/Video just handoff `html`
        self.resource._data = {
            'type': 'video',
            'html': 'FooBar HTML Content',
            'width': 100,
            'height': 100
        }
        self.assertIn('FooBar HTML Content', self.resource.render())
