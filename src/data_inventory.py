from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

from rinex_obs import parse_rinex_obs


def _dataset_id(path: Path) -> str:
    name = path.name
    name = re.sub(r"^\d+[_-]+", "", name)
    name = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", name)
    name = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_").lower()
    return name


def _receiver_name(path: Path, dataset_name: str) -> str:
    stem = path.name
    if stem.endswith(".obs"):
        stem = stem[:-4]
    plain_dataset_name = re.sub(r"^\d+[_-]+", "", dataset_name)
    prefixes = [f"{dataset_name}.", f"{plain_dataset_name}."]
    for prefix in prefixes:
        if stem.startswith(prefix):
            stem = stem[len(prefix) :]
            break
    if stem.startswith("UrbanNav-") and "." in stem:
        stem = stem.split(".", 1)[1]
    return stem


def _navigation_files(root: Path) -> List[Path]:
    candidates: List[Path] = []
    search_dirs = [root, root / "rinex", root / "raw"]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for path in search_dir.iterdir():
            if not path.is_file():
                continue
            lower = path.name.lower()
            if lower.endswith(".obs") or lower.endswith(".nmea"):
                continue
            if lower.endswith((".nav", ".rnx", ".n", ".gz")):
                candidates.append(path)
    return sorted(set(candidates))


def _observation_files(root: Path) -> List[Path]:
    candidates: List[Path] = []
    for search_dir in (root, root / "rinex"):
        if not search_dir.exists():
            continue
        for path in search_dir.glob("*.obs"):
            if path.is_file():
                candidates.append(path)
    return sorted(set(candidates))


def _matching_nmea_path(obs_path: Path, dataset_root: Path) -> Path | None:
    names = [obs_path.with_suffix(".nmea").name]
    search_dirs = [obs_path.parent, dataset_root, dataset_root / "nmea"]
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for name in names:
            candidate = search_dir / name
            if candidate.exists():
                return candidate
    return None


def summarize_observation_file(
    path: str | Path,
    dataset_name: str | None = None,
    dataset_root: str | Path | None = None,
) -> Dict[str, Any]:
    obs_path = Path(path)
    root_path = Path(dataset_root) if dataset_root is not None else obs_path.parent
    header, epochs = parse_rinex_obs(obs_path)
    systems = sorted({sat[0] for epoch in epochs for sat in epoch.sat_obs if sat})
    bds_sats = sorted({sat for epoch in epochs for sat in epoch.sat_obs if sat.startswith("C")})
    nmea_path = _matching_nmea_path(obs_path, root_path)
    return {
        "file": str(obs_path),
        "receiver": _receiver_name(obs_path, dataset_name or obs_path.parent.name),
        "version": header.version,
        "marker": header.marker_name,
        "epochs": len(epochs),
        "systems": ",".join(systems),
        "bds_epochs": sum(1 for epoch in epochs if any(sat.startswith("C") for sat in epoch.sat_obs)),
        "bds_satellites": ",".join(bds_sats),
        "approx_position_xyz": header.approx_position_xyz,
        "has_nmea": nmea_path is not None,
        "nmea_path": str(nmea_path) if nmea_path is not None else "",
        "time_first_obs": header.time_first_obs.isoformat() if header.time_first_obs else "",
        "time_system": header.time_system or "",
    }


def summarize_dataset_directory(root: str | Path) -> Dict[str, Any]:
    dataset_root = Path(root)
    dataset_name = dataset_root.name
    nav_files = _navigation_files(dataset_root)
    observations = [
        summarize_observation_file(path, dataset_name=dataset_name, dataset_root=dataset_root)
        for path in _observation_files(dataset_root)
    ]
    return {
        "dataset_id": _dataset_id(dataset_root),
        "source_dir": str(dataset_root),
        "observations": observations,
        "navigation_files": [str(path) for path in nav_files],
        "has_navigation": bool(nav_files),
    }


def write_summary_json(path: str | Path, summary: Dict[str, Any]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
