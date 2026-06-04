"""坐标转换工具：ECEF、经纬高 BLH、站心 ENU 和卫星方位高度角。"""

from __future__ import annotations

import math
from typing import Tuple

from constants import WGS84_A, WGS84_E2


def ecef_to_geodetic(x: float, y: float, z: float) -> Tuple[float, float, float]:
    """WGS84 ECEF 坐标转大地纬度、经度和高程。"""
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
    """把 ECEF 差分向量旋转到本地 East/North/Up 坐标系。"""
    sin_lat = math.sin(lat)
    cos_lat = math.cos(lat)
    sin_lon = math.sin(lon)
    cos_lon = math.cos(lon)

    east = -sin_lon * dx + cos_lon * dy
    north = -sin_lat * cos_lon * dx - sin_lat * sin_lon * dy + cos_lat * dz
    up = cos_lat * cos_lon * dx + cos_lat * sin_lon * dy + sin_lat * dz
    return east, north, up


def az_el_from_ecef(rx: Tuple[float, float, float], sat: Tuple[float, float, float]) -> Tuple[float, float]:
    """由接收机和卫星 ECEF 坐标计算卫星方位角和高度角。"""
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
