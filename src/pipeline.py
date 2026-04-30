from __future__ import annotations

from pathlib import Path
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
    residual_gate_m: Optional[float] = None,
    progress: Optional[Callable[[int, int, PositionSolution], None]] = None,
) -> Tuple[ObsHeader, List[PositionSolution], List[Dict[str, float]], Dict[str, float]]:
    if step < 1:
        raise ValueError("step 步长必须 >= 1")
    if max_epochs < 0:
        raise ValueError("max_epochs 最大历元数必须 >= 0")
    if max_iter < 1:
        raise ValueError("max_iter 最大迭代次数必须 >= 1")

    obs_file = Path(obs_path)
    nav_file = Path(nav_path)
    if not obs_file.exists():
        raise FileNotFoundError(f"观测文件不存在：{obs_file}")
    if not nav_file.exists():
        raise FileNotFoundError(f"导航文件不存在：{nav_file}")

    obs_header, epochs = parse_rinex_obs(obs_path)
    nav_header, nav_records = parse_rinex_nav(nav_path)

    if obs_header.approx_position_xyz is None:
        raise ValueError("观测文件头缺少接收机近似坐标")

    solutions: List[PositionSolution] = []
    init_xyz = obs_header.approx_position_xyz
    processed_count = 0
    skipped_count = 0
    skip_reasons: Dict[str, int] = {}

    for idx, epoch in enumerate(epochs):
        if idx % step != 0:
            continue
        if max_epochs and processed_count >= max_epochs:
            break
        processed_count += 1
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
                residual_gate_m=residual_gate_m,
                time_system=obs_header.time_system,
            )
        except ValueError as exc:
            skipped_count += 1
            reason = str(exc) or exc.__class__.__name__
            skip_reasons[reason] = skip_reasons.get(reason, 0) + 1
            continue
        solutions.append(sol)
        if progress is not None:
            progress(idx, len(solutions), sol)
        init_xyz = sol.position_ecef

    errors = compute_errors(solutions, obs_header.approx_position_xyz) if solutions else []
    stats = summarize_errors(errors)
    stats.update(
        {
            "processed_epochs": processed_count,
            "solution_epochs": len(solutions),
            "skipped_epochs": skipped_count,
            "skip_reasons": skip_reasons,
        }
    )
    return obs_header, solutions, errors, stats


def write_csv(path: str, solutions: List[PositionSolution], errors: List[Dict[str, float]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.write(
            "time,x,y,z,lat,lon,h,clock_bias_m,used_sats,pdop,gdop,"
            "residual_rms_m,residual_max_m,east,north,up,horiz,three_d\n"
        )
        for sol, err in zip(solutions, errors):
            residual_rms = "" if sol.residual_rms_m is None else f"{sol.residual_rms_m:.4f}"
            residual_max = "" if sol.residual_max_m is None else f"{sol.residual_max_m:.4f}"
            f.write(
                f"{sol.time.isoformat()},"
                f"{sol.position_ecef[0]:.4f},{sol.position_ecef[1]:.4f},{sol.position_ecef[2]:.4f},"
                f"{sol.position_blh[0]:.8f},{sol.position_blh[1]:.8f},{sol.position_blh[2]:.4f},"
                f"{sol.clock_bias_m:.4f},{len(sol.used_sats)},"
                f"{sol.pdop:.3f},{sol.gdop:.3f},{residual_rms},{residual_max},"
                f"{err['east']:.4f},{err['north']:.4f},{err['up']:.4f},"
                f"{err['horiz']:.4f},{err['three_d']:.4f}\n"
            )
