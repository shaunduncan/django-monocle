from mock import patch
from unittest2 import TestCase

from django.template import Context, Template, TemplateSyntaxError


class TagTestCase(TestCase):

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_tag(self, devour):
        tpl = Template('{% load oembed_tags %}{% oembed %}http://foo.com{% endoembed %}')
        devour.return_value = 'FOO'
        result = tpl.render(Context())

        self.assertEqual('FOO', result)
        devour.assert_called_with('http://foo.com', html=True, maxwidth=None, maxheight=None)

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_tag_with_size(self, devour):
        tpl = Template('{% load oembed_tags %}{% oembed 100x900 %}http://foo.com{% endoembed %}')
        devour.return_value = 'FOO'
        result = tpl.render(Context())

        self.assertEqual('FOO', result)
        devour.assert_called_with('http://foo.com', html=True, maxwidth=100, maxheight=900)

    def test_oembed_tag_with_size_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template('{% load oembed_tags %}{% oembed fooxbar %}http://foo.com{% endoembed %}')

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_text_tag(self, devour):
        tpl = Template('{% load oembed_tags %}{% oembed_text %}http://foo.com{% endoembed_text %}')
        devour.return_value = 'FOO'
        result = tpl.render(Context())

        self.assertEqual('FOO', result)
        devour.assert_called_with('http://foo.com', html=False, maxwidth=None, maxheight=None)

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_text_tag_with_size(self, devour):
        tpl = Template('{% load oembed_tags %}{% oembed_text 100x900 %}http://foo.com{% endoembed_text %}')
        devour.return_value = 'FOO'
        result = tpl.render(Context())

        self.assertEqual('FOO', result)
        devour.assert_called_with('http://foo.com', html=False, maxwidth=100, maxheight=900)

    def test_oembed_text_tag_with_size_raises(self):
        with self.assertRaises(TemplateSyntaxError):
            Template('{% load oembed_tags %}{% oembed_text fooxbar %}http://foo.com{% endoembed_text %}')

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_filter(self, devour):
        tpl = Template('{% load oembed_tags %}{{ content|oembed }}')
        devour.return_value = 'FOO'
        result = tpl.render(Context({'content': 'http://foo.com'}))

        self.assertEqual('FOO', result)
        devour.assert_called_width('http://foo.com', html=True, maxwidth=None, maxheight=None)

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_filter_with_size(self, devour):
        tpl = Template('{% load oembed_tags %}{{ content|oembed:"100x200" }}')
        devour.return_value = 'FOO'
        result = tpl.render(Context({'content': 'http://foo.com'}))

        self.assertEqual('FOO', result)
        devour.assert_called_width('http://foo.com', html=True, maxwidth=100, maxheight=200)

    def test_oembed_filter_with_size_raises(self):
        tpl = Template('{% load oembed_tags %}{{ content|oembed:"foo" }}')
        with self.assertRaises(TemplateSyntaxError):
            tpl.render(Context({'content': 'http://foo.com'}))

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_text_filter(self, devour):
        tpl = Template('{% load oembed_tags %}{{ content|oembed_text }}')
        devour.return_value = 'FOO'
        result = tpl.render(Context({'content': 'http://foo.com'}))

        self.assertEqual('FOO', result)
        devour.assert_called_width('http://foo.com', html=True, maxwidth=None, maxheight=None)

    @patch('monocle.templatetags.oembed_tags.devour')
    def test_oembed_text_filter_with_size(self, devour):
        tpl = Template('{% load oembed_tags %}{{ content|oembed_text:"100x200" }}')
        devour.return_value = 'FOO'
        result = tpl.render(Context({'content': 'http://foo.com'}))

        self.assertEqual('FOO', result)
        devour.assert_called_width('http://foo.com', html=True, maxwidth=100, maxheight=200)

    def test_oembed_text_filter_with_size_raises(self):
        tpl = Template('{% load oembed_tags %}{{ content|oembed_text:"foo" }}')
        with self.assertRaises(TemplateSyntaxError):
            tpl.render(Context({'content': 'http://foo.com'}))
