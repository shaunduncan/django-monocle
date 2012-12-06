import json

from monocle.settings import settings


class Resource(object):
    """
    Basically a collection of OEmbed response data.
    """
    _data = {}

    def __init__(self, url, data=None):
        self.url = url
        if data:
            self._data = data

    def __getattr__(self, attr):
        if attr == 'cache_age':
            return self.ttl
        return self._data.get(attr)

    def __setattr__(self, attr, value):
        if attr == 'cache_age':
            self.ttl = value
        else:
            self._data[attr] = value

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
        except ValueError:
            return settings.RESOURCE_DEFAULT_TTL

    def set_ttl(self, value):
        try:
            value = max(settings.RESOURCE_MIN_TTL, int(value))
        except ValueError:
            value = settings.RESOURCE_DEFAULT_TTL
        self._data['cache_age'] = value

    ttl = property(get_ttl, set_ttl)

    # TODO: Need creation date and a way to check if expired
