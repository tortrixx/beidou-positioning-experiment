from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple


@dataclass
class ObsHeader:
    version: float
    marker_name: str
    approx_position_xyz: Optional[tuple[float, float, float]]
    obs_types: List[str]
    obs_types_by_sys: Optional[Dict[str, List[str]]]
    time_first_obs: Optional[datetime]
    leap_seconds: Optional[int]
    time_system: Optional[str]


@dataclass
class ObsEpoch:
    time: datetime
    flag: int
    sat_obs: Dict[str, Dict[str, Optional[float]]]


@dataclass
class NavRecord:
    prn: str
    epoch: datetime
    af0: float
    af1: float
    af2: float
    iode: float
    crs: float
    delta_n: float
    m0: float
    cuc: float
    e: float
    cus: float
    sqrt_a: float
    toe: float
    cic: float
    omega0: float
    cis: float
    i0: float
    crc: float
    omega: float
    omega_dot: float
    idot: float
    codes_l2: float
    gps_week: float
    l2p_flag: float
    sv_accuracy: float
    sv_health: float
    tgd: float
    iodc: float
    transmission_time: float
    fit_interval: float


@dataclass
class NavHeader:
    ion_alpha: Optional[Tuple[float, float, float, float]]
    ion_beta: Optional[Tuple[float, float, float, float]]
    leap_seconds: Optional[int]


@dataclass
class PositionSolution:
    time: datetime
    position_ecef: Tuple[float, float, float]
    clock_bias_m: float
    position_blh: Tuple[float, float, float]
    used_sats: List[str]
    pdop: Optional[float]
    gdop: Optional[float]
