import logging
import re

from BeautifulSoup import BeautifulSoup

from monocle.providers import registry, InternalProvider
from monocle.settings import settings
from monocle.signals import pre_consume, post_consume


logger = logging.getLogger(__name__)


class Consumer(object):
    # From https://github.com/worldcompany/djangoembed/blob/master/oembed/constants.py#L43
    url_regex = re.compile(r'(https?://[-A-Za-z0-9+&@#/%?=~_()|!:,.;]*[-A-Za-z0-9+&@#/%=~_|])', re.I)

    def __init__(self, skip_internal=False):
        self.skip_internal = skip_internal
        registry.ensure_populated()

    def enrich(self, content, maxwidth=None, maxheight=None):
        """
        Returns an enriched version of content that replaces all URLs that
        have a provider with valid resource data
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
        version of the content with URLs replaced with rich content
        """
        pre_consume.send(sender=self)
        content = self.enrich(content or '', maxwidth=maxwidth, maxheight=maxheight)
        post_consume.send(sender=self)
        return content


class HTMLConsumer(Consumer):
    """
    Behavior is similar here to the base conumser except that we do not
    automatically consume URLs that are hyperlinked
    """
    def _is_hyperlinked(self, node):
        # TODO: This might need work if we want to go all the way up the tree
        return node.parent and node.parent.name == 'a'

    def devour(self, content, maxwidth=None, maxheight=None):
        """
        Devours content URLs by finding all element nodes whose text content
        contains a URL and is not hyperlinked and then enriching those nodes directly
        """
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
    Consume a string interpreting as text or HTML with optional max width/height.
    Optionally indicate if internal providers should be skipped
    """
    if html:
        c = HTMLConsumer(skip_internal=skip_internal)
    else:
        c = Consumer(skip_internal=skip_internal)

    return c.devour(content, maxwidth=maxwidth, maxheight=maxheight)


def prefetch(content, html=False, sizes=None):
    """
    Specify a list of sizes to prefetch. By default, no explicit size will be
    passed to the providers. Sizes can be a list of two-tuples that are explicit
    sizes or integers that are converted to size combinations. All internal
    providers are skipped here if they are not cached
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
