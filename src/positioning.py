from __future__ import annotations

import math
from datetime import timedelta
from typing import Dict, List, Optional, Tuple

from atmosphere import klobuchar_delay, saastamoinen_delay
from constants import BDT_GPS_OFFSET, C, OMEGA_E
from coords import az_el_from_ecef, ecef_to_geodetic
from models import NavHeader, NavRecord, ObsEpoch, PositionSolution
from satellite import satellite_position_and_clock, select_ephemeris
from time_utils import gps_week_seconds


def _choose_pseudorange(obs: Dict[str, Optional[float]]) -> Optional[float]:
    for key in (
        "C1",
        "P1",
        "P2",
        "C1C",
        "C1W",
        "C1I",
        "C2I",
        "C6I",
        "C7I",
        "C2X",
        "C6X",
        "C7X",
    ):
        value = obs.get(key)
        if value is not None:
            return value
    return None


def _earth_rotation_correction(pos: Tuple[float, float, float], tau: float) -> Tuple[float, float, float]:
    angle = OMEGA_E * tau
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x = cos_a * pos[0] + sin_a * pos[1]
    y = -sin_a * pos[0] + cos_a * pos[1]
    return (x, y, pos[2])


def _solve_linear_4x4(a: List[List[float]], b: List[float]) -> List[float]:
    m = [row[:] + [b[idx]] for idx, row in enumerate(a)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("Singular normal matrix")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        for j in range(col, 5):
            m[col][j] /= scale
        for r in range(4):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, 5):
                m[r][j] -= factor * m[col][j]
    return [m[r][4] for r in range(4)]


def _invert_4x4(a: List[List[float]]) -> List[List[float]]:
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(4)] for i, row in enumerate(a)]
    for col in range(4):
        pivot = max(range(col, 4), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("Singular normal matrix")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        for j in range(col, 8):
            m[col][j] /= scale
        for r in range(4):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, 8):
                m[r][j] -= factor * m[col][j]
    return [row[4:8] for row in m]


def single_point_position(
    epoch: ObsEpoch,
    nav_header: NavHeader,
    nav_records: List[NavRecord],
    approx_xyz: Tuple[float, float, float],
    max_iter: int = 8,
    elev_mask_deg: float = 10.0,
    systems: Tuple[str, ...] = ("G",),
    error_thresh_m: float = 0.01,
    residual_gate_m: float = 150.0,
    time_system: Optional[str] = None,
) -> PositionSolution:
    x, y, z = approx_xyz
    clock_bias_m = 0.0
    elev_mask = math.radians(elev_mask_deg)

    for iter_idx in range(max_iter):
        lat, lon, h = ecef_to_geodetic(x, y, z)
        gps_time = epoch.time
        if time_system == "BDT":
            gps_time = epoch.time - timedelta(seconds=BDT_GPS_OFFSET)
        _, sow = gps_week_seconds(gps_time)

        h_rows: List[List[float]] = []
        v_rows: List[float] = []
        used_sats: List[str] = []

        for prn, obs in epoch.sat_obs.items():
            if not prn:
                continue
            if prn[0] not in systems:
                continue
            pseudorange = _choose_pseudorange(obs)
            if pseudorange is None:
                continue
            if pseudorange < 1.0e7 or pseudorange > 6.0e7:
                continue

            tau = pseudorange / C
            t_tx = epoch.time - timedelta(seconds=tau)
            record = select_ephemeris(nav_records, prn, t_tx, time_system=time_system)
            if record is None:
                continue

            sat_pos, dt_sv = satellite_position_and_clock(record, t_tx, time_system=time_system)
            sat_pos = _earth_rotation_correction(sat_pos, tau)

            dx = sat_pos[0] - x
            dy = sat_pos[1] - y
            dz = sat_pos[2] - z
            rho = math.sqrt(dx * dx + dy * dy + dz * dz)

            az, elev = az_el_from_ecef((x, y, z), sat_pos)
            if elev < elev_mask:
                continue

            tropo = saastamoinen_delay(lat, h, elev)
            iono = 0.0
            if prn[0] == "G":
                iono = klobuchar_delay(lat, lon, elev, az, sow, nav_header.ion_alpha, nav_header.ion_beta)

            corrected = pseudorange + C * dt_sv - tropo - iono
            v = corrected - (rho + clock_bias_m)
            if iter_idx > 0 and abs(v) > residual_gate_m:
                continue

            h_row = [-dx / rho, -dy / rho, -dz / rho, 1.0]
            h_rows.append(h_row)
            v_rows.append(v)
            used_sats.append(prn)

        if len(h_rows) < 4:
            raise ValueError("Not enough satellites for positioning")

        normal = [[0.0 for _ in range(4)] for _ in range(4)]
        rhs = [0.0 for _ in range(4)]
        for row, v in zip(h_rows, v_rows):
            for i in range(4):
                rhs[i] += row[i] * v
                for j in range(4):
                    normal[i][j] += row[i] * row[j]

        dxs = _solve_linear_4x4(normal, rhs)
        x += dxs[0]
        y += dxs[1]
        z += dxs[2]
        clock_bias_m += dxs[3]

        if math.sqrt(dxs[0] ** 2 + dxs[1] ** 2 + dxs[2] ** 2) < error_thresh_m:
            break

    cov = _invert_4x4(normal)
    pdop = math.sqrt(cov[0][0] + cov[1][1] + cov[2][2])
    gdop = math.sqrt(cov[0][0] + cov[1][1] + cov[2][2] + cov[3][3])

    lat, lon, h = ecef_to_geodetic(x, y, z)
    return PositionSolution(
        time=epoch.time,
        position_ecef=(x, y, z),
        clock_bias_m=clock_bias_m,
        position_blh=(math.degrees(lat), math.degrees(lon), h),
        used_sats=used_sats,
        pdop=pdop,
        gdop=gdop,
    )
