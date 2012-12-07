from unittest2 import TestCase

from monocle.util import extract_content_url


class UtilsTestCase(TestCase):

    def test_extract_content_url_with_valid_param(self):
        url = 'http://www.youtube.com/oembed?url=http%3A//www.youtube.com/watch?v=fWNaR-rxAic&format=json'
        extracted = extract_content_url(url)
        self.assertEqual(extracted, 'http://www.youtube.com/watch?v=fWNaR-rxAic')

    def test_extract_content_url_with_no_url_param(self):
        url = 'http://www.example.com'
        extracted = extract_content_url(url)
        self.assertIsNone(extracted)
