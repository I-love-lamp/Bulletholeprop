import unittest

import numpy as np

from bullethole.camera import test_pattern
from bullethole.gore import Gore

W, H = 320, 240


class GoreTests(unittest.TestCase):
    def setUp(self):
        self.gore = Gore(W, H, hole_radius=50, seed=1)
        self.cam = test_pattern(W, H, 0.0)

    def test_output_is_rgb_uint8_at_frame_size(self):
        out = self.gore.render(self.cam, 0.0)
        self.assertEqual(out.shape, (H, W, 3))
        self.assertEqual(out.dtype, np.uint8)

    def test_hole_centre_shows_camera_exactly(self):
        out = self.gore.render(self.cam, 0.3)
        y, x = int(self.gore.cy), int(self.gore.cx)
        np.testing.assert_array_equal(out[y, x], self.cam[y, x])

    def test_outside_hole_is_red_flesh(self):
        out = self.gore.render(self.cam, 0.0)
        r, g, b = out[2, 2]
        self.assertGreater(r, g)
        self.assertGreater(r, b)

    def test_drips_render_across_time(self):
        for t in (0.0, 1.5, 7.0, 30.0, 300.0):
            out = self.gore.render(self.cam, t)
            self.assertEqual(out.shape, (H, W, 3))

    def test_same_seed_gives_same_wound(self):
        a = Gore(W, H, hole_radius=50, seed=3)
        b = Gore(W, H, hole_radius=50, seed=3)
        np.testing.assert_array_equal(a.edge, b.edge)

    def test_wrong_camera_size_is_rejected(self):
        with self.assertRaises(ValueError):
            self.gore.render(np.zeros((10, 10, 3), np.uint8), 0.0)


if __name__ == "__main__":
    unittest.main()
