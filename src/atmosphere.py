from __future__ import annotations

import math
from typing import Optional, Tuple

from constants import C


def saastamoinen_delay(lat: float, height_m: float, elev_rad: float) -> float:
    if elev_rad <= 0:
        return 0.0

    pressure = 1013.25 * (1.0 - 2.2557e-5 * height_m) ** 5.2568
    temperature = 15.0 - 0.0065 * height_m + 273.15
    humidity = 0.5
    e = humidity * 6.108 * math.exp((17.15 * (temperature - 273.15)) / (234.7 + (temperature - 273.15)))

    zhd = 0.0022768 * pressure / (1.0 - 0.00266 * math.cos(2.0 * lat) - 0.00028 * height_m / 1000.0)
    zwd = 0.002277 * (1255.0 / temperature + 0.05) * e

    mapping = 1.0 / math.sin(elev_rad)
    return (zhd + zwd) * mapping


def klobuchar_delay(
    lat: float,
    lon: float,
    elev_rad: float,
    az_rad: float,
    gps_tow: float,
    alpha: Optional[Tuple[float, float, float, float]],
    beta: Optional[Tuple[float, float, float, float]],
) -> float:
    if alpha is None or beta is None:
        return 0.0

    lat_sc = lat / math.pi
    lon_sc = lon / math.pi
    az_sc = az_rad / math.pi
    el_sc = elev_rad / math.pi

    psi = 0.0137 / (el_sc + 0.11) - 0.022
    phi_i = lat_sc + psi * math.cos(az_rad)
    if phi_i > 0.416:
        phi_i = 0.416
    elif phi_i < -0.416:
        phi_i = -0.416

    lam_i = lon_sc + psi * math.sin(az_rad) / math.cos(phi_i * math.pi)
    phi_m = phi_i + 0.064 * math.cos((lam_i - 1.617) * math.pi)

    t_local = 43200.0 * lam_i + gps_tow
    t_local = t_local % 86400.0

    amp = alpha[0] + alpha[1] * phi_m + alpha[2] * phi_m * phi_m + alpha[3] * phi_m * phi_m * phi_m
    if amp < 0:
        amp = 0.0

    per = beta[0] + beta[1] * phi_m + beta[2] * phi_m * phi_m + beta[3] * phi_m * phi_m * phi_m
    if per < 72000.0:
        per = 72000.0

    x = 2.0 * math.pi * (t_local - 50400.0) / per
    if abs(x) < 1.57:
        iono = 5e-9 + amp * (1.0 - x * x / 2.0 + x * x * x * x / 24.0)
    else:
        iono = 5e-9

    f = 1.0 + 16.0 * (0.53 - el_sc) ** 3
    return C * f * iono
