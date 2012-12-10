from django import template
from django.utils.safestring import mark_safe

from monocle.consumers import devour


register = template.Library()


def _args_to_dim(args):
    """Converts args list to width, height if it exists"""
    if len(args) >= 2:
        return _value_to_dim(args[1])
    return None, None


def _value_to_dim(value):
    """Converts an arg string to width,height"""
    if value:
        try:
            parts = value.lower().split('x')

            if len(parts) != 2:
                raise template.TemplateSyntaxError('OEmbed tag argument must be integers [width]x[height]')

            return map(int, parts)
        except ValueError:
            raise template.TemplateSyntaxError('OEmbed tag argument must be integers [width]x[height]')
    return None, None


class OEmbedNode(template.Node):

    def __init__(self, nodelist, width=None, height=None, html=True):
        self.nodelist = nodelist
        self.width = width
        self.height = height
        self.html = html

    def render(self, context):
        return devour(self.nodelist.render(context),
                      html=self.html,
                      maxwidth=self.width,
                      maxheight=self.height)


def oembed_tag(parser, token):
    """
    Replaces OEmbed URLs with rich content. This treats content as HTML.
    Tag may specify maxwidth and maxheight like {% oembed 600x400 %}
    """
    args = token.split_contents()
    width, height = _args_to_dim(args)

    nodelist = parser.parse(('endoembed',))
    parser.delete_first_token()

    return OEmbedNode(nodelist, width, height)


def oembed_text_tag(parser, token):
    """
    Replaces OEmbed URLs with rich content. This treats content as plain text.
    Tag may specify maxwidth and maxheight like {% oembed 600x400 %}
    """
    args = token.split_contents()
    width, height = _args_to_dim(args)

    nodelist = parser.parse(('endoembed_text',))
    parser.delete_first_token()

    return OEmbedNode(nodelist, width, height, html=False)


def oembed_filter(input, size=None):
    """
    Filter that parses content as html for OEmbed URLs
    """
    width, height = _value_to_dim(size)
    return mark_safe(devour(input, html=True, maxwidth=width, maxheight=height))


def oembed_text_filter(input, size=None):
    """
    Filter that parses content as plain text for OEmbed URLs
    """
    width, height = _value_to_dim(size)
    return mark_safe(devour(input, html=False, maxwidth=width, maxheight=height))


register.tag('oembed', oembed_tag)
register.tag('oembed_text', oembed_text_tag)
register.filter('oembed', oembed_filter)
register.filter('oembed_text', oembed_text_filter)
