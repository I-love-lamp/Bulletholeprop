"""Procedural gore for the bullet-hole prop.

The front screen shows the rear camera through a ragged hole. Everything
around the hole is flesh: a pulsing torn rim, dripping blood and splatter.

The maths is numpy and PIL only, so the look can be checked without a
display:

    python -m bullethole.gore --out preview.png
"""

import math
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw

FLESH_DARK = np.array([55, 0, 4], np.float32)
FLESH_LIGHT = np.array([150, 14, 18], np.float32)
RIM_COLOR = np.array([120, 8, 10], np.float32)
DRIP_COLOR = np.array([95, 0, 6], np.float32)
SPLATTER_COLOR = (150, 16, 18)


@dataclass
class Drip:
    x: float
    y: float
    width: float
    max_len: float
    speed: float
    period: float
    phase: float


class Gore:
    def __init__(self, width=800, height=480, hole_radius=150, seed=None,
                 drip_count=24, bpm=72):
        self.width = width
        self.height = height
        self.bpm = bpm
        self.cx = width / 2
        self.cy = height / 2
        self.hole_radius = hole_radius

        rng = np.random.default_rng(seed)
        self._build_hole(rng)
        self.background = self._build_background(rng)
        self.rim_texture = RIM_COLOR * (0.7 + 0.6 * _fbm(rng, height, width, 8, 4))[..., None]
        self.drips = self._build_drips(drip_count, rng)

    def _build_hole(self, rng):
        ys, xs = np.mgrid[0:self.height, 0:self.width].astype(np.float32)
        dx = xs - self.cx
        dy = ys - self.cy
        self.dist = np.hypot(dx, dy)
        theta = np.arctan2(dy, dx)

        # Random harmonics make the edge ragged, like a shotgun blast's
        # uneven tearing rather than a clean round hole.
        self.lumps = [
            (k, rng.uniform(0, 2 * math.pi), rng.uniform(0.05, 0.12) / math.sqrt(k))
            for k in range(3, 18)
        ]
        # Sharp tears where the tissue was blown outwards.
        self.tears = [
            (rng.uniform(-math.pi, math.pi), rng.uniform(0.05, 0.12), rng.uniform(0.15, 0.3))
            for _ in range(6)
        ]
        self.edge = self._radius_at(theta).astype(np.float32)

        feather = 1.5
        self.hole_alpha = np.clip((self.edge - self.dist) / feather + 0.5, 0, 1).astype(np.float32)
        # Walls of the hole fall into shadow so the camera reads as a tunnel.
        self.wall_shade = np.clip((self.edge - self.dist) / 14.0, 0, 1).astype(np.float32)
        self.rim_alpha = np.clip(1 - (self.dist - self.edge) / 40.0, 0, 1).astype(np.float32)
        # Bruising spreads out from the wound.
        self.bruise = np.clip(1 - (self.dist - self.edge) / 90.0, 0, 1).astype(np.float32)

    def _radius_at(self, theta):
        radius = np.ones_like(theta)
        for k, phase, amp in self.lumps:
            radius += amp * np.sin(k * theta + phase)
        for angle, width, amp in self.tears:
            diff = np.angle(np.exp(1j * (theta - angle)))
            radius += amp * np.exp(-(diff ** 2) / (2 * width ** 2))
        return self.hole_radius * radius

    def _build_background(self, rng):
        flesh = _fbm(rng, self.height, self.width, 3, 5)[..., None]
        flesh = FLESH_DARK + (FLESH_LIGHT - FLESH_DARK) * flesh

        # Thin dark veins from ridged noise.
        ridge = 1 - np.abs(2 * _fbm(rng, self.height, self.width, 6, 3) - 1)
        vein = np.clip((ridge - 0.85) * 6, 0, 1)[..., None]
        flesh *= 1 - 0.55 * vein

        img = Image.fromarray(flesh.clip(0, 255).astype(np.uint8))
        draw = ImageDraw.Draw(img)
        for _ in range(70):
            x = rng.uniform(0, self.width)
            y = rng.uniform(0, self.height)
            r = rng.uniform(2, 16)
            draw.ellipse([x - r, y - r, x + r, y + r], fill=SPLATTER_COLOR)
            for _ in range(rng.integers(0, 4)):
                # Satellite droplets thrown off each splatter.
                angle = rng.uniform(0, 2 * math.pi)
                far = r * rng.uniform(2, 4)
                x2, y2 = x + far * math.cos(angle), y + far * math.sin(angle)
                s = rng.uniform(1, 3)
                draw.ellipse([x2 - s, y2 - s, x2 + s, y2 + s], fill=SPLATTER_COLOR)

        flesh = np.asarray(img, np.float32)
        vignette = 1 - 0.35 * np.clip(self.dist / math.hypot(self.cx, self.cy), 0, 1) ** 2
        return flesh * vignette[..., None]

    def _build_drips(self, count, rng):
        drips = []
        for _ in range(count):
            # Blood only runs from the lower part of the wound.
            theta = rng.uniform(0.15, 0.85) * math.pi
            r = float(self._radius_at(np.float32(theta)))
            max_len = rng.uniform(40, 160)
            speed = rng.uniform(22, 45)
            drips.append(Drip(
                x=self.cx + r * math.cos(theta),
                y=self.cy + r * math.sin(theta),
                width=rng.uniform(3, 7),
                max_len=max_len,
                speed=speed,
                period=max_len / speed + rng.uniform(2, 6),
                phase=rng.uniform(0, 60),
            ))
        return drips

    def _paint_drips(self, flesh, t):
        for d in self.drips:
            age = (t + d.phase) % d.period
            length = min(age * d.speed, d.max_len)
            # Each drip fades out at the end of its cycle, then grows again.
            fade = min(1.0, d.period - age)
            if length < 1 or fade <= 0:
                continue
            x0 = max(0, int(d.x - d.width / 2))
            x1 = min(self.width, int(d.x + d.width / 2) + 1)
            y0 = max(0, int(d.y))
            y1 = min(self.height, int(d.y + length))
            if x1 <= x0 or y1 <= y0:
                continue
            region = flesh[y0:y1, x0:x1]
            region[:] = region * (1 - fade) + DRIP_COLOR * fade

    def render(self, camera_frame, t=0.0):
        """Return one RGB uint8 frame: camera inside the hole, gore outside.

        camera_frame must be (height, width, 3). The camera is not pulsed,
        so what shows through the wound is exactly what the camera sees.
        """
        if camera_frame.shape[:2] != (self.height, self.width):
            raise ValueError(
                f"camera frame is {camera_frame.shape[1]}x{camera_frame.shape[0]}, "
                f"expected {self.width}x{self.height}"
            )

        pulse = 1.0 + 0.06 * math.sin(2 * math.pi * self.bpm / 60 * t)
        ra = self.rim_alpha[..., None]
        flesh = self.background * pulse * (1 - 0.4 * self.bruise[..., None])
        flesh = flesh * (1 - 0.85 * ra) + self.rim_texture * pulse * 0.85 * ra
        self._paint_drips(flesh, t)

        cam = camera_frame.astype(np.float32)
        cam *= (0.5 + 0.5 * self.wall_shade)[..., None]
        ha = self.hole_alpha[..., None]
        out = cam * ha + flesh * (1 - ha)
        return np.clip(out, 0, 255).astype(np.uint8)


def _fbm(rng, height, width, base, octaves):
    """Smooth 0..1 noise: random grids upscaled with bicubic and summed."""
    total = np.zeros((height, width), np.float32)
    weight = 0.0
    amp = 1.0
    for octave in range(octaves):
        rows = base * 2 ** octave
        cols = max(2, round(rows * width / height))
        grid = rng.random((rows, cols), dtype=np.float32)
        layer = Image.fromarray((grid * 255).astype(np.uint8)).resize(
            (width, height), Image.Resampling.BICUBIC)
        total += amp * np.asarray(layer, np.float32) / 255
        weight += amp
        amp *= 0.5
    return total / weight


if __name__ == "__main__":
    import argparse

    from .camera import test_pattern

    parser = argparse.ArgumentParser(description="Render one frame to a PNG.")
    parser.add_argument("--out", default="preview.png")
    parser.add_argument("--seed", type=int, default=None)
    parser.add_argument("--t", type=float, default=0.0, help="time in seconds")
    args = parser.parse_args()

    gore = Gore(seed=args.seed)
    frame = test_pattern(gore.width, gore.height, args.t)
    Image.fromarray(gore.render(frame, args.t)).save(args.out)
    print(f"wrote {args.out}")
