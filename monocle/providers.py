import logging
import re
import warnings

from urllib import urlencode

from django.template import Context
from django.template.loader import get_template

from monocle.cache import cache
from monocle.resources import Resource
from monocle.settings import settings
from monocle.tasks import request_external_oembed


logger = logging.getLogger(__name__)


class InvalidProvider(Exception):
    pass


class Provider(object):
    api_endpoint = None
    url_schemes = None
    resource_type = None
    expose = False  # Expose this provider externally

    @property
    def _internal(self):
        return False

    def get_resource(self, url, **kwargs):
        """Obtain the OEmbed resource JSON"""
        params = kwargs
        params['url'] = url
        params['format'] = 'json'

        request_url = self.get_request_url(params)
        logger.info('Obtaining OEmbed resource at %s' % request_url)

        cached, primed = cache.get_or_prime(request_url, primer=Resource(params['url']))

        if primed or cached.is_stale:
            # Prevent many tasks being issued
            if cached.is_stale:
                cache.set(request_url, cached.fresh())

            request_external_oembed.apply_async((request_url,))
            logger.info('Scheduled external request for OEmbed resource %s' % url)

        return cached

    def get_request_url(self, params):
        zeros = (0, '0', None)

        # Remove maxwidth/maxheight of "0"
        for param in ('maxwidth', 'maxheight'):
            if param in params and params[param] in zeros:
                del params[param]

        return '%s?%s' % (self.api_endpoint, urlencode(params))

    @classmethod
    def _schemes_to_regex_str(cls, schemes):
        """
        Replace wildcards with non-greedy dot-all and escape true '.'
        """
        regex = '(%s)' % '|'.join(map(str, schemes))
        regex = regex.replace('.', '\\.').replace('*', '.*?')

        return regex

    def match(self, url):
        if self.url_schemes and len(self.url_schemes):
            return re.match(self._schemes_to_regex_str(self.url_schemes), url, re.I)
        else:
            logger.warning('No URL schemes defined for provider %s' % self.__class__.__name__)
            return False

    def nearest_allowed_size(self, width, height, maxwidth=None, maxheight=None):
        """
        Get the nearest size dimension below a maximum dimension. The dimension
        threshold is the minimum of the specified size and requested maximum size.
        The return value will either be the largest allowed size below the maximum
        or will be the maximum if no allowed size can be found
        """
        logger.debug('Resizing (%s, %s) to nearest allowed size' % (width, height))
        maxdim = (width, height)

        if maxwidth and width > maxwidth:
            logger.debug('Width exceeds maxwidth %s' % maxwidth)
            maxdim = (maxwidth, maxdim[1])

        if maxheight and height > maxheight:
            logger.debug('Height exceeds maxheight %s' % maxheight)
            maxdim = (maxdim[0], maxheight)

        dims = getattr(self, 'DIMENSIONS', settings.RESOURCE_DEFAULT_DIMENSIONS)
        smaller = lambda x, y: x[0] <= y[0] and x[1] <= y[1]
        valid_sizes = [d for d in dims if smaller(d, maxdim)]

        if valid_sizes:
            valid_sizes.sort(reverse=True)
            logger.debug('Nearest allowed size for %s: %s' % (maxdim, valid_sizes))
            return valid_sizes[0]
        else:
            logger.debug('No appropriate size found. Returning default %s' % (maxdim,))
            return maxdim


class InternalProvider(Provider):
    """
    An internal provider that does not require any network operation.
    A lot of what should be done here is up to the implementer.
    """

    # A list of tuples of valid size dimensions: (width, height)
    DIMENSIONS = []

    html_template = None
    expose = settings.EXPOSE_LOCAL_PROVIDERS
    api_endpoint = 'http://localhost/'

    # Internal providers are specific instances
    _params = {}

    @classmethod
    def get_object(cls, url):
        """
        Internal providers should instance specific. Any internal provider
        in the registry will invoke this method to get a specific instance
        to handle OEmbed requests
        """
        raise NotImplementedError

    @classmethod
    def match(cls, url):
        if cls.url_schemes and len(cls.url_schemes):
            return re.match(cls._schemes_to_regex_str(cls.url_schemes), url, re.I)
        else:
            logger.warning('No URL schemes defined for provider %s' % cls.__name__)
            return False

    @property
    def _internal(self):
        return True

    def render_html(self, data):
        """
        Helper to directly render data to the html_template of this provider
        """
        if not self.html_template:
            return ''

        template = get_template(self.html_template)
        return template.render(Context(data))

    @property
    def maxwidth(self):
        return self._params.get('maxwidth', getattr(self, 'DEFAULT_WIDTH', None))

    @property
    def maxheight(self):
        return self._params.get('maxheight', getattr(self, 'DEFAULT_HEIGHT', None))

    def width(self):
        # TODO: Is this the right way to handle this? Expensive?
        return self.nearest_allowed_size(self.maxwidth, self.maxheight)[0]

    def height(self):
        # TODO: Is this the right way to handle this? Expensive?
        return self.nearest_allowed_size(self.maxwidth, self.maxheight)[1]

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
            return attr()
        else:
            return attr

    def _check_dimension(self, width, height, maxwidth=None, maxheight=None, message=None):
        """
        Raises a warning with optional message if width and height exceeds the maximum
        allowable size as defined by this provider
        """
        new_width, new_height = self.nearest_allowed_size(width, height,
                                                          maxwidth=maxwidth,
                                                          maxheight=maxheight)
        if new_width < width or new_height < height:
            warnings.warn(message or 'Resource size exceeds allowable dimensions')

    def _build_resource(self, **kwargs):
        # These are always required
        url = kwargs.get('url')
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
        if settings.RESOURCE_CHECK_INTERNAL_SIZE:
            if 'width' in data and 'height' in data:
                self._check_dimension(data['width'], data['height'],
                                      maxwidth=kwargs.get('maxwidth'),
                                      maxheight=kwargs.get('maxheight'))

            if 'thumbnail_width' in data and 'thumbnail_height' in data:
                self._check_dimension(data['thumbnail_width'], data['thumbnail_height'],
                                      maxwidth=kwargs.get('maxwidth'),
                                      maxheight=kwargs.get('maxheight'),
                                      message='Thumbnail size exceeds allowable dimensions')

        return Resource(url, data)

    def get_resource(self, url, **kwargs):
        self._params = kwargs
        self._params['url'] = url
        self._params['format'] = 'json'

        if settings.CACHE_INTERNAL_PROVIDERS:
            cache_key = self.get_request_url(self._params)
            logger.debug('Checking InternalProvider cache for key %s' % cache_key)
            cached, primed = cache.get_or_prime(cache_key, primer=Resource(url))

            if primed or cached.is_stale:
                logger.debug('Rebuilding new or stale internal provider resource at %s' % url)
                # This is just a safeguard in case the rebuild takes a little time
                if cached.is_stale:
                    cache.set(cache_key, cached.fresh())

                cached = self._build_resource(**self._params)
                cache.set(cache_key, cached)

            return cached

        # No caching, build directly
        return self._build_resource(**self._params)


class ProviderRegistry(object):
    """
    Storage mechanism for providers to quickly identify a match
    """
    # Separate internal and external providers. Prefer internal first
    _providers = {'internal': [], 'external': []}

    def __contains__(self, provider):
        return provider in self._providers[self._provider_type(provider)]

    def ensure(self):
        # BOO circular import prevention
        from monocle.models import ThirdPartyProvider

        # Populate with things we know about: models
        self._providers['external'] = list(ThirdPartyProvider.objects.all())

    def _provider_type(self, provider):
        """
        Resolves the provider type as internal or external
        """
        return 'internal' if provider._internal else 'external'

    def clear(self):
        """Clears the internal provider registry"""
        self._providers = {'internal': [], 'external': []}

    def update(self, provider):
        """
        Updates an entry in the registry with one provided
        """
        type = self._provider_type(provider)

        try:
            idx = self._providers[type].index(provider)
        except ValueError:
            # Provider not in the registry
            self._providers[type].append(provider)
            logger.debug('Adding provider %s to %s registry' % (provider, type))
        else:
            self._providers[type][idx] = provider
            logger.debug('Updating provider %s to %s registry' % (provider, type))

    def unregister(self, provider):
        """
        Removes a provider from the registry.
        """
        type = self._provider_type(provider)

        logger.debug('Removing provider %s to %s registry' % (provider, type))

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
        logger.debug('Locating provider match for %s' % url)
        return self.match_type(url, 'internal') or self.match_type(url, 'external')

    def match_type(self, url, type):
        """
        Searches the internal provider registry for a matching
        provider for the url based on type
        """
        matched = None

        for provider in self._providers[type]:
            if provider.match(url):
                matched = provider
                break

        # If the match is internal, obtain specific instance
        if matched and hasattr(matched, 'get_object'):
            try:
                matched = matched.get_object(url)
            except Exception:
                logger.exception('InternalProvider %s get_object failed' % matched)
                matched = None

        return matched

    def register(self, provider):
        """
        Adds a provider to the internal registry. Must supply
        a valid instance of Provider
        """
        if not isinstance(provider, Provider):
            try:
                if not issubclass(provider, InternalProvider):
                    raise InvalidProvider('Object %s is not a valid Provider type' % provider)
            except TypeError:
                raise InvalidProvider('Object %s is not a valid Provider type' % provider)

        type = self._provider_type(provider)
        self._providers[type].append(provider)
        logger.debug('Adding provider %s to %s registry' % (provider, type))


registry = ProviderRegistry()
