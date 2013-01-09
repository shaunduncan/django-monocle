import json
import os

from datetime import datetime

from django.template import Context
from django.template.loader import get_template
from django.utils.safestring import mark_safe

from monocle.settings import settings


class Resource(object):
    """
    A JSON compatible response from an OEmbed provider
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
        """
        Renders this resource to the template corresponding to this resource type.
        The template is rendered with variables ``url`` and ``resource`` that represent
        the original requested URL and this resource respectively.

        If the resource is considered invalid from :func:`is_valid`, the original
        requested URL is returned unless ``RESOURCE_URLIZE_INVALID`` is configured
        in :mod:`monocle.settings`. If so, then the original URL is returned hyperlinked

        :returns: Rendered oembed content
        """
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

        * It has oembed response data
        * It is a valid oembed resource type
        * It has the required attributes based on its type
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
        True of the current timestamp is greater than the sum of the resource's
        creation timestamp plus its TTL, False otherwise.
        """
        delta = datetime.utcnow() - self.created
        age = (delta.days * 60 * 60 * 24) + delta.seconds

        return age > self.ttl

    def refresh(self):
        """
        Returns a version of this resource that is considered fresh by updating
        its internal timestamp to now
        """
        self.created = datetime.utcnow()
        return self

    @property
    def json(self):
        """
        A JSON string without any empty or null keys
        """
        return json.dumps(dict([(k, v) for k, v in self._data.items() if v]))

    def get_ttl(self):
        """
        Returns the TTL of this resource ensuring that it at minimum the value
        of ``RESOURCE_MIN_TTL`` from :mod:`monocle.settings`.

        This value could be specified by the provider via the property ``cache_age``.
        If it is not, the value ``RESOURCE_DEFAULT_TTL`` from :mod:`monocle.settings`
        is used.

        :returns: TTL in seconds
        """
        try:
            return max(settings.RESOURCE_MIN_TTL,
                       int(self._data.get('cache_age', settings.RESOURCE_DEFAULT_TTL)))
        except (ValueError, TypeError):
            return settings.RESOURCE_DEFAULT_TTL

    def set_ttl(self, value):
        """
        Sets the TTL value of this resource ensuring that it is at minimum the value
        of ``RESOURCE_MIN_TTL`` from :mod:`monocle.settings`. If it is not, the value
        of ``RESOURCE_DEFAULT_TTL`` from :mod:`monocle.settings` is used.
        """
        try:
            value = max(settings.RESOURCE_MIN_TTL, int(value))
        except (ValueError, TypeError):
            value = settings.RESOURCE_DEFAULT_TTL
        self._data['cache_age'] = value

    ttl = property(get_ttl, set_ttl)
