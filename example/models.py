import re

from django.db import models

from monocle.fields import OEmbedTextField, OEmbedCharField
from monocle.providers import InternalProvider, registry


_PREFETCH = range(200, 1100, 100)


class Blog(models.Model):
    name = models.CharField(max_length=255)
    summary = OEmbedCharField(max_length=255, prefetch_sizes=_PREFETCH)

    def __unicode__(self):
        return self.name


class Entry(models.Model):
    title = models.CharField(max_length=255)
    content = OEmbedTextField(prefetch_sizes=_PREFETCH)
    blog = models.ForeignKey('Blog')

    class Meta:
        verbose_name_plural = 'Entries'

    def __unicode__(self):
        return self.title


class EntryProvider(InternalProvider):

    # Provider things
    html_template = 'entry_oembed.html'
    resource_type = 'rich'
    url_schemes = ['http://localhost/entry/*']

    DIMENSIONS = [(x, x) for x in range(200, 600, 100)]
    DEFAULT_WIDTH = 400
    DEFAULT_HEIGHT = 400

    def __init__(self, entry):
        self.entry = entry

    @classmethod
    def get_object(cls, url):
        try:
            id = re.findall(r'entry/([0-9]+)', url, re.I)[0]
            return EntryProvider(entry=Entry.objects.get(id=id))
        except:
            return None

    @property
    def title(self):
        return self.entry.title

    @property
    def html(self):
        return self.render_html({
            'entry': self.entry,
            'width': self.width,
            'height': self.height
        })


registry.register(EntryProvider)
