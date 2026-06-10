"""Typed records for program plan, config, and each log type.

All numeric/optional log fields default to None so blank CSV cells map cleanly
to "no value" (mirrors the spreadsheet's IF(x="","",...) guards downstream).
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    program_start: str  # ISO date string, e.g. "2026-06-01"


@dataclass
class ProgramWeek:
    week: int
    zone2_planned_min: Optional[float]
    ruck_planned_min: Optional[float]
    ruck_planned_weight: Optional[float]
    hill_planned_repeats: Optional[float]
    notes: str = ""


@dataclass
class StrengthRow:
    date: str
    lift: str = ""
    workout: str = ""
    weight: Optional[float] = None
    sets: Optional[float] = None
    reps: Optional[float] = None
    bodyweight: Optional[float] = None
    notes: str = ""


@dataclass
class Zone2Row:
    date: str
    activity: str = ""
    duration_min: Optional[float] = None
    avg_hr: Optional[float] = None
    distance: Optional[float] = None
    resistance: Optional[float] = None
    rpe: Optional[float] = None
    notes: str = ""


@dataclass
class RuckRow:
    date: str
    pack_weight: Optional[float] = None
    duration_min: Optional[float] = None
    distance: Optional[float] = None
    elevation: Optional[float] = None
    terrain: str = ""
    notes: str = ""


@dataclass
class HillRow:
    date: str
    repeats: Optional[float] = None
    hill_len_sec: Optional[float] = None
    rpe: Optional[float] = None
    walk_down: str = ""
    notes: str = ""


@dataclass
class RecoveryRow:
    week: int
    bodyweight: Optional[float] = None
    avg_sleep: Optional[float] = None
    energy: Optional[float] = None
    fatigue: Optional[float] = None
    soreness: Optional[float] = None
    notes: str = ""
