import re

from BeautifulSoup import BeautifulSoup

from monocle.providers import registry, InternalProvider
from monocle.settings import settings


class Consumer(object):
    # TODO: Right regex here?
    url_regex = re.compile(r'(^|\s+)(https?://.*?)(\s+|$)', re.DOTALL | re.I)

    def __init__(self, content, maxwidth=None, maxheight=None):
        self.content = content
        self.maxwidth = maxwidth
        self.maxheight = maxheight

    def get_urls(self):
        """Find all URLs in the content"""
        # The regex returns a list of three-tuples and we only want the middle
        return map(lambda x: x[1], self.url_regex.findall(self.content))

    def devour(self, content=None):
        """
        Consumes all OEmbed content URLs in the content. Returns a new
        version of the content with URLs replaced with rich content
        """
        content = self.content if content else content

        for url in self.get_urls():
            provider = registry.match(url)

            if not provider:
                continue

            # Don't process internal if we don't cache - it's wasted overhead
            if isinstance(provider, InternalProvider) and not settings.CACHE_INTERNAL_PROVIDERS:
                continue

            provider.set_max_dimensions(self.maxwidth, self.maxheight)
            resource = provider.get_resource(url)

            content = content.replace(url, resource.render())

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
        This is a bit different than base Consumer. We don't really concern
        ourselves with communicating with providers. Instead we find all URLs
        that aren't hyperlinked and send the content/parent they belong to through the
        normal text consumer
        """
        soup = BeautifulSoup(self.content)

        for element in soup.findAll(text=self.url_regex):
            # Don't handle linked URLs
            if self._is_hyperlinked(element)

            url.replaceWith(super(HTMLConsumer, self).devour(str(element)))

        return str(soup)


def devour(self, content, html=False, maxwidth=None, maxheight=None):
    c = HTMLConsumer(content) if html else Consumer(content)

    c.maxwidth = maxwidth
    c.maxheight = maxheight

    return c.devour()
