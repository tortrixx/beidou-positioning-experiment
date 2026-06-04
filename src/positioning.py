"""SPP 单点定位核心：逐历元用伪距、星历和误差改正估计接收机位置。"""

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
    """按优先级从一个卫星的观测值中选出可用于 SPP 的伪距。"""
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
    """补偿信号传播时间内地球自转造成的卫星坐标旋转。"""
    angle = OMEGA_E * tau
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    x = cos_a * pos[0] + sin_a * pos[1]
    y = -sin_a * pos[0] + cos_a * pos[1]
    return (x, y, pos[2])


def _ionosphere_coefficients(
    nav_header: NavHeader,
    system: str,
) -> Tuple[Optional[Tuple[float, float, float, float]], Optional[Tuple[float, float, float, float]]]:
    if system == "C" and nav_header.ion_corr:
        return nav_header.ion_corr.get("BDSA"), nav_header.ion_corr.get("BDSB")
    return nav_header.ion_alpha, nav_header.ion_beta


def _default_residual_gate_m(systems: Tuple[str, ...]) -> float:
    """给残差粗差剔除提供默认阈值，BDS 城市场景放宽一些。"""
    if "C" in systems:
        return 1000.0
    return 150.0


def _validate_receiver_state(lat: float, lon: float, height_m: float) -> None:
    values = (lat, lon, height_m)
    if not all(math.isfinite(value) for value in values):
        raise ValueError("接收机状态不是有限数值")
    if height_m < -1000.0 or height_m > 50000.0:
        raise ValueError("接收机高度超出当前 SPP 支持范围")


def _elevation_weight(elev_rad: float) -> float:
    """高度角越低观测越不可靠，因此给低高度角卫星更小权重。"""
    return max(math.sin(elev_rad) ** 2, 0.05)


def _solve_linear(a: List[List[float]], b: List[float]) -> List[float]:
    """用高斯消元解法方程，避免额外依赖 numpy。"""
    size = len(a)
    m = [row[:] + [b[idx]] for idx, row in enumerate(a)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("法方程矩阵奇异，无法解算")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        for j in range(col, size + 1):
            m[col][j] /= scale
        for r in range(size):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, size + 1):
                m[r][j] -= factor * m[col][j]
    return [m[r][size] for r in range(size)]


def _invert_matrix(a: List[List[float]]) -> List[List[float]]:
    size = len(a)
    m = [row[:] + [1.0 if i == j else 0.0 for j in range(size)] for i, row in enumerate(a)]
    for col in range(size):
        pivot = max(range(col, size), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            raise ValueError("法方程矩阵奇异，无法计算 DOP")
        m[col], m[pivot] = m[pivot], m[col]
        scale = m[col][col]
        for j in range(col, size * 2):
            m[col][j] /= scale
        for r in range(size):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, size * 2):
                m[r][j] -= factor * m[col][j]
    return [row[size : size * 2] for row in m]


def _solve_linear_4x4(a: List[List[float]], b: List[float]) -> List[float]:
    return _solve_linear(a, b)


def _invert_4x4(a: List[List[float]]) -> List[List[float]]:
    return _invert_matrix(a)


def single_point_position(
    epoch: ObsEpoch,
    nav_header: NavHeader,
    nav_records: List[NavRecord],
    approx_xyz: Tuple[float, float, float],
    max_iter: int = 8,
    elev_mask_deg: float = 10.0,
    systems: Tuple[str, ...] = ("G",),
    error_thresh_m: float = 0.01,
    residual_gate_m: Optional[float] = None,
    time_system: Optional[str] = None,
) -> PositionSolution:
    """对单个观测历元执行加权迭代最小二乘 SPP 解算。"""
    x, y, z = approx_xyz
    clock_bias_by_system: Dict[str, float] = {system: 0.0 for system in systems}
    active_systems: List[str] = []
    elev_mask = math.radians(elev_mask_deg)
    residual_gate = _default_residual_gate_m(systems) if residual_gate_m is None else residual_gate_m
    normal: List[List[float]] = []
    postfit_residuals: List[float] = []

    for iter_idx in range(max_iter):
        # 每次迭代都用当前接收机坐标重新计算卫星几何距离、方位角和高度角。
        lat, lon, h = ecef_to_geodetic(x, y, z)
        _validate_receiver_state(lat, lon, h)
        gps_time = epoch.time
        if time_system == "BDT":
            gps_time = epoch.time + timedelta(seconds=BDT_GPS_OFFSET)
        _, sow = gps_week_seconds(gps_time)

        geometry_rows: List[Tuple[str, List[float], float, float]] = []
        used_sats: List[str] = []

        for prn, obs in epoch.sat_obs.items():
            # 先按系统、伪距范围、星历和高度角筛掉不能参与解算的卫星。
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
            alpha, beta = _ionosphere_coefficients(nav_header, prn[0])
            iono = klobuchar_delay(lat, lon, elev, az, sow, alpha, beta)

            # corrected 是扣除卫星钟差、对流层、电离层后的伪距观测量。
            corrected = pseudorange + C * dt_sv - tropo - iono
            sat_system = prn[0]
            v = corrected - (rho + clock_bias_by_system.get(sat_system, 0.0))
            if iter_idx > 0 and abs(v) > residual_gate:
                continue

            geometry_rows.append((sat_system, [-dx / rho, -dy / rho, -dz / rho], v, _elevation_weight(elev)))
            used_sats.append(prn)

        active_systems = []
        for system, _, _, _ in geometry_rows:
            if system not in active_systems:
                active_systems.append(system)
        active_systems.sort(key=lambda system: systems.index(system) if system in systems else len(systems))
        if "G" in active_systems:
            active_systems.insert(0, active_systems.pop(active_systems.index("G")))

        # 未知量包括三维坐标改正，以及每个系统一个接收机钟差。
        unknown_count = 3 + len(active_systems)
        if len(geometry_rows) < unknown_count:
            raise ValueError("参与定位的卫星数量不足")

        normal = [[0.0 for _ in range(unknown_count)] for _ in range(unknown_count)]
        rhs = [0.0 for _ in range(unknown_count)]
        design_rows: List[Tuple[List[float], float]] = []
        for system, geometry, v, weight in geometry_rows:
            row = geometry + [1.0 if system == active_system else 0.0 for active_system in active_systems]
            design_rows.append((row, v))
            for i in range(unknown_count):
                rhs[i] += weight * row[i] * v
                for j in range(unknown_count):
                    normal[i][j] += weight * row[i] * row[j]

        dxs = _solve_linear(normal, rhs)
        if not all(math.isfinite(delta) for delta in dxs):
            raise ValueError("定位迭代结果不是有限数值")
        x += dxs[0]
        y += dxs[1]
        z += dxs[2]
        for idx, system in enumerate(active_systems):
            clock_bias_by_system[system] = clock_bias_by_system.get(system, 0.0) + dxs[3 + idx]
        postfit_residuals = [v - sum(row[i] * dxs[i] for i in range(unknown_count)) for row, v in design_rows]

        # 坐标改正量小于 error_thresh_m 时认为收敛；精度要求可在 CLI/GUI 参数处调整。
        if math.sqrt(dxs[0] ** 2 + dxs[1] ** 2 + dxs[2] ** 2) < error_thresh_m:
            break

    # 法方程逆矩阵的坐标部分用于计算 PDOP/GDOP。
    cov = _invert_matrix(normal)
    pdop = math.sqrt(cov[0][0] + cov[1][1] + cov[2][2])
    gdop = math.sqrt(cov[0][0] + cov[1][1] + cov[2][2] + cov[3][3])

    lat, lon, h = ecef_to_geodetic(x, y, z)
    ref_system = active_systems[0] if active_systems else (systems[0] if systems else "G")
    residual_rms = None
    residual_max = None
    if postfit_residuals:
        residual_rms = math.sqrt(sum(value * value for value in postfit_residuals) / len(postfit_residuals))
        residual_max = max(abs(value) for value in postfit_residuals)
    return PositionSolution(
        time=epoch.time,
        position_ecef=(x, y, z),
        clock_bias_m=clock_bias_by_system.get(ref_system, 0.0),
        position_blh=(math.degrees(lat), math.degrees(lon), h),
        used_sats=used_sats,
        pdop=pdop,
        gdop=gdop,
        residual_rms_m=residual_rms,
        residual_max_m=residual_max,
    )
