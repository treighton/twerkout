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
            "lift": r.lift, "weight": r.weight, "sets": r.sets, "reps": r.reps,
            "bodyweight": r.bodyweight, "notes": r.notes,
            "e1rm": metrics.e1rm(r.weight, r.reps),
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
    """Per-lift [ {date, value}, ... ] for the e1RM-over-time line chart.

    Lifts are discovered from the data (the `lift` field) rather than a fixed
    column set, and points are emitted in date order.
    """
    series: dict[str, list] = {}
    for row in sorted(strength, key=lambda r: r["date"]):
        if row.get("e1rm") is None:
            continue
        series.setdefault(row["lift"], []).append(
            {"date": row["date"], "value": round(row["e1rm"], 1)}
        )
    return series


def _summary(strength: list[dict], zone2: list[dict], recovery: list[dict]) -> dict:
    # "latest" is by date/week, not input position, so out-of-order hand-edited
    # CSV rows still produce the correct most-recent values.
    strength_by_date = sorted(strength, key=lambda r: r["date"])
    current_week = max(
        [r["week"] for r in strength] + [r["week"] for r in zone2] + [1]
    )
    total_zone2 = sum(r["duration_min"] for r in zone2 if r["duration_min"] is not None)
    latest_e1rm: dict[str, float] = {}
    for r in strength_by_date:  # already sorted by date ascending; last per lift wins
        if r.get("e1rm") is not None:
            latest_e1rm[r["lift"]] = round(r["e1rm"], 1)
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
