import logging
import re

from BeautifulSoup import BeautifulSoup

from monocle.providers import registry, InternalProvider
from monocle.settings import settings
from monocle.signals import pre_consume, post_consume


logger = logging.getLogger(__name__)


class Consumer(object):
    """
    Consumers are objects that essentially scan some content string for URL patterns and
    interact with the provider framework to locate a corresponding resource. If a valid
    resource is returned from the provider framework, all occurrences of the URL matched
    will be replaced with the resource's response.
    """

    # From https://github.com/worldcompany/djangoembed/blob/master/oembed/constants.py#L43
    url_regex = re.compile(r'(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_|])', re.I)

    def __init__(self, skip_internal=False):
        self.skip_internal = skip_internal
        registry.ensure_populated()

    def enrich(self, content, maxwidth=None, maxheight=None):
        """
        Returns an enriched version of content that replaces all URLs that
        have a provider with valid resource data. By default, all providers
        are considered for possible replacement. However, if the consumer's
        ``skip_internal`` attribute is True and internal provider responses
        are not configured to be cached, no matched URL that is an internal
        provider will be rendered. This is useful if any prefetching is to
        occur where rendering internal providers may be wasted effort.

        :param string content: Content to enrich
        :param integer maxwidth: Maximum width of resource
        :param integer maxheight: Maximum height of resource
        :returns: A version of specific content with matched URLs replaced with
                  rendered resources
        """
        for url in self.url_regex.findall(content):
            provider = registry.match(url)

            if not provider:
                logger.debug('No provider match for %s' % url)
                continue

            # Bypass internal providers if they aren't cached
            if (self.skip_internal and isinstance(provider, InternalProvider) and
                    not settings.CACHE_INTERNAL_PROVIDERS):
                logger.debug('Skipping uncached internal provider')
                continue

            # This is generally a safeguard against bad provider implementations
            try:
                resource = provider.get_resource(url, maxwidth=maxwidth, maxheight=maxheight)
            except:
                logger.exception('Failed to get resource from provider %s' % provider)
            else:
                if not resource.is_valid:
                    logger.warning('Provider %s returned a bad resource' % provider)

                logger.debug('Embedding %s for url %s' % (resource, url))
                content = content.replace(url, resource.render())
        return content

    def devour(self, content, maxwidth=None, maxheight=None):
        """
        Consumes all OEmbed content URLs in the content. Returns a new
        version of the content with URLs replaced with rich content. This
        sends both ``pre_consume`` and ``post_consume`` signals before and
        after enriching the specified content. Any subclasses should take
        note to honor this behavior.

        :param string content: Content to enrich
        :param integer maxwidth: Maximum width of resource
        :param integer maxheight: Maximum height of resource
        :returns: A version of specific content with matched URLs replaced with
                  rendered resources
        """
        pre_consume.send(sender=self)
        content = self.enrich(content or '', maxwidth=maxwidth, maxheight=maxheight)
        post_consume.send(sender=self)
        return content


class HTMLConsumer(Consumer):
    """
    A type of consumer that treats content blocks as html. This directly affects
    the behavior of content enrichment in the sense that any matched URLs that
    are actually the text portion of a hyperlink (i.e. <a>http://foo.com</a>)
    will be respected and not replaced with rich content

    .. note:
       Parsing html content is currently handled via BeautifulSoup
    """
    def _is_hyperlinked(self, node):
        """
        Checks if an html node is hyperlinked (if it has a parent, and the parent
        is the 'a' tag)

        :param node: A BeautifulSoup element
        :returns: Bool
        """
        # TODO: This might need work if we want to go all the way up the tree
        return node.parent and node.parent.name == 'a'

    def devour(self, content, maxwidth=None, maxheight=None):
        pre_consume.send(sender=self)
        soup = BeautifulSoup(content or '')

        for element in soup.findAll(text=self.url_regex):
            # Don't handle linked URLs
            if self._is_hyperlinked(element):
                logger.debug('Skipping hyperlinked content: %s' % element)
                continue
            repl = self.enrich(str(element), maxwidth=maxwidth, maxheight=maxheight)
            element.replaceWith(BeautifulSoup(repl))

        post_consume.send(sender=self)
        return str(soup)


def devour(content, html=False, maxwidth=None, maxheight=None, skip_internal=False):
    """
    Consume a string interpreting as text or html with optional max width/height.
    Optionally indicate if internal providers should be skipped

    :param string content: Content to enrich
    :param boolean html: Whether to treat content as plain text or html
    :param integer maxwidth: Maximum width of resource
    :param integer maxheight: Maximum height of resource
    :param integer skip_internal: Whether internal providers should be processed
    :returns: A version of specific content with matched URLs replaced with
              rendered resources
    """
    if html:
        c = HTMLConsumer(skip_internal=skip_internal)
    else:
        c = Consumer(skip_internal=skip_internal)

    return c.devour(content, maxwidth=maxwidth, maxheight=maxheight)


def prefetch(content, html=False, sizes=None):
    """
    Performs a series of :func:`devour` calls for each entry in the ``sizes`` parameter.
    By default, no explicit size will be passed to the providers. Sizes can be a
    list of integer two-tuples or integers that are converted to size combinations
    (i.e. 100 becomes (100, None), (None, 100) and (100, 100)). All internal providers
    are skipped here if they are not cached

    :param string content: Content to enrich
    :param boolean html: Whether to treat content as plain text or html
    :param list sizes: Integer two-tuples or single integers
    :returns: A version of specific content with matched URLs replaced with
              rendered resources
    """
    logger.debug('Prefetching OEmbed content excluding uncached internal providers')

    # Get a consumer
    c = HTMLConsumer(skip_internal=True) if html else Consumer(skip_internal=True)
    c.devour(content)

    # Process size combinations
    for size in (sizes or []):
        # Explicit size
        if isinstance(size, tuple):
            c.devour(content, maxwidth=size[0], maxheight=size[1])

        # All size combinations - (size, None), (None, size), (size, size)
        elif isinstance(size, int):
            c.devour(content, maxwidth=size)
            c.devour(content, maxheight=size)
            c.devour(content, maxwidth=size, maxheight=size)
