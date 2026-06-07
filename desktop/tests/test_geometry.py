import pytest

from second_monitor.geometry import CoordinateMapper, Rect, TouchPoint


def test_maps_tablet_center_to_virtual_monitor_center() -> None:
    mapper = CoordinateMapper(Rect(x=1920, y=0, width=1280, height=720))

    assert mapper.map_point(TouchPoint(x=500, y=250, source_width=1000, source_height=500)) == (2560, 360)


def test_clamps_touch_points_to_target_bounds() -> None:
    mapper = CoordinateMapper(Rect(x=100, y=50, width=200, height=100))

    assert mapper.map_point(TouchPoint(x=300, y=-20, source_width=100, source_height=100)) == (299, 50)


def test_rejects_invalid_dimensions() -> None:
    with pytest.raises(ValueError):
        CoordinateMapper(Rect(x=0, y=0, width=0, height=1))

    mapper = CoordinateMapper(Rect(x=0, y=0, width=1, height=1))
    with pytest.raises(ValueError):
        mapper.map_point(TouchPoint(x=0, y=0, source_width=0, source_height=1))
