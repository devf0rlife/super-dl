import unittest

from super_dl.sites import thothub


class ThothubTest(unittest.TestCase):
    def test_extract_mp4_url_from_js_line(self):
        html = """
        <script>
        var config = {
            video_url: 'function/0/https://teenager365.to/get_file/3/45b26c39d91fadc25ca70fe1c5912ccf52b9121dfa/15000/15879/15879.mp4/'
        }
        </script>
        """
        url = thothub.extract_mp4_url(html)
        self.assertIsNotNone(url)
        self.assertTrue(url.endswith('.mp4'))

    def test_extract_mp4_url_fallback(self):
        html = '<a href="https://cdn.example.com/videos/12345.mp4">download</a>'
        url = thothub.extract_mp4_url(html)
        self.assertEqual(url, 'https://cdn.example.com/videos/12345.mp4')

    def test_filename_from_url_logic(self):
        url = 'https://teenager365.to/get_file/3/45b26c39d91fadc25ca70fe1c5912ccf52b9121dfa/15000/15879/15879.mp4/?rnd=4361069126400'
        name = thothub._filename_from_url(url)
        self.assertEqual(name, '15879.mp4')


if __name__ == '__main__':
    unittest.main()
