"""Serve the prop as a web page.

CSS animates the drips and the heartbeat rim. The rear camera is streamed as
MJPEG into the wound. Chromium in kiosk mode shows the page on the DSI screen.
"""

import io
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np
from PIL import Image

BOUNDARY = "frame"

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=800">
<title>Bullet hole</title>
<style>
  html, body { margin: 0; background: #000; overflow: hidden; cursor: none; }
  #stage { position: relative; width: 800px; height: 480px; overflow: hidden;
           background: #2a0004 url(/background.png) 0 0 / 800px 480px no-repeat; }
  #stage > * { position: absolute; left: 0; top: 0; }
  #bruise { width: 800px; height: 480px;
            background: radial-gradient(circle at 400px 240px,
                        transparent 170px, rgba(30, 0, 0, .5) 290px); }
  .rim { width: 800px; height: 480px; transform-origin: 400px 240px;
         animation: beat __BEAT__s ease-in-out infinite; }
  #cam { width: 800px; height: 480px; clip-path: polygon(__POLY__); }
  #cam img { display: block; width: 800px; height: 480px; }
  .drip { height: 0; border-radius: 0 0 999px 999px; transform-origin: top;
          background: linear-gradient(90deg, #3d0104, #9a0b10 40%, #4f0205);
          animation: drip var(--dur) ease-in-out infinite;
          animation-delay: var(--delay); }
  @keyframes beat {
    0%, 100% { opacity: .85; transform: scale(1); }
    15%      { opacity: 1;   transform: scale(1.015); }
    30%      { opacity: .9;  transform: scale(1); }
  }
  @keyframes drip {
    0%   { height: 0;            opacity: 1; }
    55%  { height: var(--len);   opacity: 1; }
    80%  { height: var(--len);   opacity: 1; }
    100% { height: var(--len);   opacity: 0; }
  }
</style>
</head>
<body>
<div id="stage">
  <div id="bruise"></div>
  <svg class="rim" width="800" height="480" viewBox="0 0 800 480">
    <path d="__PATH__" fill="none" stroke="#780810" stroke-width="40" style="filter: blur(10px)"/>
  </svg>
__DRIPS__
  <div id="cam"><img src="/camera.mjpg" alt=""></div>
  <svg width="800" height="480" viewBox="0 0 800 480">
    <path d="__PATH__" fill="none" stroke="rgba(0, 0, 0, .55)" stroke-width="14" style="filter: blur(5px)"/>
  </svg>
</div>
</body>
</html>
"""


def build_page(gore):
    points = gore.outline()
    poly = ", ".join(f"{x:.1f}px {y:.1f}px" for x, y in points)
    path = "M " + " L ".join(f"{x:.1f} {y:.1f}" for x, y in points) + " Z"
    drips = "\n".join(
        f'  <div class="drip" style="left: {d.x - d.width / 2:.1f}px; top: {d.y:.1f}px; '
        f'width: {d.width:.1f}px; --len: {d.max_len:.1f}px; --dur: {d.period * 1.5:.1f}s; '
        f'--delay: {-d.phase * 1.5:.1f}s"></div>'
        for d in gore.drips
    )
    return (PAGE
            .replace("__BEAT__", f"{60 / gore.bpm:.2f}")
            .replace("__POLY__", poly)
            .replace("__PATH__", path)
            .replace("__DRIPS__", drips)
            .encode("utf-8"))


def background_png(gore):
    img = Image.fromarray(gore.background.clip(0, 255).astype(np.uint8))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


def make_handler(page, background, camera, mirror, fps):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/":
                self._send(page, "text/html; charset=utf-8")
            elif self.path == "/background.png":
                self._send(background, "image/png")
            elif self.path == "/camera.mjpg":
                self._stream_camera()
            else:
                self.send_error(404)

        def _send(self, body, content_type):
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _stream_camera(self):
            self.send_response(200)
            self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={BOUNDARY}")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            try:
                while True:
                    frame = camera.read()
                    if mirror:
                        frame = frame[:, ::-1]
                    buf = io.BytesIO()
                    Image.fromarray(np.ascontiguousarray(frame)).save(buf, "JPEG", quality=80)
                    data = buf.getvalue()
                    self.wfile.write(
                        f"--{BOUNDARY}\r\nContent-Type: image/jpeg\r\n"
                        f"Content-Length: {len(data)}\r\n\r\n".encode() + data + b"\r\n")
                    time.sleep(1 / fps)
            except (BrokenPipeError, ConnectionResetError):
                pass  # the browser closed the stream

        def log_message(self, *args):
            pass

    return Handler


def serve(gore, camera, port=8000, mirror=False, fps=15):
    handler = make_handler(build_page(gore), background_png(gore), camera, mirror, fps)
    server = ThreadingHTTPServer(("127.0.0.1", port), handler)
    print(f"bullet hole on http://127.0.0.1:{port}/ (Ctrl-C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
