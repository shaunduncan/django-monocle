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
from monocle.util import synced


logger = logging.getLogger(__name__)


class InvalidProvider(Exception):
    """
    General purpose exception used to indicated a provider is misconfigured
    """
    pass


class Provider(object):
    """
    A Provider is essentially an OEmbed endpoint that, well, provides
    rich content to a consumer. Providers are aware of URL patterns of
    rich content they provide and what URL endpoint should be contacted
    to retrieve a resource for OEmbedding.

    Monocle providers should be configured to expose an attribute representing
    the type of content they provide. Valid options are:

    * rich
    * link
    * video
    * photo

    Monocle providers are also optionally exposed from a django url (configured
    in :mod:`monocle.urls`). Exposing monocle providers allows external sources
    to consume rich content from django
    """
    api_endpoint = None
    url_schemes = None
    resource_type = None
    expose = False  # Expose this provider externally
    _internal = False

    def get_resource(self, url, **kwargs):
        """
        Obtain an OEmbed resource JSON

        :param string url: Requested rich content URL
        :param kwargs: Optional arguments along with this request.
                       Currently only ``maxwidth`` and ``maxheight`` supported.
        :returns: :class:`monocle.resources.Resource`

        .. note::
            Currently only JSON-compatible requests are honored. If a request is
            made for an XML resource, it will still return a JSON resource
        """
        params = kwargs
        params['url'] = url

        # Only support JSON format
        params['format'] = 'json'

        request_url = self.get_request_url(**params)
        logger.info('Obtaining OEmbed resource at %s' % request_url)

        cached, primed = cache.get_or_prime(request_url, primer=Resource(params['url']))

        if primed or cached.is_stale:
            # Prevent many tasks being issued
            if cached.is_stale:
                cache.set(request_url, cached.refresh())

            request_external_oembed.apply_async((request_url,))
            logger.info('Scheduled external request for OEmbed resource %s' % url)

        return cached

    def get_request_url(self, **params):
        """
        Constructs a request URL to the provider API endpoint with kwargs
        as URL parameters. Removes maxwidth and maxheight if they are like
        zero (i.e 0, '0' or None)

        :returns: Escaped endpoint url
        """
        zeros = (0, '0', None)

        # Remove maxwidth/maxheight of "0"
        for param in ('maxwidth', 'maxheight'):
            if param in params and params[param] in zeros:
                del params[param]

        return '%s?%s' % (self.api_endpoint, urlencode(params))

    @classmethod
    def schemes_to_regex_str(cls, schemes):
        """
        Replace wildcards with non-greedy dot-all and escaped true dots.
        Since many providers may honor several URL patterns for content they
        serve, this will essentially create a single regular expression that
        can test all of them simultaneously.

        For Example

        >>> cls.schemes_to_regex_str(['http://foo.com/a/*', 'http://foo.com/b/*'])
        "(http://foo.com/a/.\*?|http://foo.com/b/.\*?|http://foo.com/c/.\*?)"

        :param list schemes: URL pattern strings
        :returns: A single regex string
        """
        regex = '(%s)' % '|'.join(map(str, schemes))
        regex = regex.replace('.', '\\.').replace('*', '.*?')

        return regex

    def match(self, url):
        """
        Tests a url against the url schemes of a provider instance

        :param string url: URL to test
        :returns: Bool False if provider has no schemes, None if no match found,
                  a python re match if found
        """
        if self.url_schemes:
            return re.match(self.schemes_to_regex_str(self.url_schemes), url, re.I)
        else:
            logger.warning('No URL schemes defined for provider %s' % self.__class__.__name__)
            return False

    def nearest_allowed_size(self, width, height, maxwidth=None, maxheight=None):
        """
        Obtain a 'nearest size' that is just below a specific maximum. In other words,
        this is min(current_size, max_size). This will scan either the provider's
        ``DIMENSION`` attribute (a list of int two-tuples representing valid sizes) or
        ``RESOURCE_DEFAULT_DIMENSIONS`` configured in :mod:`monocle.settings`.

        :param integer width: Current width integer
        :param integer height: Current height integer
        :param integer maxwidth: Maximum width integer to constrain within
        :param integer maxheight: Maximum height integer to constrain within
        :returns: Size as integer two-tuple (width, height). This is either
                  largest allowable size or the default maximum if no allowable size
                  found
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
    An internal provider is meant as a means to abstract locally provided
    rich content resources. In essence, this means that these type of providers
    require no network operations. Instead, implementers should provide a specific
    mechanism to retrieve an object-specific instance :func:`get_object`.

    Properly implemented providers should follow a basic contract

    * Implement :func:`get_object` as a means to convert a URL to an instance
    * Define attribute ``DIMENSIONS`` of integer two-tuples
    * Define attribute ``html_template`` that is a str template path used to render
      object specific HTML for embedding
    * Define attribute ``url_schemes`` as a list of asterisk wildcard URL patterns
    * Define attribute ``resource_type`` that is a valid OEmbed type
    * Define attributes ``DEFAULT_WIDTH`` and ``DEFAULT_HEIGHT`` as fallback
      dimensions in case oembed consumers do not specify maximum dimensions

    Providers should also define properties or methods the correspond
    to names of OEmbed resource attributes. These are listed in :mod:`monocle.settings`
    under ``RESOURCE_REQUIRED_ATTRS`` and ``RESOURCE_OPTIONAL_ATTRS``.

    Implementations are not automatically must be added manually via
    :class:`ProviderRegistry`:

        from monocle.providers import registry
        registry.register(MyInternalProvider)
    """

    # A list of tuples of valid size dimensions: (width, height)
    DIMENSIONS = []

    html_template = None
    expose = settings.EXPOSE_LOCAL_PROVIDERS
    api_endpoint = 'http://localhost/'
    _internal = True

    # Internal providers are specific instances
    _params = {}

    @classmethod
    def get_object(cls, url):
        """
        A mechanism to convert a URL for some rich content and return a specific
        instance of InternalProvider. This should be implemented by subclasses
        of :class:`InternalProvider` otherwise NotImplementedError will be raised.
        Implementers should ensure this method returns a provider instance or None
        if no suitable provider can be found for the given URL.

        :param string url: URL to convert to provider instance
        :returns: A provider instance or None
        """
        raise NotImplementedError

    @classmethod
    def match(cls, url):
        if cls.url_schemes:
            return re.match(cls.schemes_to_regex_str(cls.url_schemes), url, re.I)
        else:
            logger.warning('No URL schemes defined for provider %s' % cls.__name__)
            return False

    def render_html(self, data):
        """
        Helper to directly render data to the html_template of this provider.

        :param dict data: Data that is passed directly to the template as a context
        :returns: Rendered template
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

        Example::

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
        """
        Constructs a valid JSON resource response complying to OEmbed spec based
        on the attributes exposed by the provider
        """
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

        # Only support JSON format
        self._params['format'] = 'json'

        if settings.CACHE_INTERNAL_PROVIDERS:
            cache_key = self.get_request_url(**self._params)
            logger.debug('Checking InternalProvider cache for key %s' % cache_key)
            cached, primed = cache.get_or_prime(cache_key, primer=Resource(url))

            if primed or cached.is_stale:
                logger.debug('Rebuilding new or stale internal provider resource at %s' % url)
                # This is just a safeguard in case the rebuild takes a little time
                if cached.is_stale:
                    cache.set(cache_key, cached.refresh())

                cached = self._build_resource(**self._params)
                cache.set(cache_key, cached)

            return cached

        # No caching, build directly
        return self._build_resource(**self._params)


class ProviderRegistry(object):
    """
    An in-memory storage mechanism for all provider implementations.
    Currently, external providers are pre-populated as instances of
    :class:`ThirdPartyProvider`. Implementations of :class:`InternalProvider`
    need to be manually added to registry::

        from monocle.providers import registry
        registry.register(MyProvider)
    """
    # Separate internal and external providers. Prefer internal first
    _providers = {'internal': [], 'external': []}

    def __contains__(self, provider):
        """
        Checks if a provider instance or class is in the registry

        :param provider: A :class:`Provider` instance or subclass
        :returns: True if in registry, False otherwise
        """
        return provider in self._providers[self._provider_type(provider)]

    def ensure_populated(self):
        """
        Ensures the external provider cache is pre-populated with all external
        provider instances. This will run only if the internal cache of external
        providers is empty
        """
        # BOO circular import prevention
        from monocle.models import ThirdPartyProvider

        # Models have post_save/delete signals. We only need to ensure once
        if self._providers['external']:
            return

        # Populate with things we know about: models - ONLY IF THE DB IS SYNCED
        if synced(ThirdPartyProvider):
            self._providers['external'] = list(ThirdPartyProvider.objects.all())

    def _provider_type(self, provider):
        """
        Resolves the provider type as internal or external. This is done
        by checking the ``_internal`` attribute of the given parameter

        :param provider: A :class:`Provider` instance or subclass
        :returns: str 'internal' if an internal provider, str 'external' otherwise
        """
        return 'internal' if provider._internal else 'external'

    def clear(self):
        """
        Clears the internal provider registry
        """
        self._providers = {'internal': [], 'external': []}

    def update(self, provider):
        """
        Updates an entry in the registry with one provided. If the provider
        does not exist in the registry, it is silently added.

        :param provider: A :class:`Provider` instance or subclass
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

        :param provider: A :class:`Provider` instance or subclass
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

        :param string url: URL to match a provider against
        :returns: A provider instance or None if no match is found
        """
        logger.debug('Locating provider match for %s' % url)
        return self.match_type(url, 'internal') or self.match_type(url, 'external')

    def match_type(self, url, type):
        """
        Searches the internal provider registry for a matching
        provider for the url based on type

        :param string url: URL to match a provider against
        :param string type: The type of provider to check (either 'internal' or 'external')
        :returns: A provider instance or None if no match is found
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
        Adds an internal provider class to the registry.

        :param provider: A subclass of :class:`InternalProvider`
        :raises: :class:`InvalidProvider` if the supplied param is not a valid subclass
        """
        registry.ensure_populated()

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
