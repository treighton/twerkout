"""Load hand-edited CSVs into typed records.

Blank cells -> None for numeric fields, "" for text fields. Malformed numbers
raise ValueError with the file + field so CI fails loudly at push time.
"""
import csv
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

from twerkout.models import (
    Config, ProgramWeek, StrengthRow, Zone2Row, RuckRow, HillRow, RecoveryRow,
)


def _num(value: str, *, field: str, source: Path) -> Optional[float]:
    value = (value or "").strip()
    if value == "":
        return None
    try:
        return float(value)
    except ValueError as exc:
        raise ValueError(f"{source.name}: bad number in '{field}': {value!r}") from exc


def _int_required(value: str, *, field: str, source: Path) -> int:
    v = (value or "").strip()
    if not v:
        raise ValueError(f"{source.name}: required integer field '{field}' is blank")
    try:
        return int(v)
    except ValueError as exc:
        raise ValueError(f"{source.name}: bad integer in '{field}': {v!r}") from exc


def _rows(path: Path) -> Iterator[dict[str, str]]:
    with open(path, newline="") as f:
        yield from csv.DictReader(f)


def load_config(path: Path) -> Config:
    values = {r["key"].strip(): r["value"].strip() for r in _rows(path)}
    try:
        start = values["program_start"]
    except KeyError:
        raise ValueError(f"{path.name}: missing required key 'program_start'")
    return Config(program_start=start)


def load_program(path: Path) -> list[ProgramWeek]:
    out = []
    for r in _rows(path):
        out.append(ProgramWeek(
            week=_int_required(r["week"], field="week", source=path),
            zone2_planned_min=_num(r["zone2_planned_min"], field="zone2_planned_min", source=path),
            ruck_planned_min=_num(r["ruck_planned_min"], field="ruck_planned_min", source=path),
            ruck_planned_weight=_num(r["ruck_planned_weight"], field="ruck_planned_weight", source=path),
            hill_planned_repeats=_num(r["hill_planned_repeats"], field="hill_planned_repeats", source=path),
            notes=(r.get("notes") or "").strip(),
        ))
    seen = set()
    for pw in out:
        if pw.week in seen:
            raise ValueError(f"{path.name}: duplicate week {pw.week}")
        seen.add(pw.week)
    return out


def load_strength(path: Path) -> list[StrengthRow]:
    out = []
    for r in _rows(path):
        out.append(StrengthRow(
            date=r["date"].strip(),
            workout=(r.get("workout") or "").strip(),
            bodyweight=_num(r["bodyweight"], field="bodyweight", source=path),
            squat=_num(r["squat"], field="squat", source=path),
            press=_num(r["press"], field="press", source=path),
            bench=_num(r["bench"], field="bench", source=path),
            deadlift=_num(r["deadlift"], field="deadlift", source=path),
            reps=_num(r["reps"], field="reps", source=path),
            notes=(r.get("notes") or "").strip(),
        ))
    return out


def load_zone2(path: Path) -> list[Zone2Row]:
    out = []
    for r in _rows(path):
        out.append(Zone2Row(
            date=r["date"].strip(),
            activity=(r.get("activity") or "").strip(),
            duration_min=_num(r["duration_min"], field="duration_min", source=path),
            avg_hr=_num(r["avg_hr"], field="avg_hr", source=path),
            distance=_num(r["distance"], field="distance", source=path),
            resistance=_num(r["resistance"], field="resistance", source=path),
            rpe=_num(r["rpe"], field="rpe", source=path),
            notes=(r.get("notes") or "").strip(),
        ))
    return out


def load_ruck(path: Path) -> list[RuckRow]:
    out = []
    for r in _rows(path):
        out.append(RuckRow(
            date=r["date"].strip(),
            pack_weight=_num(r["pack_weight"], field="pack_weight", source=path),
            duration_min=_num(r["duration_min"], field="duration_min", source=path),
            distance=_num(r["distance"], field="distance", source=path),
            elevation=_num(r["elevation"], field="elevation", source=path),
            terrain=(r.get("terrain") or "").strip(),
            notes=(r.get("notes") or "").strip(),
        ))
    return out


def load_hill(path: Path) -> list[HillRow]:
    out = []
    for r in _rows(path):
        out.append(HillRow(
            date=r["date"].strip(),
            repeats=_num(r["repeats"], field="repeats", source=path),
            hill_len_sec=_num(r["hill_len_sec"], field="hill_len_sec", source=path),
            rpe=_num(r["rpe"], field="rpe", source=path),
            walk_down=(r.get("walk_down") or "").strip(),
            notes=(r.get("notes") or "").strip(),
        ))
    return out


def load_recovery(path: Path) -> list[RecoveryRow]:
    out = []
    for r in _rows(path):
        out.append(RecoveryRow(
            week=_int_required(r["week"], field="week", source=path),
            bodyweight=_num(r["bodyweight"], field="bodyweight", source=path),
            avg_sleep=_num(r["avg_sleep"], field="avg_sleep", source=path),
            energy=_num(r["energy"], field="energy", source=path),
            fatigue=_num(r["fatigue"], field="fatigue", source=path),
            soreness=_num(r["soreness"], field="soreness", source=path),
            notes=(r.get("notes") or "").strip(),
        ))
    return out
