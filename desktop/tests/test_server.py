import json
import threading
import urllib.request

from second_monitor.geometry import Rect
from second_monitor.server import MonitorServer, MonitorState


def test_health_endpoint_reports_ok() -> None:
    server = MonitorServer(("127.0.0.1", 0), MonitorState(Rect(0, 0, 100, 100), inject_touch=False), fps=1)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        url = f"http://127.0.0.1:{server.server_port}/health"
        with urllib.request.urlopen(url, timeout=2) as response:
            payload = json.loads(response.read())
        assert payload == {"ok": True, "touchInjection": False}
    finally:
        server.shutdown()
        thread.join(timeout=2)
