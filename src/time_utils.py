from __future__ import annotations

from datetime import datetime

GPS_EPOCH = datetime(1980, 1, 6, 0, 0, 0)
BDT_EPOCH = datetime(2006, 1, 1, 0, 0, 0)
SECONDS_IN_WEEK = 604800.0
HALF_WEEK = SECONDS_IN_WEEK / 2.0


def gps_seconds(dt: datetime) -> float:
    delta = dt - GPS_EPOCH
    return delta.total_seconds()


def gps_week_seconds(dt: datetime) -> tuple[int, float]:
    total = gps_seconds(dt)
    week = int(total // SECONDS_IN_WEEK)
    sow = total - week * SECONDS_IN_WEEK
    return week, sow


def gnss_week_seconds(system: str, dt: datetime) -> tuple[int, float]:
    epoch = BDT_EPOCH if system == "C" else GPS_EPOCH
    total = (dt - epoch).total_seconds()
    week = int(total // SECONDS_IN_WEEK)
    sow = total - week * SECONDS_IN_WEEK
    return week, sow


def adjust_week(tk: float) -> float:
    if tk > HALF_WEEK:
        tk -= SECONDS_IN_WEEK
    elif tk < -HALF_WEEK:
        tk += SECONDS_IN_WEEK
    return tk
