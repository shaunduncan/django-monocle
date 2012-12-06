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
