import re

from monocle.providers import registry, InternalProvider
from monocle.settings import settings


class Consumer(object):
    url_regex = re.compile(r'(^|\s+)(https?://.*?)(\s+|$)', re.DOTALL | re.I)

    def __init__(self, content):
        self.content = content

    def get_urls(self):
        """Find all URLs in the content"""
        # The regex returns a list of three-tuples and we only want the middle
        return map(lambda x: x[1], self.url_regex.findall(self.content))

    def consume(self, sizes=None):
        for url in self.get_urls():
            provider = registry.match(url)

            if not provider:
                continue

            # Don't process internal if we don't cache - it's wasted overhead
            if isinstance(provider, InternalProvider) and not settings.CACHE_INTERNAL_PROVIDERS:
                continue

            if not sizes:
                provider.get_resource(url)
                continue
            else:
                for size in sizes:
                    provider.set_max_dimensions(size[0], size[1])
                    provider.get_resource(url)


class HTMLConsumer(Consumer):
    """
    Behavior is similar here to the base conumser except that we do not
    automatically consume URLs that are hyperlinked
    """
    pass


def devour(self, content, html=False, sizes=None):
    c = HTMLConsumer(content) if html else Consumer(content)
    c.consume(sizes=sizes)
