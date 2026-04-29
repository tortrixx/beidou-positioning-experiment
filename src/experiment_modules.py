from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional, Tuple

from analysis import compute_errors, summarize_errors
from atmosphere import klobuchar_delay, saastamoinen_delay
from constants import BDT_GPS_OFFSET, C
from coords import az_el_from_ecef, ecef_to_geodetic
from models import NavHeader, NavRecord, ObsEpoch, ObsHeader, PositionSolution
from pipeline import run_continuous_pipeline, write_csv
from plotting import plot_error_and_dop, plot_trajectory
from positioning import _choose_pseudorange, _earth_rotation_correction, _ionosphere_coefficients, single_point_position
from rinex_nav import parse_rinex_nav
from rinex_obs import parse_rinex_obs
from satellite import satellite_position_and_clock, select_ephemeris
from time_utils import gps_week_seconds


@dataclass
class RinexDataset:
    obs_header: ObsHeader
    epochs: List[ObsEpoch]
    nav_header: NavHeader
    nav_records: List[NavRecord]


@dataclass
class SatelliteMeasurement:
    prn: str
    pseudorange_m: float
    corrected_pseudorange_m: float
    satellite_position_ecef: Tuple[float, float, float]
    satellite_clock_s: float
    azimuth_deg: float
    elevation_deg: float
    troposphere_delay_m: float
    ionosphere_delay_m: float


@dataclass
class SystemRunResult:
    obs_header: ObsHeader
    solutions: List[PositionSolution]
    errors: List[Dict[str, float]]
    stats: Dict[str, float]


class RinexDataModule:
    """模块1：RINEX 数据解析与基础预处理。"""

    def load(self, obs_path: str | Path, nav_path: str | Path) -> RinexDataset:
        obs_file = Path(obs_path)
        nav_file = Path(nav_path)
        if not obs_file.exists():
            raise FileNotFoundError(f"Observation file not found: {obs_file}")
        if not nav_file.exists():
            raise FileNotFoundError(f"Navigation file not found: {nav_file}")

        obs_header, epochs = parse_rinex_obs(obs_file)
        nav_header, nav_records = parse_rinex_nav(nav_file)
        if obs_header.approx_position_xyz is None:
            raise ValueError("Missing approximate receiver position in obs header")
        if not epochs:
            raise ValueError("No observation epochs found")
        if not nav_records:
            raise ValueError("No navigation records found")
        return RinexDataset(obs_header, epochs, nav_header, nav_records)

    def valid_observations(
        self,
        epoch: ObsEpoch,
        systems: Iterable[str] = ("G",),
        pseudorange_limits_m: Tuple[float, float] = (1.0e7, 6.0e7),
    ) -> Dict[str, float]:
        allowed_systems = tuple(systems)
        valid: Dict[str, float] = {}
        for prn, obs in epoch.sat_obs.items():
            if not prn or prn[0] not in allowed_systems:
                continue
            pseudorange = _choose_pseudorange(obs)
            if pseudorange is None:
                continue
            if pseudorange_limits_m[0] <= pseudorange <= pseudorange_limits_m[1]:
                valid[prn] = pseudorange
        return valid


class SatelliteCorrectionModule:
    """模块2：卫星位置、钟差、对流层与电离层改正。"""

    def __init__(self, nav_header: NavHeader, nav_records: List[NavRecord]) -> None:
        self.nav_header = nav_header
        self.nav_records = nav_records

    def visible_measurements(
        self,
        epoch: ObsEpoch,
        receiver_xyz: Optional[Tuple[float, float, float]],
        elev_mask_deg: float = 10.0,
        systems: Iterable[str] = ("G",),
        time_system: Optional[str] = None,
    ) -> List[SatelliteMeasurement]:
        if receiver_xyz is None:
            raise ValueError("receiver_xyz is required")

        allowed_systems = tuple(systems)
        elev_mask = math.radians(elev_mask_deg)
        lat, lon, height = ecef_to_geodetic(*receiver_xyz)
        gps_time = epoch.time + timedelta(seconds=BDT_GPS_OFFSET) if time_system == "BDT" else epoch.time
        _, sow = gps_week_seconds(gps_time)
        measurements: List[SatelliteMeasurement] = []

        for prn, obs in epoch.sat_obs.items():
            if not prn or prn[0] not in allowed_systems:
                continue
            pseudorange = _choose_pseudorange(obs)
            if pseudorange is None or pseudorange < 1.0e7 or pseudorange > 6.0e7:
                continue

            tau = pseudorange / C
            transmit_time = epoch.time - timedelta(seconds=tau)
            record = select_ephemeris(self.nav_records, prn, transmit_time, time_system=time_system)
            if record is None:
                continue

            sat_pos, sat_clock = satellite_position_and_clock(record, transmit_time, time_system=time_system)
            sat_pos = _earth_rotation_correction(sat_pos, tau)
            azimuth, elevation = az_el_from_ecef(receiver_xyz, sat_pos)
            if elevation < elev_mask:
                continue

            tropo = saastamoinen_delay(lat, height, elevation)
            alpha, beta = _ionosphere_coefficients(self.nav_header, prn[0])
            iono = klobuchar_delay(lat, lon, elevation, azimuth, sow, alpha, beta)
            corrected = pseudorange + C * sat_clock - tropo - iono

            measurements.append(
                SatelliteMeasurement(
                    prn=prn,
                    pseudorange_m=pseudorange,
                    corrected_pseudorange_m=corrected,
                    satellite_position_ecef=sat_pos,
                    satellite_clock_s=sat_clock,
                    azimuth_deg=math.degrees(azimuth),
                    elevation_deg=math.degrees(elevation),
                    troposphere_delay_m=tropo,
                    ionosphere_delay_m=iono,
                )
            )
        return measurements


class SinglePointPositioningModule:
    """模块3：可见卫星筛选、DOP 计算与迭代最小二乘 SPP。"""

    def __init__(self, nav_header: NavHeader, nav_records: List[NavRecord]) -> None:
        self.nav_header = nav_header
        self.nav_records = nav_records

    def solve_epoch(
        self,
        epoch: ObsEpoch,
        approx_xyz: Optional[Tuple[float, float, float]],
        max_iter: int = 8,
        elev_mask_deg: float = 10.0,
        systems: Iterable[str] = ("G",),
        error_thresh_m: float = 0.01,
        residual_gate_m: Optional[float] = None,
        time_system: Optional[str] = None,
    ) -> PositionSolution:
        if approx_xyz is None:
            raise ValueError("approx_xyz is required")
        return single_point_position(
            epoch,
            self.nav_header,
            self.nav_records,
            approx_xyz,
            max_iter=max_iter,
            elev_mask_deg=elev_mask_deg,
            systems=tuple(systems),
            error_thresh_m=error_thresh_m,
            residual_gate_m=residual_gate_m,
            time_system=time_system,
        )


class ContinuousAnalysisModule:
    """模块4：连续定位结果、误差统计、CSV 与图表输出。"""

    def evaluate(
        self,
        solutions: List[PositionSolution],
        reference_xyz: Optional[Tuple[float, float, float]],
    ) -> Tuple[List[Dict[str, float]], Dict[str, float]]:
        if reference_xyz is None:
            raise ValueError("reference_xyz is required")
        errors = compute_errors(solutions, reference_xyz)
        return errors, summarize_errors(errors)

    def export_csv(self, path: str | Path, solutions: List[PositionSolution], errors: List[Dict[str, float]]) -> None:
        write_csv(str(path), solutions, errors)

    def save_plots(
        self,
        output_dir: str | Path,
        solutions: List[PositionSolution],
        errors: List[Dict[str, float]],
    ) -> Tuple[Path, Path]:
        out_dir = Path(output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        times = list(range(len(solutions)))
        horiz = [err["horiz"] for err in errors]
        three_d = [err["three_d"] for err in errors]
        pdop = [sol.pdop or float("nan") for sol in solutions]
        lat = [sol.position_blh[0] for sol in solutions]
        lon = [sol.position_blh[1] for sol in solutions]

        error_path = out_dir / "error_dop.png"
        trajectory_path = out_dir / "trajectory.png"
        if not plot_error_and_dop(times, horiz, three_d, pdop, str(error_path)):
            raise RuntimeError("Failed to save error/DOP plot")
        if not plot_trajectory(lat, lon, str(trajectory_path)):
            raise RuntimeError("Failed to save trajectory plot")
        return error_path, trajectory_path


class SoftwareSystemModule:
    """模块5：完整软件系统整合与自动化运行入口。"""

    def run(
        self,
        obs_path: str | Path,
        nav_path: str | Path,
        step: int = 1,
        max_epochs: int = 0,
        max_iter: int = 8,
        elev_mask_deg: float = 10.0,
        systems: Iterable[str] = ("G",),
        error_thresh_m: float = 0.01,
        residual_gate_m: Optional[float] = None,
        output_csv: Optional[str | Path] = None,
        progress: Optional[Callable[[int, int, PositionSolution], None]] = None,
    ) -> SystemRunResult:
        obs_header, solutions, errors, stats = run_continuous_pipeline(
            str(obs_path),
            str(nav_path),
            step=step,
            max_epochs=max_epochs,
            max_iter=max_iter,
            elev_mask_deg=elev_mask_deg,
            systems=systems,
            error_thresh_m=error_thresh_m,
            residual_gate_m=residual_gate_m,
            progress=progress,
        )
        if output_csv is not None:
            write_csv(str(output_csv), solutions, errors)
        return SystemRunResult(obs_header=obs_header, solutions=solutions, errors=errors, stats=stats)


__all__ = [
    "ContinuousAnalysisModule",
    "RinexDataModule",
    "RinexDataset",
    "SatelliteCorrectionModule",
    "SatelliteMeasurement",
    "SinglePointPositioningModule",
    "SoftwareSystemModule",
    "SystemRunResult",
]
