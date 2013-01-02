import json
import os

from datetime import datetime

from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from monocle.settings import settings


class Resource(object):
    """
    Basically a collection of OEmbed response data.
    """

    def __init__(self, url, data=None):
        self.url = url
        self.created = datetime.utcnow()
        self._data = data or {}

    def __getitem__(self, key):
        if key == 'cache_age':
            return self.ttl
        return self._data.get(key, '')

    def __setitem__(self, key, value):
        if key == 'cache_age':
            self.ttl = value
        else:
            self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    def render(self):
        """Render this resource to the correct template for proper embedding"""
        if not self.is_valid:
            if settings.RESOURCE_URLIZE_INVALID:
                template_name = 'monocle/link.html'
            else:
                return self.url
        else:
            template_name = os.path.join('monocle', '%s.html' % self._data['type'])

        template = get_template(template_name)
        return mark_safe(template.render(Context({'url': self.url, 'resource': self})))

    @property
    def is_valid(self):
        """
        Perform validation against this resource object. The resource is considered
        valid if it meets the following criteria:

        - It has oembed response data
        - It is a valid oembed resource type
        - It has the required attributes based on its type
        """
        # We can create resources without valid data
        if not self._data:
            return False

        # Must be a valid type
        if self._data.get('type') not in settings.RESOURCE_TYPES:
            return False

        # Must have required fields
        has_required = True
        for field in settings.RESOURCE_REQUIRED_ATTRS[self._data['type']]:
            has_required = has_required and (field in self._data)

        if not has_required:
            return False

        return True

    @property
    def is_stale(self):
        """
        Returns True if this resource's age since it was updated
        is greater than it's TTL
        """
        delta = datetime.utcnow() - self.created
        age = (delta.days * 60 * 60 * 24) + delta.seconds

        return age > self.ttl

    def refresh(self):
        """Returns a 'fresh' version of this resource (internal datetime is now)"""
        self.created = datetime.utcnow()
        return self

    @property
    def json(self):
        """Return JSON ouput minus any empty things"""
        return json.dumps(dict([(k, v) for k, v in self._data.items() if v]))

    def get_ttl(self):
        """
        Returns the TTL of this resource ensuring that it meets configurable
        minimum value. This value could be specified by the provider. If not
        a configurable default TTL is used
        """
        try:
            return max(settings.RESOURCE_MIN_TTL,
                       int(self._data.get('cache_age', settings.RESOURCE_DEFAULT_TTL)))
        except (ValueError, TypeError):
            return settings.RESOURCE_DEFAULT_TTL

    def set_ttl(self, value):
        try:
            value = max(settings.RESOURCE_MIN_TTL, int(value))
        except (ValueError, TypeError):
            value = settings.RESOURCE_DEFAULT_TTL
        self._data['cache_age'] = value

    ttl = property(get_ttl, set_ttl)
