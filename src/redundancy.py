from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

from pipeline import run_continuous_pipeline, write_csv


@dataclass
class RedundancyCase:
    name: str
    obs_path: str | Path
    nav_path: str | Path
    systems: tuple[str, ...] = ("G",)
    max_epochs: int = 10
    step: int = 1
    min_solutions: int = 1
    expect_error: Optional[str] = None
    output_csv: Optional[str | Path] = None


def run_redundancy_cases(cases: Iterable[RedundancyCase]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case in cases:
        rows.append(_run_case(case))
    return rows


def write_redundancy_summary(path: str | Path, rows: list[dict[str, object]]) -> None:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "name",
        "status",
        "systems",
        "solutions",
        "processed_epochs",
        "skipped_epochs",
        "horiz_rms",
        "3d_rms",
        "message",
    ]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _run_case(case: RedundancyCase) -> dict[str, object]:
    try:
        _, solutions, errors, stats = run_continuous_pipeline(
            str(case.obs_path),
            str(case.nav_path),
            step=case.step,
            max_epochs=case.max_epochs,
            systems=case.systems,
        )
        if case.output_csv is not None:
            write_csv(str(case.output_csv), solutions, errors)
        status = "ok" if len(solutions) >= case.min_solutions else "warning"
        message = "ok" if status == "ok" else "valid solutions below threshold"
        return {
            "name": case.name,
            "status": status,
            "systems": ",".join(case.systems),
            "solutions": len(solutions),
            "processed_epochs": stats.get("processed_epochs", 0),
            "skipped_epochs": stats.get("skipped_epochs", 0),
            "horiz_rms": stats.get("horiz_rms", ""),
            "3d_rms": stats.get("3d_rms", ""),
            "message": message,
        }
    except Exception as exc:
        message = str(exc)
        if case.expect_error and case.expect_error in message:
            status = "expected_error"
        else:
            status = "error"
        return {
            "name": case.name,
            "status": status,
            "systems": ",".join(case.systems),
            "solutions": 0,
            "processed_epochs": 0,
            "skipped_epochs": 0,
            "horiz_rms": "",
            "3d_rms": "",
            "message": message,
        }
