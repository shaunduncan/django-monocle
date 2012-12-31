import re

from urlparse import urlparse

from django.core.exceptions import ValidationError
from django.db import models

from monocle.providers import Provider, registry
from monocle.settings import settings


RESOURCE_CHOICES = [(x, x.capitalize()) for x in settings.RESOURCE_TYPES]


class ThirdPartyProvider(models.Model, Provider):
    """
    Database-backed third-party provider configuration
    """
    name = models.CharField(max_length=50, blank=True)
    api_endpoint = models.URLField(verify_exists=False)
    resource_type = models.CharField(choices=RESOURCE_CHOICES, max_length=10)
    is_active = models.BooleanField(default=True)
    expose = models.BooleanField(default=False,
                                 help_text="Expose this resource to external requests")

    class Meta:
        ordering = ('api_endpoint', 'resource_type')

    @property
    def url_schemes(self):
        return list(self._schemes.all())

    def clean(self):
        """Ensures the API endpoint is valid"""
        if not self.api_endpoint:
            raise ValidationError('API Endpoint is required')

        if self.api_endpoint.lower().startswith('https'):
            raise ValidationError('API Endpoint cannot be a HTTPS endpoint')

    def __unicode__(self):
        return self.name or self.api_endpoint


class URLScheme(models.Model):
    scheme = models.CharField(max_length=255, unique=True,
                              help_text="Wildcard URL pattern: http://*.flickr.com/photos/*")
    provider = models.ForeignKey('ThirdPartyProvider', related_name='_schemes')

    def clean(self):
        """
        Validate the URL scheme according to these examples

        OK: http://www.flickr.com/photos/*
        OK: http://www.flickr.com/photos/*/foo
        OK: http://*.flickr.com/photos/*
        OK: https://www.flickr.com/photos/*
        NOT OK: http://*.com/photos/*
        NOT OK: *://www.flickr.com/photos/*
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
    registry.update(instance)


def _unregister_provider(sender, instance, **kwargs):
    """Post-delete signal callback"""
    registry.unregister(instance)


# Connect signals
models.signals.post_save.connect(_update_provider, sender=ThirdPartyProvider)
models.signals.post_delete.connect(_unregister_provider, sender=ThirdPartyProvider)


# Prepopulate
registry.ensure()
