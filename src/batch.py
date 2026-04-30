from __future__ import annotations

import csv
import math
from pathlib import Path
from typing import Dict, Iterable, List


def _rms(values: Iterable[float]) -> float:
    vals = list(values)
    if not vals:
        return float("nan")
    return math.sqrt(sum(value * value for value in vals) / len(vals))


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


def _column(rows: List[Dict[str, str]], name: str) -> List[float]:
    return [float(row[name]) for row in rows if row.get(name) not in (None, "")]


def summarize_result_csv(dataset: str, system: str, csv_path: str | Path) -> Dict[str, float | int | str]:
    path = Path(csv_path)
    with path.open("r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    horiz = _column(rows, "horiz")
    three_d = _column(rows, "three_d")
    used_sats = _column(rows, "used_sats")
    pdop = _column(rows, "pdop")
    residual = _column(rows, "residual_rms_m")

    return {
        "dataset": dataset,
        "system": system,
        "path": str(path),
        "epochs": len(rows),
        "horiz_rms": _rms(horiz),
        "horiz_mean": _mean(horiz),
        "horiz_max": _max(horiz),
        "3d_rms": _rms(three_d),
        "3d_mean": _mean(three_d),
        "3d_max": _max(three_d),
        "used_sats_mean": _mean(used_sats),
        "used_sats_min": min(used_sats) if used_sats else float("nan"),
        "used_sats_max": max(used_sats) if used_sats else float("nan"),
        "pdop_mean": _mean(pdop),
        "pdop_max": _max(pdop),
        "residual_rms_mean": _mean(residual),
        "residual_rms_max": _max(residual),
    }


def write_summary(path: str | Path, summaries: List[Dict[str, float | int | str]]) -> None:
    if not summaries:
        raise ValueError("没有可写入的汇总结果")
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(summaries[0].keys())
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(summaries)
