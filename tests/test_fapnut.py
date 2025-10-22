import unittest

from super_dl.sites import fapnut


class FapnutTest(unittest.TestCase):
    def test_extract_iframe_src(self):
        html = '<iframe src="https://player.example.com/embed/abc"></iframe>'
        src = fapnut.extract_iframe_src(html)
        self.assertEqual(src, 'https://player.example.com/embed/abc')

    def test_extract_m3u8_from_src(self):
        html = '<video src="https://cdn.example.com/hls/stream.m3u8"></video>'
        m3u8 = fapnut.extract_m3u8_from_html(html)
        self.assertEqual(m3u8, 'https://cdn.example.com/hls/stream.m3u8')

    def test_extract_m3u8_anywhere(self):
        html = 'Some JS var player = "https://cdn.example.com/stream/playlist.m3u8?token=1";'
        m3u8 = fapnut.extract_m3u8_from_html(html)
        self.assertTrue(m3u8.endswith('.m3u8'))

    def test_filename_from_page_url(self):
        url = 'https://fapnut.net/some-video/'
        name = fapnut._filename_from_page_url(url)
        self.assertEqual(name, 'some-video.mp4')


if __name__ == '__main__':
    unittest.main()
