import unittest

from bullethole.gore import Gore
from bullethole.web import background_png, build_page

W, H = 320, 240


class WebTests(unittest.TestCase):
    def setUp(self):
        self.gore = Gore(W, H, hole_radius=50, seed=1)

    def test_page_has_one_element_per_drip(self):
        page = build_page(self.gore).decode()
        self.assertEqual(page.count('class="drip"'), len(self.gore.drips))

    def test_page_outlines_the_wound_and_streams_camera(self):
        page = build_page(self.gore).decode()
        self.assertIn("clip-path: polygon(", page)
        self.assertIn('src="/camera.mjpg"', page)
        self.assertNotIn("__", page.split("<style>")[1].split("</style>")[0])

    def test_outline_has_requested_points_around_centre(self):
        points = self.gore.outline(count=36)
        self.assertEqual(len(points), 36)
        for x, y in points:
            self.assertLess(abs(x - self.gore.cx), 50 * 1.6)
            self.assertLess(abs(y - self.gore.cy), 50 * 1.6)

    def test_background_is_png(self):
        self.assertEqual(background_png(self.gore)[:8], b"\x89PNG\r\n\x1a\n")


if __name__ == "__main__":
    unittest.main()
