from urllib import urlencode

from django.core.cache import cache
from django.template import Context
from django.template.loader import get_template

from monocle.cache import get_or_prime, make_key
from monocle.resources import Resource
from monocle.settings import settings
from monocle.tasks import request_external_oembed


class Provider(object):
    api_endpoint = None
    url_scheme = None
    resource_type = None
    expose = False  # Expose this provider externally

    def __init__(self, url, **kwargs):
        self._params = kwargs
        self._params['url'] = url
        self._params['format'] = 'json'

    def get_resource(self):
        """Obtain the OEmbed resource JSON"""
        request_url = self.get_request_url()

        cached, primed = get_or_prime(request_url, primer=Resource(self._params['url']))

        if primed or cached.is_stale:
            request_external_oembed.apply_async(request_url)

        return cached

    def get_request_url(self):
        return '%s?%s' % (self.api_endpoint, urlencode(self._params))

    @property
    def maxwidth(self):
        return self._params.get('maxwidth')

    @property
    def maxheight(self):
        return self._params.get('maxheight')


class InternalProvider(Provider):
    """
    An internal provider that does not require any network operation.
    A lot of what should be done here is up to the implementer
    """
    html_template = None
    expose = settings.EXPOSE_LOCAL_PROVIDERS

    def render_html(self, data):
        """
        Helper to directly render data to the html_template of this provider
        """
        if not self.html_template:
            return ''

        template = get_template(self.html_template)
        return template.render(Context(data))

    def _data_attribute(self, name, required=False):
        """
        Gets an attribute as should be defined by an implementer.
        Raises NotImplementedError if required by resource type but not
        implemented and indicated as required

        Example:

        class VideoProvider(LocalProvider):
            resource_type = 'video'
            html_template = 'path/to/embed/template.html'

            def html(self):
                return self.render_html(data)

            @property
            def width(self):
                return 100

            @property
            def height(self):
                return 100
        """
        attr = getattr(self, name)

        if attr is None and required:
            raise NotImplementedError
        elif callable(attr):
            return attr(self)
        else:
            return attr

    def resize_maybe(self, width, height):
        # TODO: How should this work??
        pass

    def get_resource(self):
        url = self._params['url']
        cache_key = 'INTERNAL:%s' % url

        if settings.CACHE_LOCAL_PROVIDERS:
            cached, primed = get_or_prime(cache_key, primer=Resource(url))
            if not primed:
                return cached

        # These are always required
        data = {
            'type': self.resource_type,
            'version': '1.0'
        }

        # Apply required attributes by resource type
        for attr in settings.RESOURCE_REQUIRED_ATTRS[self.resource_type]:
            data[attr] = self._data_attribute(attr, required=True)

        # Optional attributes
        for attr in settings.RESOURCE_OPTIONAL_ATTRS:
            data[attr] = self._data_attribute(attr)

        # TODO : CONSTRAIN TO MAXWIDTH/MAXHEIGHT

        resource = Resource(url, data)

        if settings.CACHE_LOCAL_PROVIDERS:
            cache.set(cache_key, resource, timeout=resource.ttl)

        return resource
