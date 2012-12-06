import json

from datetime import datetime

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
        return self._data.get(key)

    def __setitem__(self, key, value):
        if key == 'cache_age':
            self.ttl = value
        else:
            self._data[key] = value

    def __contains__(self, key):
        return key in self._data

    @property
    def is_stale(self):
        """
        Returns True if this resource's age since it was updated
        is greater than it's TTL
        """
        delta = datetime.utcnow() - self.created
        age = (delta.days * 60 * 60 * 24) + delta.seconds

        return age > self.ttl

    def fresh(self):
        """Returns a 'fresh' version of this resource (internal datetime is now)"""
        self.created = datetime.utcnow()
        return self

    @property
    def json(self):
        return json.dumps(self._data)

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
