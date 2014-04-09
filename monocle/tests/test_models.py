from unittest import TestCase

from monocle.models import ThirdPartyProvider, URLScheme


class ModelsTestCase(TestCase):

    def setUp(self):
        # Create a provider
        self.provider = ThirdPartyProvider(name='test',
                                           resource_type='rich',
                                           is_active=True,
                                           expose=True)
        self.provider.save()

        # Add URLSchemes
        self.scheme, created = URLScheme.objects.get_or_create(
            scheme='foo',
            defaults={'provider': self.provider}
        )

        if not created:
            self.scheme.provider = self.provider
            self.scheme.save()

    def tearDown(self):
        self.scheme.delete()
        self.provider.delete()

    def test_url_schemes_property_cached(self):
        assert not hasattr(self.provider, '_url_schemes')
        self.provider.url_schemes
        assert self.provider._url_schemes == [u'foo']

    def test_provider_post_save_signal_invalidates_cache(self):
        self.provider.url_schemes
        assert hasattr(self.provider, '_url_schemes')

        self.provider.save()
        assert not hasattr(self.provider, '_url_schemes')

    def test_scheme_post_save_signal_invalidates_cache(self):
        self.provider.url_schemes
        assert hasattr(self.provider, '_url_schemes')

        self.scheme.save()
        assert not hasattr(self.provider, '_url_schemes')
