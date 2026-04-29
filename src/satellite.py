from __future__ import annotations

import math
from datetime import datetime, timedelta
from typing import Iterable, Optional, Tuple

from constants import BDT_GPS_OFFSET, F_REL, MU_BDS, MU_GPS, OMEGA_E, OMEGA_E_BDS
from models import NavRecord
from time_utils import adjust_week, gnss_week_seconds

BDS_GEO_INCLINATION_OFFSET = math.radians(-5.0)


def _apply_time_offset(prn: str, t: datetime, time_system: Optional[str]) -> datetime:
    if prn.startswith("C") and time_system != "BDT":
        return t - timedelta(seconds=BDT_GPS_OFFSET)
    return t


def _is_bds_geo(prn: str) -> bool:
    if not prn.startswith("C"):
        return False
    try:
        number = int(prn[1:])
    except ValueError:
        return False
    return 1 <= number <= 5


def select_ephemeris(
    records: Iterable[NavRecord],
    prn: str,
    t: datetime,
    time_system: Optional[str] = None,
) -> Optional[NavRecord]:
    t_ref = _apply_time_offset(prn, t, time_system)
    _, sow = gnss_week_seconds(prn[0], t_ref)
    best: Optional[NavRecord] = None
    best_dt = float("inf")
    for record in records:
        if record.prn != prn:
            continue
        if record.sv_health > 0:
            continue
        tk = adjust_week(sow - record.toe)
        dt = abs(tk)
        if dt < best_dt:
            best_dt = dt
            best = record
    return best


def satellite_position_and_clock(
    record: NavRecord,
    t: datetime,
    time_system: Optional[str] = None,
) -> Tuple[Tuple[float, float, float], float]:
    system = record.prn[0]
    t_ref = _apply_time_offset(record.prn, t, time_system)
    _, sow = gnss_week_seconds(system, t_ref)
    toc_week, toc_sow = gnss_week_seconds(system, record.epoch)
    _ = toc_week

    tk = adjust_week(sow - record.toe)
    dt = adjust_week(sow - toc_sow)

    a = record.sqrt_a * record.sqrt_a
    mu = MU_BDS if system == "C" else MU_GPS
    omega_e = OMEGA_E_BDS if system == "C" else OMEGA_E
    n0 = math.sqrt(mu / (a * a * a))
    n = n0 + record.delta_n
    m = record.m0 + n * tk

    e = record.e
    ek = m
    for _ in range(10):
        ek = m + e * math.sin(ek)

    sin_e = math.sin(ek)
    cos_e = math.cos(ek)
    v = math.atan2(math.sqrt(1.0 - e * e) * sin_e, cos_e - e)
    phi = v + record.omega

    sin2phi = math.sin(2.0 * phi)
    cos2phi = math.cos(2.0 * phi)

    du = record.cus * sin2phi + record.cuc * cos2phi
    dr = record.crs * sin2phi + record.crc * cos2phi
    di = record.cis * sin2phi + record.cic * cos2phi

    u = phi + du
    r = a * (1.0 - e * cos_e) + dr
    i = record.i0 + di + record.idot * tk

    x_orb = r * math.cos(u)
    y_orb = r * math.sin(u)

    if _is_bds_geo(record.prn):
        omega = record.omega0 + record.omega_dot * tk - omega_e * record.toe
    else:
        omega = record.omega0 + (record.omega_dot - omega_e) * tk - omega_e * record.toe
    cos_omega = math.cos(omega)
    sin_omega = math.sin(omega)
    cos_i = math.cos(i)
    sin_i = math.sin(i)

    x_g = x_orb * cos_omega - y_orb * cos_i * sin_omega
    y_g = x_orb * sin_omega + y_orb * cos_i * cos_omega
    z_g = y_orb * sin_i

    if _is_bds_geo(record.prn):
        sin_rot = math.sin(omega_e * tk)
        cos_rot = math.cos(omega_e * tk)
        sin_offset = math.sin(BDS_GEO_INCLINATION_OFFSET)
        cos_offset = math.cos(BDS_GEO_INCLINATION_OFFSET)
        x = x_g * cos_rot + y_g * sin_rot * cos_offset + z_g * sin_rot * sin_offset
        y = -x_g * sin_rot + y_g * cos_rot * cos_offset + z_g * cos_rot * sin_offset
        z = -y_g * sin_offset + z_g * cos_offset
    else:
        x = x_g
        y = y_g
        z = z_g

    dtr = F_REL * e * record.sqrt_a * sin_e
    dt_sv = record.af0 + record.af1 * dt + record.af2 * dt * dt + dtr - record.tgd

    return (x, y, z), dt_sv
