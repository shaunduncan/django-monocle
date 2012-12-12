import logging

from django.db.models import fields

from monocle.consumers import prefetch


logger = logging.getLogger(__name__)


class OEmbedCharField(fields.CharField):
    """
    An extension of CharField with two optional attributes

    contains_html: If the content of this field is marked to contain
                   html content, this will affect the parsing behavior.
                   By default this is false and any matching OEmbed URL
                   will be consumed
    prefetch_sizes: A list of two-tuples that allow the consumer to retrieve
                    multiple sizes on save. The tuples should be in the form
                    (maxwidth, maxheight) which will translate to URL parameters
                    maxwidth and maxheight by the consumer. At least one size
                    is required, but sizes such as (None, 100) or (100, None)
                    are valid and result in fetching with ONLY maxwidth or
                    maxheight.
    """

    description = 'CharField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.pop('contains_html', False)
        self.prefetch_sizes = kwargs.pop('prefetch_sizes', [])
        super(OEmbedCharField, self).__init__(*args, **kwargs)

    def pre_save(self, model, add):
        prefetch(getattr(model, self.attname), html=self.contains_html)
        return super(OEmbedCharField, self).pre_save(model, add)


class OEmbedTextField(fields.TextField):
    """
    An extension of TextField with two optional attributes

    contains_html: If the content of this field is marked to contain
                   html content, this will affect the parsing behavior.
                   By default this is false and any matching OEmbed URL
                   will be consumed
    prefetch_sizes: A list of two-tuples that allow the consumer to retrieve
                    multiple sizes on save. The tuples should be in the form
                    (maxwidth, maxheight) which will translate to URL parameters
                    maxwidth and maxheight by the consumer. At least one size
                    is required, but sizes such as (None, 100) or (100, None)
                    are valid and result in fetching with ONLY maxwidth or
                    maxheight.
    """

    description = 'TextField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.pop('contains_html', True)
        self.prefetch_sizes = kwargs.pop('prefetch_sizes', [])
        super(OEmbedTextField, self).__init__(*args, **kwargs)

    def pre_save(self, model, add):
        prefetch(getattr(model, self.attname), html=self.contains_html)
        return super(OEmbedTextField, self).pre_save(model, add)
