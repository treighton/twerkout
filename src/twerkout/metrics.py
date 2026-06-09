"""Pure metric functions ported 1:1 from the spreadsheet formulas.

All functions return None/"" for blank inputs, mirroring the sheet's
IF(x="","",...) guards. No I/O, no globals — fully unit-testable.
"""
from datetime import date
from typing import Optional


def _parse(d: str) -> date:
    return date.fromisoformat(d)


def week_for_date(row_date: str, program_start: str) -> int:
    """INT((date - start)/7)+1 — day 1..7 = week 1, day 8..14 = week 2, etc.

    Every log row requires a date; a blank or malformed date is a bad row and
    fails loudly with context rather than producing a silently-wrong week.
    """
    try:
        delta = (_parse(row_date) - _parse(program_start)).days
    except ValueError as exc:
        raise ValueError(
            f"invalid date: row_date={row_date!r}, program_start={program_start!r}"
        ) from exc
    return delta // 7 + 1


def e1rm(weight: Optional[float], reps: Optional[float]) -> Optional[float]:
    """Epley estimated 1-rep max: weight * (1 + reps/30)."""
    if weight is None or reps is None:
        return None
    return weight * (1 + reps / 30)


def planned_met_zone2(actual_min: Optional[float], planned_min: Optional[float]) -> str:
    if actual_min is None or planned_min is None:
        return ""
    return "Yes" if actual_min >= planned_min else "No"


def planned_met_ruck(
    pack_weight: Optional[float], planned_weight: Optional[float],
    duration_min: Optional[float], planned_min: Optional[float],
) -> str:
    if None in (pack_weight, planned_weight, duration_min, planned_min):
        return ""
    met = pack_weight >= planned_weight and duration_min >= planned_min
    return "Yes" if met else "No"


def planned_met_hill(actual_repeats: Optional[float], planned_repeats: Optional[float]) -> str:
    if actual_repeats is None or planned_repeats is None:
        return ""
    return "Yes" if actual_repeats >= planned_repeats else "No"


def ruck_load(pack_weight: Optional[float], duration_min: Optional[float]) -> Optional[float]:
    if pack_weight is None or duration_min is None:
        return None
    return pack_weight * duration_min


def recovery_score(
    sleep: Optional[float], energy: Optional[float],
    fatigue: Optional[float], soreness: Optional[float],
) -> Optional[float]:
    if None in (sleep, energy, fatigue, soreness):
        return None
    return (sleep / 8 * 4) + (energy / 10 * 3) - ((fatigue + soreness) / 20 * 3)


def status_for_score(score: Optional[float]) -> str:
    if score is None:
        return ""
    if score < 1.5:
        return "Back Off"
    if score < 2.5:
        return "Caution"
    return "On Track"
