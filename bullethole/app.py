"""Start the prop: camera in, gore page out. Chromium kiosk shows it on the DSI display."""

import argparse

from .camera import PiCamera, TestPattern
from .gore import Gore
from .web import serve

WIDTH, HEIGHT = 800, 480


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bullet-hole shirt prop.")
    parser.add_argument("--fake-camera", action="store_true",
                        help="use a test pattern instead of the Pi camera")
    parser.add_argument("--mirror", action="store_true",
                        help="flip the camera image left-right")
    parser.add_argument("--no-swap-rgb", action="store_true",
                        help="don't swap camera channels (use if colours look wrong)")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--fps", type=int, default=15, help="camera stream frame rate")
    parser.add_argument("--bpm", type=int, default=72, help="heartbeat speed of the rim")
    parser.add_argument("--hole-radius", type=int, default=180)
    parser.add_argument("--seed", type=int, default=None,
                        help="fixed seed gives the same wound shape every run")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)

    if args.fake_camera:
        camera = TestPattern(WIDTH, HEIGHT)
    else:
        camera = PiCamera(WIDTH, HEIGHT, swap_rgb=not args.no_swap_rgb)
    gore = Gore(WIDTH, HEIGHT, hole_radius=args.hole_radius, seed=args.seed, bpm=args.bpm)

    try:
        serve(gore, camera, port=args.port, mirror=args.mirror, fps=args.fps)
    finally:
        camera.close()
