from __future__ import annotations

import math
from typing import Tuple

from constants import WGS84_A, WGS84_E2


def ecef_to_geodetic(x: float, y: float, z: float) -> Tuple[float, float, float]:
    p = math.hypot(x, y)
    lon = math.atan2(y, x)
    lat = math.atan2(z, p * (1.0 - WGS84_E2))
    h = 0.0

    for _ in range(6):
        sin_lat = math.sin(lat)
        n = WGS84_A / math.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        h = p / math.cos(lat) - n
        lat = math.atan2(z, p * (1.0 - WGS84_E2 * n / (n + h)))

    return lat, lon, h


def enu_from_ecef(dx: float, dy: float, dz: float, lat: float, lon: float) -> Tuple[float, float, float]:
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


def az_el_from_ecef(rx: Tuple[float, float, float], sat: Tuple[float, float, float]) -> Tuple[float, float]:
    lat, lon, _ = ecef_to_geodetic(*rx)
    dx = sat[0] - rx[0]
    dy = sat[1] - rx[1]
    dz = sat[2] - rx[2]
    east, north, up = enu_from_ecef(dx, dy, dz, lat, lon)

    az = math.atan2(east, north)
    if az < 0:
        az += 2.0 * math.pi
    horiz = math.hypot(east, north)
    elev = math.atan2(up, horiz)
    return az, elev
