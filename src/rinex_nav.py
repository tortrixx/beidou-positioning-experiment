from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

from models import NavHeader, NavRecord
from utils import rinex_float, rinex_int


def _parse_time_fields(year: int, month: int, day: int, hour: int, minute: int, second: float) -> datetime:
    if year < 80:
        year += 2000
    else:
        year += 1900
    sec_int = int(second)
    micro = int(round((second - sec_int) * 1_000_000))
    return datetime(year, month, day, hour, minute, sec_int, micro)


def _parse_four(line: str) -> list[float]:
    return [
        rinex_float(line[3:22]) or 0.0,
        rinex_float(line[22:41]) or 0.0,
        rinex_float(line[41:60]) or 0.0,
        rinex_float(line[60:79]) or 0.0,
    ]


def _parse_header_four(line: str) -> Tuple[float, float, float, float]:
    parts = line[0:60].split()
    values = [(rinex_float(part) or 0.0) for part in parts[:4]]
    while len(values) < 4:
        values.append(0.0)
    return (values[0], values[1], values[2], values[3])


def parse_rinex_nav(path: str | Path) -> Tuple[NavHeader, List[NavRecord]]:
    lines = Path(path).read_text(encoding="utf-8", errors="ignore").splitlines()
    i = 0
    version = 0.0
    ion_alpha: Optional[Tuple[float, float, float, float]] = None
    ion_beta: Optional[Tuple[float, float, float, float]] = None
    leap_seconds: Optional[int] = None
    while i < len(lines):
        label = lines[i][60:80].strip()
        if label == "RINEX VERSION / TYPE":
            version_text = lines[i][0:9].strip()
            if version_text:
                version = float(version_text)
        elif label == "ION ALPHA":
            ion_alpha = _parse_header_four(lines[i])
        elif label == "ION BETA":
            ion_beta = _parse_header_four(lines[i])
        elif label == "LEAP SECONDS":
            leap_seconds = rinex_int(lines[i][0:6])
        elif label == "END OF HEADER":
            i += 1
            break
        i += 1

    header = NavHeader(ion_alpha=ion_alpha, ion_beta=ion_beta, leap_seconds=leap_seconds)

    records: List[NavRecord] = []
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue

        head = line[0:22].split()
        if len(head) < 7:
            i += 1
            continue

        prn_token = head[0]
        if prn_token and prn_token[0].isalpha():
            prn = prn_token
        else:
            prn = f"G{int(prn_token):02d}"

        year_token = int(head[1])
        if year_token >= 1000:
            year = year_token
        else:
            year = year_token + 2000 if year_token < 80 else year_token + 1900
        month = int(head[2])
        day = int(head[3])
        hour = int(head[4])
        minute = int(head[5])
        second = float(head[6])
        epoch = datetime(year, month, day, hour, minute, int(second), int(round((second % 1) * 1_000_000)))

        af0 = rinex_float(line[22:41]) or 0.0
        af1 = rinex_float(line[41:60]) or 0.0
        af2 = rinex_float(line[60:79]) or 0.0

        i += 1
        vals2 = _parse_four(lines[i])
        i += 1
        vals3 = _parse_four(lines[i])
        i += 1
        vals4 = _parse_four(lines[i])
        i += 1
        vals5 = _parse_four(lines[i])
        i += 1
        vals6 = _parse_four(lines[i])
        i += 1
        vals7 = _parse_four(lines[i])
        i += 1
        vals8 = _parse_four(lines[i])
        i += 1

        record = NavRecord(
            prn=prn,
            epoch=epoch,
            af0=af0,
            af1=af1,
            af2=af2,
            iode=vals2[0],
            crs=vals2[1],
            delta_n=vals2[2],
            m0=vals2[3],
            cuc=vals3[0],
            e=vals3[1],
            cus=vals3[2],
            sqrt_a=vals3[3],
            toe=vals4[0],
            cic=vals4[1],
            omega0=vals4[2],
            cis=vals4[3],
            i0=vals5[0],
            crc=vals5[1],
            omega=vals5[2],
            omega_dot=vals5[3],
            idot=vals6[0],
            codes_l2=vals6[1],
            gps_week=vals6[2],
            l2p_flag=vals6[3],
            sv_accuracy=vals7[0],
            sv_health=vals7[1],
            tgd=vals7[2],
            iodc=vals7[3],
            transmission_time=vals8[0],
            fit_interval=vals8[1],
        )
        records.append(record)

    return header, records
