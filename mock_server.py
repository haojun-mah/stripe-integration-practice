"""Provided local API and tiny PNG renderer. This is not candidate work.

Run: python mock_server.py --port 8765
Only the Python standard library is used. No external map requests are made.
"""

import argparse
from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import struct
import threading
from urllib.parse import urlsplit
import uuid
import zlib

API_KEY = "practice-map-key"
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
COLORS = {"blue": (36, 97, 210), "brown": (148, 84, 42), "white": (255, 255, 255)}


def _number(value):
    return type(value) is int or (type(value) is float and math.isfinite(value))


def _coordinate(value):
    return (
        isinstance(value, dict)
        and set(value) == {"lat", "lon"}
        and _number(value["lat"])
        and _number(value["lon"])
        and -90 <= value["lat"] <= 90
        and -180 <= value["lon"] <= 180
    )


def validate_payload(payload):
    if not isinstance(payload, dict):
        return "body must be a JSON object"
    required = {"center", "width", "height", "zoom"}
    if not required <= payload.keys():
        return "center, width, height, and zoom are required"
    if payload.keys() - required - {"markers", "paths"}:
        return "unknown map field"
    if not _coordinate(payload["center"]):
        return "center must contain valid lat and lon numbers"
    for field in ("width", "height"):
        if type(payload[field]) is not int or not 100 <= payload[field] <= 1200:
            return f"{field} must be an integer from 100 to 1200"
    if type(payload["zoom"]) is not int or not 1 <= payload["zoom"] <= 20:
        return "zoom must be an integer from 1 to 20"
    markers, paths = payload.get("markers", []), payload.get("paths", [])
    if not isinstance(markers, list) or len(markers) > 20:
        return "markers must be an array of at most 20 entries"
    if not isinstance(paths, list) or len(paths) > 1000:
        return "paths must be an array of at most 1000 entries"
    for marker in markers:
        if not isinstance(marker, dict) or set(marker) != {"color", "label", "coord"}:
            return "marker fields must be color, label, coord"
        if marker["color"] not in ("white", "blue", "brown"):
            return "unsupported marker color"
        if marker["label"] not in ("Start", "Stripe") or not _coordinate(marker["coord"]):
            return "invalid marker label or coordinate"
    total = 0
    for path in paths:
        if not isinstance(path, dict) or set(path) != {"color", "positions"}:
            return "path fields must be color and positions"
        if path["color"] not in ("blue", "brown"):
            return "unsupported path color"
        positions = path["positions"]
        if not isinstance(positions, list) or len(positions) < 2:
            return "each path needs at least two positions"
        if not all(_coordinate(position) for position in positions):
            return "invalid path coordinate"
        total += len(positions)
    if total > 20000:
        return "too many path positions"
    return None


def render_png(payload):
    """Draw a schematic local grid, projected polylines, and labeled markers."""
    width, height = payload["width"], payload["height"]
    pixels = bytearray((244, 247, 242)) * (width * height)

    def pixel(x, y, color):
        if 0 <= x < width and 0 <= y < height:
            offset = (y * width + x) * 3
            pixels[offset:offset + 3] = bytes(color)

    for y in range(height):
        for x in range(width):
            if x % 40 == 0 or y % 40 == 0:
                pixel(x, y, (220, 228, 219))

    scale = 256 * (2 ** payload["zoom"]) / 360
    center = payload["center"]

    def latitude_y(lat):
        lat = max(-85.0511, min(85.0511, lat))
        return math.degrees(math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)))

    center_y = latitude_y(center["lat"])

    def project(coord):
        return (
            width / 2 + (coord["lon"] - center["lon"]) * scale,
            height / 2 + (center_y - latitude_y(coord["lat"])) * scale,
        )

    def dot(x, y, radius, color):
        x, y = round(x), round(y)
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    pixel(x + dx, y + dy, color)

    def line(first, second, color):
        # Clip first so distant, valid geographic coordinates cannot cause huge loops.
        x0, y0 = first
        dx, dy = second[0] - x0, second[1] - y0
        lower, upper = 0.0, 1.0
        for p, q in ((-dx, x0), (dx, width - 1 - x0), (-dy, y0), (dy, height - 1 - y0)):
            if p == 0:
                if q < 0:
                    return
                continue
            bound = q / p
            if p < 0:
                lower = max(lower, bound)
            else:
                upper = min(upper, bound)
            if lower > upper:
                return
        xa, ya = x0 + lower * dx, y0 + lower * dy
        xb, yb = x0 + upper * dx, y0 + upper * dy
        steps = max(1, math.ceil(max(abs(xb - xa), abs(yb - ya))))
        for step in range(steps + 1):
            fraction = step / steps
            dot(xa + fraction * (xb - xa), ya + fraction * (yb - ya), 2, color)

    for path in payload.get("paths", []):
        positions = [project(position) for position in path["positions"]]
        for first, second in zip(positions, positions[1:]):
            line(first, second, COLORS[path["color"]])

    font = {
        "A": ("010", "101", "111", "101", "101"),
        "E": ("111", "100", "110", "100", "111"),
        "I": ("111", "010", "010", "010", "111"),
        "P": ("110", "101", "110", "100", "100"),
        "R": ("110", "101", "110", "101", "101"),
        "S": ("111", "100", "111", "001", "111"),
        "T": ("111", "010", "010", "010", "010"),
    }
    for marker in payload.get("markers", []):
        x, y = project(marker["coord"])
        dot(x, y, 8, (40, 48, 55))
        dot(x, y, 6, COLORS[marker["color"]])
        for index, char in enumerate(marker["label"].upper()):
            for row, pattern in enumerate(font[char]):
                for col, filled in enumerate(pattern):
                    if filled == "1":
                        for dy in range(2):
                            for dx in range(2):
                                pixel(round(x) + 12 + index * 8 + col * 2 + dx,
                                      round(y) - 5 + row * 2 + dy, (30, 37, 44))

    def chunk(kind, body):
        return (struct.pack("!I", len(body)) + kind + body
                + struct.pack("!I", zlib.crc32(kind + body) & 0xFFFFFFFF))

    rows = b"".join(b"\x00" + pixels[y * width * 3:(y + 1) * width * 3]
                    for y in range(height))
    header = struct.pack("!IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(rows)) + chunk(b"IEND", b"")


class PracticeServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address):
        super().__init__(address, Handler)
        self.calls = []
        self.calls_lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    server_version = "PracticeStaticMap/1.0"

    def log_message(self, *_):
        pass

    def _send(self, status, body, content_type):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-Request-Id", str(uuid.uuid4()))
        self.end_headers()
        try:
            self.wfile.write(body)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def _json(self, status, value):
        self._send(status, json.dumps(value).encode(), "application/json")

    def _error(self, status, code, message):
        self._json(status, {"error": {"code": code, "message": message}})

    def do_GET(self):
        path = urlsplit(self.path).path
        if path == "/health":
            self._json(200, {"status": "ok", "service": "practice-staticmap"})
        elif path == "/__requests":
            with self.server.calls_lock:
                calls = list(self.server.calls)
            self._json(200, {"requests": calls})
        else:
            self._error(404, "not_found", "unknown endpoint")

    def do_POST(self):
        if urlsplit(self.path).path != "/map.png":
            self._error(404, "not_found", "unknown endpoint")
            return
        if self.headers.get("Authorization") != f"Bearer {API_KEY}":
            self._error(401, "unauthorized", "invalid development API key")
            return
        if self.headers.get("Content-Type", "").split(";")[0].lower() != "application/json":
            self._error(415, "unsupported_media_type", "send a JSON request body")
            return
        if "image/png" not in self.headers.get("Accept", ""):
            self._error(415, "unsupported_media_type", "Accept must include image/png")
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            self._error(400, "invalid_request", "invalid content length")
            return
        if not 0 <= length <= 2_000_000:
            self._error(413, "payload_too_large", "body exceeds the request limit")
            return
        try:
            payload = json.loads(self.rfile.read(length))
        except (ValueError, UnicodeDecodeError):
            self._error(400, "invalid_request", "invalid JSON body")
            return
        with self.server.calls_lock:
            self.server.calls.append({"method": "POST", "path": "/map.png", "payload": payload})
            self.server.calls[:] = self.server.calls[-100:]
        problem = validate_payload(payload)
        if problem:
            self._error(400, "invalid_request", problem)
            return
        self._send(200, render_png(payload), "image/png")


@contextmanager
def running_server():
    """Acceptance-test helper: bind an unused local port and clean up afterward."""
    server = PracticeServer(("127.0.0.1", 0))
    thread = threading.Thread(target=server.serve_forever, kwargs={"poll_interval": 0.02}, daemon=True)
    thread.start()
    try:
        yield server, f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    server = PracticeServer(("127.0.0.1", args.port))
    print(f"Practice map API: http://127.0.0.1:{server.server_port}", flush=True)
    print("Ctrl+C to stop. No external API calls are made.", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
