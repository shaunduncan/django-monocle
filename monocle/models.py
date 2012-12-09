from django.db import models

from monocle.providers import Provider, registry
from monocle.settings import settings


RESOURCE_CHOICES = [(x, x.capitalize()) for x in settings.RESOURCE_TYPES]


class ThirdPartyProvider(models.Model, Provider):
    """
    Database-backed third-party provider configuration
    """
    url_scheme = models.CharField(max_length=255,
                                  help_text="Wildcard URL pattern: http://*.flickr.com/photos/*")
    api_endpoint = models.URLField(verify_exists=False)
    resource_type = models.CharField(choices=RESOURCE_CHOICES, max_length=10)
    is_active = models.BooleanField(default=True)
    expose = models.BooleanField(default=False,
                                 help_text="Expose this resource to external requests")

    class Meta:
        ordering = ('api_endpoint', 'resource_type')

    # TODO - Validation : the url_scheme must be valid according to spec
    # OK: http://www.flickr.com/photos/*
    # OK: http://www.flickr.com/photos/*/foo
    # OK: http://*.flickr.com/photos/*
    # NOT OK: https://www.flickr.com/photos/*
    # NOT OK: http://*.com/photos/*
    # NOT OK: *://www.flickr.com/photos/*


def _update_provider(sender, instance, created, **kwargs):
    """Post-save signal callback"""
    registry.update(instance)


def _unregister_provider(sender, instance, **kwargs):
    """Post-delete signal callback"""
    registry.unregister(instance)


# Connect signals
models.signals.post_save.connect(_update_provider, sender=ThirdPartyProvider)
models.signals.post_delete.connect(_unregister_provider, sender=ThirdPartyProvider)
