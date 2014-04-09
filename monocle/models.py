import re

from distutils.version import LooseVersion
from urlparse import urlparse

from django import get_version as django_version
from django.core.exceptions import ValidationError
from django.db import models

from monocle.providers import Provider, registry
from monocle.settings import settings

RESOURCE_CHOICES = [(x, x.capitalize()) for x in settings.RESOURCE_TYPES]


class ThirdPartyProvider(models.Model, Provider):
    """
    Database-backed third-party provider configuration. These are considered by
    monocle to be endpoint configuration of external providers. This model utilizes
    signals to ensure that the internal :class:`monocle.providers.ProviderRegistry`
    is maintained in a current state.
    """
    name = models.CharField(max_length=50, blank=True)
    resource_type = models.CharField(choices=RESOURCE_CHOICES, max_length=10)
    is_active = models.BooleanField(default=True, db_index=True)
    expose = models.BooleanField(default=False, db_index=True,
                                 help_text="Expose this resource to external requests")

    # verify_exists deprecated in >= 1.4
    if LooseVersion(django_version()) < LooseVersion('1.4'):
        api_endpoint = models.URLField(verify_exists=False)
    else:
        api_endpoint = models.URLField()

    class Meta:
        ordering = ('api_endpoint', 'resource_type')

    @property
    def url_schemes(self):
        if not hasattr(self, '_url_schemes'):
            self._url_schemes = list(self._schemes.values_list('scheme', flat=True))
        return self._url_schemes

    def clean(self):
        """
        Ensures the API endpoint is valid according to OEmbed spec, which is only that
        the endpoint cannot be HTTPS
        """
        if not self.api_endpoint:
            raise ValidationError('API Endpoint is required')

        if self.api_endpoint.lower().startswith('https'):
            raise ValidationError('API Endpoint cannot be a HTTPS endpoint')

    def __unicode__(self):
        return self.name or self.api_endpoint

    def invalidate_scheme_cache(self):
        """
        To reduce unnecessary database trips, url schemes are cached in memory.
        This will invalidate that cache.
        """
        if hasattr(self, '_url_schemes'):
            delattr(self, '_url_schemes')


class URLScheme(models.Model):
    """
    Asterisk wildcard URL that represents patterns a :class:`ThirdPartyProvider` is a valid
    provider for
    """
    scheme = models.CharField(max_length=255, unique=True,
                              help_text="Wildcard URL pattern: http://*.flickr.com/photos/*")
    provider = models.ForeignKey('ThirdPartyProvider', related_name='_schemes')

    def clean(self):
        """
        Validate the URL scheme according to these examples from the
        `OEmbed Spec <http://oembed.com>`_

        Valid Schemes

        * ``http://www.flickr.com/photos/*``
        * ``http://www.flickr.com/photos/*/foo``
        * ``http://*.flickr.com/photos/*``
        * ``https://www.flickr.com/photos/*``

        Invalid Schemes

        * ``http://*.com/photos/*``
        * ``*://www.flickr.com/photos/*``
        """
        if not self.scheme:
            raise ValidationError('URL Scheme is required')

        parts = urlparse(self.scheme.lower())

        if not parts.scheme:
            raise ValidationError('URL Scheme cannot be a wildcard')

        if re.match(r'\*\.?(\w{3}|(\w{2}\.)?\w{2})$', parts.netloc):
            raise ValidationError('URL Scheme is too agressive')

        if not self.provider:
            raise ValidationError('This URL Scheme must belong to a provider')

    def __unicode__(self):
        return self.scheme


def _update_provider(sender, instance, created, **kwargs):
    """Post-save signal callback"""
    instance.invalidate_scheme_cache()
    registry.update(instance)


def _unregister_provider(sender, instance, **kwargs):
    """Post-delete signal callback"""
    registry.unregister(instance)


def _invalidate_provider_schemes(sender, instance, created, **kwargs):
    # Invalidate the related object cache
    instance.provider.invalidate_scheme_cache()


# Connect signals
models.signals.post_save.connect(_update_provider, sender=ThirdPartyProvider)
models.signals.post_save.connect(_invalidate_provider_schemes, sender=URLScheme)

models.signals.post_delete.connect(_unregister_provider, sender=ThirdPartyProvider)


# Prepopulate
registry.ensure_populated()
