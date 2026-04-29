from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from models import ObsEpoch, ObsHeader
from utils import rinex_float, rinex_int


def _parse_time_fields(year: int, month: int, day: int, hour: int, minute: int, second: float) -> datetime:
    if year < 80:
        year += 2000
    else:
        year += 1900
    sec_int = int(second)
    micro = int(round((second - sec_int) * 1_000_000))
    return datetime(year, month, day, hour, minute, sec_int, micro)


def _parse_obs_values(
    lines: List[str],
    start_index: int,
    obs_types: List[str],
    offset: int = 0,
) -> Tuple[Dict[str, Optional[float]], int]:
    values: Dict[str, Optional[float]] = {}
    chunks: List[str] = []
    idx = start_index
    while len(chunks) < len(obs_types):
        line = lines[idx]
        start = offset if idx == start_index else 0
        for pos in range(start, 80, 16):
            if len(chunks) >= len(obs_types):
                break
            chunks.append(line[pos : pos + 16])
        idx += 1

    for obs_type, chunk in zip(obs_types, chunks):
        values[obs_type] = rinex_float(chunk[:14])

    return values, idx - start_index


def parse_rinex_obs(path: str | Path) -> Tuple[ObsHeader, List[ObsEpoch]]:
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    version = 0.0
    marker_name = ""
    approx_position_xyz: Optional[tuple[float, float, float]] = None
    obs_types: List[str] = []
    obs_types_by_sys: Optional[Dict[str, List[str]]] = None
    time_first_obs: Optional[datetime] = None
    leap_seconds: Optional[int] = None
    time_system: Optional[str] = None

    while i < len(lines):
        line = lines[i]
        label = line[60:80].strip()
        if label == "RINEX VERSION / TYPE":
            version = float(line[0:9].strip())
        elif label == "MARKER NAME":
            marker_name = line[0:60].strip()
        elif label == "APPROX POSITION XYZ":
            x = rinex_float(line[0:14])
            y = rinex_float(line[14:28])
            z = rinex_float(line[28:42])
            if x is not None and y is not None and z is not None:
                approx_position_xyz = (x, y, z)
        elif label == "# / TYPES OF OBSERV":
            count = rinex_int(line[0:6]) or 0
            obs_types.extend(line[6:60].split())
            while len(obs_types) < count:
                i += 1
                line = lines[i]
                obs_types.extend(line[6:60].split())
        elif label == "SYS / # / OBS TYPES":
            system = line[0:1]
            if obs_types_by_sys is None:
                obs_types_by_sys = {}
            count = rinex_int(line[3:6]) or 0
            types = line[6:60].split()
            while len(types) < count:
                i += 1
                line = lines[i]
                types.extend(line[6:60].split())
            obs_types_by_sys[system] = types
        elif label == "TIME OF FIRST OBS":
            year = int(line[0:6])
            month = int(line[6:12])
            day = int(line[12:18])
            hour = int(line[18:24])
            minute = int(line[24:30])
            second = float(line[30:43])
            time_first_obs = _parse_time_fields(year, month, day, hour, minute, second)
        elif label == "TIME SYSTEM ID":
            time_system = line[0:3].strip()
        elif label == "LEAP SECONDS":
            leap_seconds = rinex_int(line[0:6])
        elif label == "END OF HEADER":
            i += 1
            break
        i += 1

    header = ObsHeader(
        version=version,
        marker_name=marker_name,
        approx_position_xyz=approx_position_xyz,
        obs_types=obs_types,
        obs_types_by_sys=obs_types_by_sys,
        time_first_obs=time_first_obs,
        leap_seconds=leap_seconds,
        time_system=time_system,
    )

    epochs: List[ObsEpoch] = []
    if version >= 3.0:
        obs_types_by_sys = obs_types_by_sys or {}
        while i < len(lines):
            line = lines[i]
            if not line.startswith(">"):
                i += 1
                continue
            tokens = line[1:].split()
            if len(tokens) < 7:
                i += 1
                continue

            year = int(tokens[0])
            month = int(tokens[1])
            day = int(tokens[2])
            hour = int(tokens[3])
            minute = int(tokens[4])
            second = float(tokens[5])
            flag = int(tokens[6])
            nsv = int(tokens[7]) if len(tokens) > 7 else 0
            time = datetime(year, month, day, hour, minute, int(second), int(round((second % 1) * 1_000_000)))

            i += 1
            sat_obs: Dict[str, Dict[str, Optional[float]]] = {}
            for _ in range(nsv):
                if i >= len(lines):
                    break
                sat_line = lines[i]
                sat = sat_line[0:3].strip()
                obs_types = obs_types_by_sys.get(sat[0], [])
                obs_values, consumed = _parse_obs_values(lines, i, obs_types, offset=3)
                sat_obs[sat] = obs_values
                i += consumed

            epochs.append(ObsEpoch(time=time, flag=flag, sat_obs=sat_obs))
        return header, epochs

    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        epoch_fields = line[0:32].split()
        if len(epoch_fields) < 6:
            i += 1
            continue

        year = int(epoch_fields[0])
        month = int(epoch_fields[1])
        day = int(epoch_fields[2])
        hour = int(epoch_fields[3])
        minute = int(epoch_fields[4])
        second = float(epoch_fields[5])
        flag = int(epoch_fields[6]) if len(epoch_fields) > 6 else 0
        nsv = int(epoch_fields[7]) if len(epoch_fields) > 7 else 0
        time = _parse_time_fields(year, month, day, hour, minute, second)

        sats: List[str] = []
        sat_chunk = line[32:68]
        for pos in range(0, len(sat_chunk), 3):
            sat = sat_chunk[pos : pos + 3].strip()
            if sat:
                sats.append(sat)
        i += 1
        while len(sats) < nsv:
            cont_line = lines[i]
            sat_chunk = cont_line[32:68]
            for pos in range(0, len(sat_chunk), 3):
                sat = sat_chunk[pos : pos + 3].strip()
                if sat:
                    sats.append(sat)
            i += 1

        sat_obs: Dict[str, Dict[str, Optional[float]]] = {}
        for sat in sats:
            obs_values, consumed = _parse_obs_values(lines, i, obs_types)
            sat_obs[sat] = obs_values
            i += consumed

        epochs.append(ObsEpoch(time=time, flag=flag, sat_obs=sat_obs))

    return header, epochs
