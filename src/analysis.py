from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

from coords import ecef_to_geodetic, enu_from_ecef
from models import PositionSolution


def compute_errors(
    solutions: Iterable[PositionSolution],
    ref_xyz: Tuple[float, float, float],
) -> List[Dict[str, float]]:
    lat_ref, lon_ref, _ = ecef_to_geodetic(*ref_xyz)
    results: List[Dict[str, float]] = []

    for sol in solutions:
        dx = sol.position_ecef[0] - ref_xyz[0]
        dy = sol.position_ecef[1] - ref_xyz[1]
        dz = sol.position_ecef[2] - ref_xyz[2]
        east, north, up = enu_from_ecef(dx, dy, dz, lat_ref, lon_ref)
        horiz = math.hypot(east, north)
        three_d = math.sqrt(east * east + north * north + up * up)

        results.append(
            {
                "east": east,
                "north": north,
                "up": up,
                "horiz": horiz,
                "three_d": three_d,
            }
        )

    return results


def _rms(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return float("nan")
    return math.sqrt(sum(v * v for v in vals) / len(vals))


def _mean(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return float("nan")
    return sum(vals) / len(vals)


def _max(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return float("nan")
    return max(vals)


def summarize_errors(errors: List[Dict[str, float]]) -> Dict[str, float]:
    horiz = [row["horiz"] for row in errors]
    three_d = [row["three_d"] for row in errors]
    return {
        "horiz_rms": _rms(horiz),
        "horiz_mean": _mean(horiz),
        "horiz_max": _max(horiz),
        "3d_rms": _rms(three_d),
        "3d_mean": _mean(three_d),
        "3d_max": _max(three_d),
    }
