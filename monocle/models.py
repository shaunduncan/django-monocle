from django.db import models

from monocle.providers import Provider
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
