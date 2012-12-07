from django.db.models import fields


class OEmbedCharField(fields.CharField):

    description = 'CharField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.get('contains_html', False)
        super(OEmbedCharField, self).__init__(*args, **kwargs)

    # TODO: on save?
    def pre_save(self, model, add):
        content = getattr(model, self.attname)

        # TODO: Create a consumer and, well, consume

        return super(OEmbedCharField, self).pre_save(model, add)


class OEmbedTextField(fields.TextField):

    description = 'TextField that transparently fetches OEmbed content on save'

    def __init__(self, *args, **kwargs):
        self.contains_html = kwargs.get('contains_html', False)
        super(OEmbedTextField, self).__init__(*args, **kwargs)

    # TODO: on save?
    def pre_save(self, model, add):
        content = getattr(model, self.attname)

        # TODO: Create a consumer and, well, consume

        return super(OEmbedTextField, self).pre_save(model, add)
