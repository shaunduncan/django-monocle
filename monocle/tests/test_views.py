from mock import Mock, patch
from unittest2 import TestCase

from monocle.views import oembed


class ViewsTestCase(TestCase):

    def setUp(self):
        self.request = Mock()

    def _oembed_status(self):
        return oembed(self.request).status_code

    def test_oembed_bad_request(self):
        for test in [{}, {'url': ''}]:
            self.request.GET = test
            self.assertEqual(400, self._oembed_status())

    def test_oembed_not_implemented_format(self):
        self.request.GET = {'url': 'foo', 'format': 'xml'}
        self.assertEqual(501, self._oembed_status())

    @patch('monocle.views.registry')
    def test_oembed_not_found_provider(self, registry):
        self.request.GET = {'url': 'foo'}

        registry.match.return_value = None
        self.assertEqual(404, self._oembed_status())

        fake_provider = Mock()
        fake_provider.expose = False
        registry.match.return_value = fake_provider
        self.assertEqual(404, self._oembed_status())

    @patch('monocle.views.registry')
    def test_oembed_handles_max_dim_params_valid(self, registry):
        provider = Mock()
        provider.expose = True
        registry.match.return_value = provider

        self.request.GET = {'url': 'foo', 'maxwidth': '100', 'maxheight': '200'}
        oembed(self.request)
        provider.get_resource.assert_called_with('foo', maxwidth=100, maxheight=200)

    @patch('monocle.views.registry')
    def test_oembed_handles_max_dim_params_filter_none(self, registry):
        provider = Mock()
        provider.expose = True
        registry.match.return_value = provider

        # Filter None
        self.request.GET = {'url': 'foo', 'maxwidth': '100'}
        oembed(self.request)
        provider.get_resource.assert_called_with('foo', maxwidth=100)

    @patch('monocle.views.registry')
    def test_oembed_handles_max_dim_params_filter_invalid(self, registry):
        provider = Mock()
        provider.expose = True
        registry.match.return_value = provider

        # Filter Invalid
        self.request.GET = {'url': 'foo', 'maxwidth': '100', 'maxheight': 'foo'}
        oembed(self.request)
        provider.get_resource.assert_called_with('foo', maxwidth=100)

    @patch('monocle.views.registry')
    def test_oembed_handles_jsonp_callbacks(self, registry):
        resource = Mock()
        resource.json = '{"foo": "bar"}'
        provider = Mock()
        provider.expose = True
        provider.get_resource.return_value = resource
        registry.match.return_value = provider

        self.request.GET = {'url': 'foo', 'callback': 'acallback'}
        response = oembed(self.request)
        self.assertEqual('acallback({"foo": "bar"})', response.content)
