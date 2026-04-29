from __future__ import annotations

from typing import Callable, Dict, Iterable, List, Optional, Tuple

from analysis import compute_errors, summarize_errors
from models import ObsHeader, PositionSolution
from positioning import single_point_position
from rinex_nav import parse_rinex_nav
from rinex_obs import parse_rinex_obs


def run_continuous_pipeline(
    obs_path: str,
    nav_path: str,
    step: int = 1,
    max_epochs: int = 0,
    max_iter: int = 8,
    elev_mask_deg: float = 10.0,
    systems: Iterable[str] = ("G",),
    error_thresh_m: float = 0.01,
    progress: Optional[Callable[[int, int, PositionSolution], None]] = None,
) -> Tuple[ObsHeader, List[PositionSolution], List[Dict[str, float]], Dict[str, float]]:
    obs_header, epochs = parse_rinex_obs(obs_path)
    nav_header, nav_records = parse_rinex_nav(nav_path)

    if obs_header.approx_position_xyz is None:
        raise ValueError("Missing approximate receiver position in obs header")

    solutions: List[PositionSolution] = []
    init_xyz = obs_header.approx_position_xyz
    count = 0

    for idx, epoch in enumerate(epochs):
        if idx % step != 0:
            continue
        if max_epochs and count >= max_epochs:
            break
        try:
            sol = single_point_position(
                epoch,
                nav_header,
                nav_records,
                init_xyz,
                max_iter=max_iter,
                elev_mask_deg=elev_mask_deg,
                systems=tuple(systems),
                error_thresh_m=error_thresh_m,
                time_system=obs_header.time_system,
            )
        except ValueError:
            continue
        solutions.append(sol)
        if progress is not None:
            progress(idx, count + 1, sol)
        init_xyz = sol.position_ecef
        count += 1

    if not solutions:
        raise ValueError("No valid solutions")

    errors = compute_errors(solutions, obs_header.approx_position_xyz)
    stats = summarize_errors(errors)
    return obs_header, solutions, errors, stats


def write_csv(path: str, solutions: List[PositionSolution], errors: List[Dict[str, float]]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write(
            "time,x,y,z,lat,lon,h,clock_bias_m,used_sats,pdop,gdop,east,north,up,horiz,three_d\n"
        )
        for sol, err in zip(solutions, errors):
            f.write(
                f"{sol.time.isoformat()},"
                f"{sol.position_ecef[0]:.4f},{sol.position_ecef[1]:.4f},{sol.position_ecef[2]:.4f},"
                f"{sol.position_blh[0]:.8f},{sol.position_blh[1]:.8f},{sol.position_blh[2]:.4f},"
                f"{sol.clock_bias_m:.4f},{len(sol.used_sats)},"
                f"{sol.pdop:.3f},{sol.gdop:.3f},"
                f"{err['east']:.4f},{err['north']:.4f},{err['up']:.4f},"
                f"{err['horiz']:.4f},{err['three_d']:.4f}\n"
            )
