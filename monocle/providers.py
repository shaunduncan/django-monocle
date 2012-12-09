import re
import warnings

from urllib import urlencode

from django.template import Context
from django.template.loader import get_template

from monocle.cache import cache
from monocle.resources import Resource
from monocle.settings import settings
from monocle.tasks import request_external_oembed


class InvalidProvider(Exception):
    pass


class Provider(object):
    api_endpoint = None
    url_scheme = None
    resource_type = None
    expose = False  # Expose this provider externally

    def __init__(self, url, **kwargs):
        self._params = kwargs
        self._params['url'] = url
        self._params['format'] = 'json'

        # Prepare rege pattern substituting wildcards for non-greedy match-all
        self.url_re = re.compile(self.url_scheme.replace('*', '.*?'), re.I)

    def set_max_dimensions(self, width=None, height=None):
        if width:
            self._params['maxwidth']

        if height:
            self._params['maxheight']

    def get_resource(self):
        """Obtain the OEmbed resource JSON"""
        request_url = self.get_request_url()

        cached, primed = cache.get_or_prime(request_url, primer=Resource(self._params['url']))

        if primed or cached.is_stale:
            # Prevent many tasks being issued
            if cached.is_stale:
                cache.set(request_url, cached.fresh())

            request_external_oembed.apply_async(request_url)

        return cached

    def get_request_url(self):
        return '%s?%s' % (self.api_endpoint, urlencode(self._params))

    @property
    def maxwidth(self):
        return self._params.get('maxwidth', 0)

    @property
    def maxheight(self):
        return self._params.get('maxheight', 0)

    def match(self, url):
        return self.url_re.match(url)


class InternalProvider(Provider):
    """
    An internal provider that does not require any network operation.
    A lot of what should be done here is up to the implementer.
    """

    # A list of tuples of valid size dimensions: (width, height)
    DIMENSIONS = []

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
        attr = getattr(self, name, None)

        if attr is None and required:
            raise NotImplementedError
        elif callable(attr):
            return attr(self)
        else:
            return attr

    def nearest_allowed_size(self, width, height):
        """
        Get the nearest size dimension below a maximum dimension. The dimension
        threshold is the minimum of the specified size and requested maximum size.
        The return value will either be the largest allowed size below the maximum
        or will be the maximum if no allowed size can be found
        """
        maxdim = (width, height)

        if self.maxwidth:
            maxdim = (min(width, self.maxwidth), maxdim[1])

        if self.maxheight:
            maxdim = (maxdim[0], min(height, self.maxheight))

        dims = getattr(self, 'DIMENSIONS', settings.RESOURCE_DEFAULT_DIMENSIONS)
        smaller = lambda x, y: x[0] <= y[0] and x[1] <= y[1]
        valid_sizes = [d for d in dims if smaller(d, maxdim)]

        if valid_sizes:
            return sorted(valid_sizes, reverse=True)[0]
        else:
            return maxdim

    def _check_dimension(self, width, height, message=None):
        """
        Raises a warning with optional message if width and height exceeds the maximum
        allowable size as defined by this provider
        """
        new_width, new_height = self.nearest_allowed_size(width, height)
        if new_width < width or new_height < height:
            warnings.warn(message or 'Resource size exceeds allowable dimensions')

    def _build_resource(self):
        url = self._params['url']

        # These are always required
        data = {
            'type': self.resource_type,
            'version': '1.0'
        }

        # Apply required attributes by resource type
        for attr in settings.RESOURCE_REQUIRED_ATTRS.get(self.resource_type, []):
            data[attr] = self._data_attribute(attr, required=True)

        # Optional attributes
        for attr in settings.RESOURCE_OPTIONAL_ATTRS:
            data[attr] = self._data_attribute(attr)

        # Raise a warning if width/height exceed maximum requested and scale
        # TODO: I'm still not convinced this is the right way to handle this
        if 'width' in data and 'height' in data:
            self._check_dimension(data['width'], data['height'])

        if 'thumbnail_width' in data and 'thumbnail_height' in data:
            self._check_dimension(data['thumbnail_width'], data['thumbnail_height'],
                                  'Thumbnail size exceeds allowable dimensions')

        return Resource(url, data)

    def get_resource(self):
        url = self._params['url']

        if settings.CACHE_INTERNAL_PROVIDERS:
            cache_key = 'INTERNAL:%s' % url
            cached, primed = cache.get_or_prime(cache_key, primer=Resource(url))

            if primed or cached.is_stale:
                # This is just a safeguard in case the rebuild takes a little time
                if cached.is_stale:
                    cache.set(cache_key, cached.fresh())

                cached = self._build_resource()
                cache.set(cache_key, cached)

            return cached

        # No caching, build directly
        return self._build_resource()


class ProviderRegistry(object):
    """
    Storage mechanism for providers to quickly identify a match
    """
    # Separate internal and external providers. Prefer internal first
    _providers = {'internal': [], 'external': []}

    def ensure(self):
        if self._providers:
            return

        # BOO circular import prevention
        from monocle.models import ThirdPartyProvider

        # Populate with things we know about: models
        for provider in ThirdPartyProvider.objects.all():
            self.register(provider, ensure=False)

    def _provider_type(self, provider):
        """
        Resolves the provider type as internal or external
        """
        if isinstance(provider, InternalProvider):
            return 'internal'
        else:
            return 'external'

    def update(self, provider):
        """
        Updates an entry in the registry with one provided
        """
        self.ensure()
        type = self._provider_type(provider)

        try:
            idx = self._providers[type].index(provider)
        except ValueError:
            # Provider not in the registry
            self._providers[type].append(provider)
        else:
            self._providers[type][idx] = provider

    def unregister(self, provider):
        """
        Removes a provider from the registry.
        """
        self.ensure()
        type = self._provider_type(provider)

        try:
            self._providers[type].remove(provider)
        except ValueError:
            # Provider not in the list
            pass

    def match(self, url):
        """
        Locates the first provider that matches the URL. This
        prefers matching internal providers over external providers
        """
        self.ensure()

        return self.match_type(url, 'internal') or self.match_type(url, 'external')

    def match_type(self, url, type):
        """
        Searches the internal provider registry for a matching
        provider for the url based on type
        """
        for provider in self._providers[type]:
            if provider.match(url):
                return provider
        return None

    def register(self, provider, ensure=True):
        """
        Adds a provider to the internal registry. Must supply
        a valid instance of Provider
        """
        if ensure:
            self.ensure()

        if not isinstance(provider, Provider):
            raise InvalidProvider('Object %s is not a valid Provider type' % provider)

        type = self._provider_type(provider)
        self._providers[type].append(provider)


registry = ProviderRegistry()
