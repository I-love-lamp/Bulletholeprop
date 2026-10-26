"""Full-screen loop: camera in, gore out, on the 800x480 DSI display."""

import argparse
import time

import pygame

from .camera import PiCamera, TestPattern
from .gore import Gore

WIDTH, HEIGHT = 800, 480


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Bullet-hole shirt prop.")
    parser.add_argument("--fake-camera", action="store_true",
                        help="use a test pattern instead of the Pi camera")
    parser.add_argument("--mirror", action="store_true",
                        help="flip the camera image left-right")
    parser.add_argument("--no-swap-rgb", action="store_true",
                        help="don't swap camera channels (use if colours look wrong)")
    parser.add_argument("--windowed", action="store_true",
                        help="run in a window instead of full screen")
    parser.add_argument("--fps", type=int, default=20)
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

    pygame.init()
    flags = 0 if args.windowed else pygame.FULLSCREEN
    screen = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.mouse.set_visible(False)
    clock = pygame.time.Clock()
    start = time.monotonic()

    try:
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (
                        event.type == pygame.KEYDOWN and event.key in (pygame.K_ESCAPE, pygame.K_q)):
                    running = False

            frame = camera.read()
            if args.mirror:
                frame = frame[:, ::-1]
            img = gore.render(frame, time.monotonic() - start)
            surface = pygame.image.frombuffer(img.tobytes(), (WIDTH, HEIGHT), "RGB")
            screen.blit(surface, (0, 0))
            pygame.display.flip()
            clock.tick(args.fps)
    finally:
        camera.close()
        pygame.quit()
