"""
A collection of Django field extensions that handle OEmbed content prefetching
"""
import logging

from django.db.models import fields

from monocle.consumers import prefetch
from monocle.settings import settings


logger = logging.getLogger(__name__)


class OEmbedCharField(fields.CharField):
    """
    An extension of ``CharField`` with two optional attributes

    * ``contains_html``

      * Bool indicating whether content of this field should be treated
        as html. Default is False.

    * ``prefetch_sizes``

      * List of either integer two-tuples (width, height) or single integers.
        This has the effect of prefetching multiple size variations. These values
        translate to request arguments ``maxwidth`` and ``maxheight`` so tuples
        in the form ``(100, None)`` and ``(None, 100)`` are valid.
    """

    description = 'CharField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.pop('contains_html', False)
        self.prefetch_sizes = kwargs.pop('prefetch_sizes', settings.RESOURCE_DEFAULT_DIMENSIONS)
        super(OEmbedCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model, add):
        prefetch(getattr(model, self.attname), html=self.contains_html, sizes=self.prefetch_sizes)
        return super(OEmbedCharField, self).pre_save(model, add)


class OEmbedTextField(fields.TextField):
    """
    An extension of ``TextField`` with two optional attributes

    * ``contains_html``

      * Bool indicating whether content of this field should be treated
        as html. Default is True.

    * ``prefetch_sizes``

      * List of either integer two-tuples (width, height) or single integers.
        This has the effect of prefetching multiple size variations. These values
        translate to request arguments ``maxwidth`` and ``maxheight`` so tuples
        in the form ``(100, None)`` and ``(None, 100)`` are valid.
    """

    description = 'TextField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.pop('contains_html', True)
        self.prefetch_sizes = kwargs.pop('prefetch_sizes', settings.RESOURCE_DEFAULT_DIMENSIONS)
        super(OEmbedTextField, self).__init__(*args, **kwargs)

    def pre_save(self, model, add):
        prefetch(getattr(model, self.attname), html=self.contains_html, sizes=self.prefetch_sizes)
        return super(OEmbedTextField, self).pre_save(model, add)


class OEmbedURLField(fields.URLField):
    """
    An extension of ``URLField`` with optional attribute. Content is **always**
    parsed as plain text.

    * ``prefetch_sizes``

      * List of either integer two-tuples (width, height) or single integers.
        This has the effect of prefetching multiple size variations. These values
        translate to request arguments ``maxwidth`` and ``maxheight`` so tuples
        in the form ``(100, None)`` and ``(None, 100)`` are valid.
    """

    description = 'URLField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.prefetch_sizes = kwargs.pop('prefetch_sizes', settings.RESOURCE_DEFAULT_DIMENSIONS)
        super(OEmbedURLField, self).__init__(*args, **kwargs)

    def pre_save(self, model, add):
        prefetch(getattr(model, self.attname), html=False, sizes=self.prefetch_sizes)
        return super(OEmbedURLField, self).pre_save(model, add)

try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    _rule1 = ((OEmbedCharField, OEmbedTextField, OEmbedURLField), # Classes the rules apply to
             [],                     # Positional arguments -- not used
             {'prefetch_sizes': ["prefetch_sizes", {'default':settings.RESOURCE_DEFAULT_DIMENSIONS}]
              })
    _rule2 = ((OEmbedCharField, OEmbedTextField), # Classes the rules apply to
             [],                     # Positional arguments -- not used
             {'contains_html': ["contains_html", {}],
              })

    add_introspection_rules([_rule1, _rule2], ['^monocle\.fields\.OEmbed(Char|Text|URL)Field'])
