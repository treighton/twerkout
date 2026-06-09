"""Enrich raw log rows with derived values and compute weekly aggregates.

Output is plain dicts (JSON-friendly) so render.py can embed them directly.
"""
from twerkout.models import (
    Config, ProgramWeek, StrengthRow, Zone2Row, RuckRow, HillRow, RecoveryRow,
)
from twerkout import metrics


def _program_by_week(program: list[ProgramWeek]) -> dict[int, ProgramWeek]:
    return {p.week: p for p in program}


def enrich_strength(rows: list[StrengthRow], program_start: str) -> list[dict]:
    out = []
    for r in rows:
        week = metrics.week_for_date(r.date, program_start)
        out.append({
            "date": r.date, "week": week, "workout": r.workout,
            "bodyweight": r.bodyweight, "reps": r.reps, "notes": r.notes,
            "squat": r.squat, "press": r.press, "bench": r.bench, "deadlift": r.deadlift,
            "e1rm_squat": metrics.e1rm(r.squat, r.reps),
            "e1rm_press": metrics.e1rm(r.press, r.reps),
            "e1rm_bench": metrics.e1rm(r.bench, r.reps),
            "e1rm_deadlift": metrics.e1rm(r.deadlift, r.reps),
        })
    return out


def enrich_zone2(rows: list[Zone2Row], program: list[ProgramWeek], program_start: str) -> list[dict]:
    by_week = _program_by_week(program)
    out = []
    for r in rows:
        week = metrics.week_for_date(r.date, program_start)
        p = by_week.get(week)
        planned = p.zone2_planned_min if p else None
        # resistance is not surfaced — no planned target or derived metric uses it
        out.append({
            "date": r.date, "week": week, "activity": r.activity,
            "duration_min": r.duration_min, "avg_hr": r.avg_hr,
            "distance": r.distance, "rpe": r.rpe, "notes": r.notes,
            "planned_min": planned,
            "planned_met": metrics.planned_met_zone2(r.duration_min, planned),
        })
    return out


def enrich_ruck(rows: list[RuckRow], program: list[ProgramWeek], program_start: str) -> list[dict]:
    by_week = _program_by_week(program)
    out = []
    for r in rows:
        week = metrics.week_for_date(r.date, program_start)
        p = by_week.get(week)
        planned_min = p.ruck_planned_min if p else None
        planned_wt = p.ruck_planned_weight if p else None
        out.append({
            "date": r.date, "week": week,
            "pack_weight": r.pack_weight, "duration_min": r.duration_min,
            "distance": r.distance, "elevation": r.elevation, "terrain": r.terrain,
            "notes": r.notes,
            "planned_min": planned_min, "planned_weight": planned_wt,
            "load": metrics.ruck_load(r.pack_weight, r.duration_min),
            "planned_met": metrics.planned_met_ruck(
                r.pack_weight, planned_wt, r.duration_min, planned_min),
        })
    return out


def enrich_hill(rows: list[HillRow], program: list[ProgramWeek], program_start: str) -> list[dict]:
    by_week = _program_by_week(program)
    out = []
    for r in rows:
        week = metrics.week_for_date(r.date, program_start)
        p = by_week.get(week)
        planned = p.hill_planned_repeats if p else None
        out.append({
            "date": r.date, "week": week, "repeats": r.repeats,
            "hill_len_sec": r.hill_len_sec, "rpe": r.rpe,
            "walk_down": r.walk_down, "notes": r.notes,
            "planned_repeats": planned,
            "planned_met": metrics.planned_met_hill(r.repeats, planned),
        })
    return out


def enrich_recovery(rows: list[RecoveryRow]) -> list[dict]:
    out = []
    for r in rows:
        score = metrics.recovery_score(r.avg_sleep, r.energy, r.fatigue, r.soreness)
        out.append({
            "week": r.week, "bodyweight": r.bodyweight, "avg_sleep": r.avg_sleep,
            "energy": r.energy, "fatigue": r.fatigue, "soreness": r.soreness,
            "notes": r.notes,
            "score": score, "status": metrics.status_for_score(score),
        })
    return out


def _weekly_actual_vs_planned(
    enriched: list[dict], actual_key: str,
    program: list[ProgramWeek], planned_attr: str,
) -> dict[int, dict]:
    by_week = _program_by_week(program)
    totals: dict[int, float] = {}
    for row in enriched:
        v = row.get(actual_key)
        if v is not None:
            totals[row["week"]] = totals.get(row["week"], 0) + v
    result = {}
    for week, actual in sorted(totals.items()):
        p = by_week.get(week)
        result[week] = {"actual": actual, "planned": getattr(p, planned_attr) if p else None}
    return result


def weekly_zone2_volume(enriched: list[dict], program: list[ProgramWeek]) -> dict[int, dict]:
    return _weekly_actual_vs_planned(enriched, "duration_min", program, "zone2_planned_min")


def weekly_ruck_volume(enriched: list[dict], program: list[ProgramWeek]) -> dict[int, dict]:
    return _weekly_actual_vs_planned(enriched, "duration_min", program, "ruck_planned_min")


def weekly_hill_volume(enriched: list[dict], program: list[ProgramWeek]) -> dict[int, dict]:
    return _weekly_actual_vs_planned(enriched, "repeats", program, "hill_planned_repeats")


def _e1rm_series(strength: list[dict]) -> dict[str, list]:
    """Per-lift [ {date, value}, ... ] for the e1RM-over-time line chart."""
    lifts = ("squat", "press", "bench", "deadlift")
    series = {lift: [] for lift in lifts}
    for row in strength:
        for lift in lifts:
            v = row.get(f"e1rm_{lift}")
            if v is not None:
                series[lift].append({"date": row["date"], "value": round(v, 1)})
    return series


def _summary(strength: list[dict], zone2: list[dict], recovery: list[dict]) -> dict:
    # "latest" is by date/week, not input position, so out-of-order hand-edited
    # CSV rows still produce the correct most-recent values.
    strength_by_date = sorted(strength, key=lambda r: r["date"])
    current_week = max(
        [r["week"] for r in strength] + [r["week"] for r in zone2] + [1]
    )
    total_zone2 = sum(r["duration_min"] for r in zone2 if r["duration_min"] is not None)
    latest_e1rm = {}
    for lift in ("squat", "press", "bench", "deadlift"):
        vals = [r[f"e1rm_{lift}"] for r in strength_by_date if r.get(f"e1rm_{lift}") is not None]
        latest_e1rm[lift] = round(vals[-1], 1) if vals else None
    latest_status = ""
    if recovery:
        latest_status = max(recovery, key=lambda r: r["week"])["status"]
    return {
        "current_week": current_week,
        "total_zone2_min": total_zone2,
        "latest_e1rm": latest_e1rm,
        "latest_recovery_status": latest_status,
    }


def build_view(
    config: Config, program: list[ProgramWeek],
    strength: list[StrengthRow], zone2: list[Zone2Row],
    ruck: list[RuckRow], hill: list[HillRow], recovery: list[RecoveryRow],
) -> dict:
    start = config.program_start
    s = enrich_strength(strength, start)
    z = enrich_zone2(zone2, program, start)
    rk = enrich_ruck(ruck, program, start)
    h = enrich_hill(hill, program, start)
    rec = enrich_recovery(recovery)
    return {
        "program": [vars(p) for p in program],
        "strength": s, "zone2": z, "ruck": rk, "hill": h, "recovery": rec,
        "summary": _summary(s, z, rec),
        "e1rm_series": _e1rm_series(s),
        "zone2_volume": weekly_zone2_volume(z, program),
        "ruck_volume": weekly_ruck_volume(rk, program),
        "hill_volume": weekly_hill_volume(h, program),
    }
