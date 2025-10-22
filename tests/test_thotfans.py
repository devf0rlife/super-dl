import unittest

from super_dl.sites import thotfans


class ThotfansTest(unittest.TestCase):
    def test_extract_mp4_from_source_tag(self):
        html = '<video><source type="video/mp4" src="https://cdn.thotfans.com/igw/2412/jeed.mp4?_=1" /></video>'
        url = thotfans.extract_mp4_url(html)
        self.assertIsNotNone(url)
        self.assertTrue(url.endswith('.mp4'))

    def test_extract_mp4_from_anchor(self):
        html = '<a href="https://cdn.thotfans.com/igw/2412/jeed.mp4">https://cdn.thotfans.com/igw/2412/jeed.mp4</a>'
        url = thotfans.extract_mp4_url(html)
        self.assertEqual(url, 'https://cdn.thotfans.com/igw/2412/jeed.mp4')

    def test_filename_from_url(self):
        url = 'https://cdn.thotfans.com/igw/2412/jeed.mp4?_=1'
        name = thotfans._filename_from_url(url)
        self.assertEqual(name, 'jeed.mp4')


if __name__ == '__main__':
    unittest.main()
