"""Camera sources: the Pi camera on the back, or a test pattern for desktop runs."""

import time

import numpy as np


def test_pattern(width, height, t=0.0):
    """Moving stripes and a colour gradient, so the hole is obvious in previews."""
    ys, xs = np.mgrid[0:height, 0:width]
    stripes = ((xs + int(t * 60)) // 40) % 2
    r = (xs * 255 // width).astype(np.uint8)
    g = (ys * 255 // height).astype(np.uint8)
    b = np.where(stripes, 230, 40).astype(np.uint8)
    return np.dstack([r, g, b])


class PiCamera:
    def __init__(self, width, height, swap_rgb=True):
        # Imported here so the rest of the code runs on machines without picamera2.
        from picamera2 import Picamera2

        self.swap_rgb = swap_rgb
        self.cam = Picamera2()
        config = self.cam.create_video_configuration(
            main={"size": (width, height), "format": "RGB888"})
        self.cam.configure(config)
        self.cam.start()

    def read(self):
        frame = self.cam.capture_array("main")
        # picamera2's RGB888 is laid out B,G,R in memory. Swap so colours are right.
        return frame[..., ::-1] if self.swap_rgb else frame

    def close(self):
        self.cam.stop()


class TestPattern:
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.start = time.monotonic()

    def read(self):
        return test_pattern(self.width, self.height, time.monotonic() - self.start)

    def close(self):
        pass
