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

    def __init__(self, maxwidth=None, maxheight=None, skip_internal=False):
        self.maxwidth = maxwidth
        self.maxheight = maxheight
        self.skip_internal = skip_internal
        registry.ensure()

    def enrich(self, content):
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
                resource = provider.get_resource(url, maxwidth=self.maxwidth, maxheight=self.maxheight)
            except:
                logger.exception('Failed to get resource from provider %s' % provider)
            else:
                if resource.is_valid:
                    logger.debug('Embedding %s for url %s' % (resource, url))
                    content = content.replace(url, resource.render())
                else:
                    logger.warning('Provider %s returned a bad resource' % provider)
        return content

    def devour(self, content=None):
        """
        Consumes all OEmbed content URLs in the content. Returns a new
        version of the content with URLs replaced with rich content
        """
        pre_consume.send(sender=self)
        content = self.enrich(content or '')
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

    def devour(self, content=None):
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
            element.replaceWith(BeautifulSoup(self.enrich(str(element))))

        post_consume.send(sender=self)
        return str(soup)


def devour(content, html=False, maxwidth=None, maxheight=None, skip_internal=False):
    if html:
        c = HTMLConsumer(skip_internal=skip_internal)
    else:
        c = Consumer(skip_internal=skip_internal)

    c.maxwidth = maxwidth
    c.maxheight = maxheight

    return c.devour(content)


def prefetch(content, html=False, sizes=None):
    """
    A wrapper for devour() that does specialized work for prefetching
    OEmbed content. Specify a list of sizes to prefetch. By default,
    no explicit size will be passed to the providers. Sizes can be a list
    of two-tuples that are explicit sizes or integers that are converted
    to size combinations
    """
    logger.debug('Prefetching OEmbed content excluding uncached internal providers')
    devour(content, html=html, skip_internal=True)

    if not sizes:
        return

    for size in sizes:
        logger.debug('Prefetching Size %s' % (size,))

        # Explicit size
        if isinstance(size, tuple):
            devour(content, html=html, maxwidth=size[0], maxheight=size[1], skip_internal=True)

        # All size combinations - (size, None), (None, size), (size, size)
        elif isinstance(size, int):
            devour(content, html=html, maxwidth=size, skip_internal=True)
            devour(content, html=html, maxheight=size, skip_internal=True)
            devour(content, html=html, maxwidth=size, maxheight=size, skip_internal=True)
