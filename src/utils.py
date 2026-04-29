from __future__ import annotations

from typing import Optional


def rinex_float(text: str) -> Optional[float]:
    value = text.strip()
    if not value:
        return None
    return float(value.replace("D", "E"))


def rinex_int(text: str) -> Optional[int]:
    value = text.strip()
    if not value:
        return None
    return int(value)
