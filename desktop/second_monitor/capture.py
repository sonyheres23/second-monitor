from __future__ import annotations

import importlib.util
import io
import time


def placeholder_frame(width: int = 1280, height: int = 720) -> bytes:
    """Return a tiny SVG frame when optional screen-capture dependencies are absent."""

    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    svg = f"""<svg xmlns='http://www.w3.org/2000/svg' width='{width}' height='{height}'>
<rect width='100%' height='100%' fill='#101827'/>
<text x='48' y='90' fill='#ffffff' font-family='sans-serif' font-size='42'>Second Monitor USB Prototype</text>
<text x='48' y='155' fill='#9ca3af' font-family='sans-serif' font-size='28'>Install mss and pillow to stream the selected display.</text>
<text x='48' y='210' fill='#60a5fa' font-family='sans-serif' font-size='24'>{timestamp}</text>
</svg>"""
    return svg.encode("utf-8")


class FrameGrabber:
    """Capture the host display as JPEG bytes, falling back to an SVG status frame."""

    def __init__(self, monitor_index: int = 1, jpeg_quality: int = 65) -> None:
        self.monitor_index = monitor_index
        self.jpeg_quality = jpeg_quality

    def grab(self) -> tuple[bytes, str]:
        if importlib.util.find_spec("mss") is None or importlib.util.find_spec("PIL") is None:
            return placeholder_frame(), "image/svg+xml"

        import mss
        from PIL import Image

        with mss.mss() as sct:
            monitors = sct.monitors
            index = min(max(self.monitor_index, 1), len(monitors) - 1)
            shot = sct.grab(monitors[index])
            image = Image.frombytes("RGB", shot.size, shot.rgb)
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=self.jpeg_quality, optimize=True)
            return buffer.getvalue(), "image/jpeg"
