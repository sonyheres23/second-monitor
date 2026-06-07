from __future__ import annotations

import argparse
import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .adb import AdbError, reverse_port
from .capture import FrameGrabber
from .geometry import CoordinateMapper, Rect, TouchPoint
from .input_linux import InputInjector


class MonitorState:
    def __init__(self, target: Rect, inject_touch: bool) -> None:
        self.mapper = CoordinateMapper(target)
        self.grabber = FrameGrabber()
        self.injector = InputInjector(enabled=inject_touch)
        self.last_touch: dict[str, object] | None = None


class MonitorHandler(BaseHTTPRequestHandler):
    server: "MonitorServer"

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json({"ok": True, "touchInjection": self.server.state.injector.available})
            return
        if self.path == "/frame":
            frame, content_type = self.server.state.grabber.grab()
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(frame)))
            self.end_headers()
            self.wfile.write(frame)
            return
        if self.path == "/stream":
            self._stream_frames()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def do_POST(self) -> None:
        if self.path != "/touch":
            self.send_error(HTTPStatus.NOT_FOUND)
            return
        length = int(self.headers.get("Content-Length", "0"))
        payload = json.loads(self.rfile.read(length) or b"{}")
        point = TouchPoint(
            x=float(payload["x"]),
            y=float(payload["y"]),
            source_width=float(payload["width"]),
            source_height=float(payload["height"]),
        )
        host_x, host_y = self.server.state.mapper.map_point(point)
        action = str(payload.get("action", "move"))
        injected = self.server.state.injector.tap(host_x, host_y) if action == "tap" else self.server.state.injector.move(host_x, host_y)
        self.server.state.last_touch = {"x": host_x, "y": host_y, "action": action, "injected": injected}
        self._send_json(self.server.state.last_touch)

    def log_message(self, format: str, *args: object) -> None:
        print(f"{self.address_string()} - {format % args}")

    def _send_json(self, payload: dict[str, object]) -> None:
        data = json.dumps(payload).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _stream_frames(self) -> None:
        boundary = "second-monitor-frame"
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", f"multipart/x-mixed-replace; boundary={boundary}")
        self.end_headers()
        while True:
            frame, content_type = self.server.state.grabber.grab()
            self.wfile.write(f"--{boundary}\r\n".encode("ascii"))
            self.wfile.write(f"Content-Type: {content_type}\r\n".encode("ascii"))
            self.wfile.write(f"Content-Length: {len(frame)}\r\n\r\n".encode("ascii"))
            self.wfile.write(frame + b"\r\n")
            self.wfile.flush()
            time.sleep(1 / self.server.fps)


class MonitorServer(ThreadingHTTPServer):
    def __init__(self, address: tuple[str, int], state: MonitorState, fps: int) -> None:
        super().__init__(address, MonitorHandler)
        self.state = state
        self.fps = fps


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the desktop companion for an ADB USB second monitor.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--fps", type=int, default=15)
    parser.add_argument("--target-x", type=int, default=1920)
    parser.add_argument("--target-y", type=int, default=0)
    parser.add_argument("--target-width", type=int, default=1280)
    parser.add_argument("--target-height", type=int, default=720)
    parser.add_argument("--no-adb-reverse", action="store_true")
    parser.add_argument("--no-touch-injection", action="store_true")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    if not args.no_adb_reverse:
        try:
            reverse_port(args.port)
            print(f"ADB reverse is active: tablet 127.0.0.1:{args.port} -> laptop {args.host}:{args.port}")
        except AdbError as exc:
            print(f"ADB reverse setup skipped: {exc}")
    state = MonitorState(
        Rect(args.target_x, args.target_y, args.target_width, args.target_height),
        inject_touch=not args.no_touch_injection,
    )
    server = MonitorServer((args.host, args.port), state, max(1, args.fps))
    print(f"Serving second monitor stream on http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
