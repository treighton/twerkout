from twerkout.models import ProgramWeek, StrengthRow, Zone2Row, RecoveryRow
from twerkout.rollups import (
    enrich_strength, enrich_zone2, weekly_zone2_volume, enrich_recovery,
)

PROGRAM = [
    ProgramWeek(1, 30, 30, 20, 4, "Start easy"),
    ProgramWeek(2, 30, 30, 20, 5, ""),
]
START = "2026-06-01"


def test_enrich_strength_adds_week_and_e1rm():
    rows = [StrengthRow(date="2026-06-02", workout="A", squat=225, reps=5)]
    out = enrich_strength(rows, START)
    assert out[0]["week"] == 1
    assert round(out[0]["e1rm_squat"], 1) == round(225 * (1 + 5 / 30), 1)
    # blank lifts have None e1rm
    assert out[0]["e1rm_press"] is None


def test_enrich_zone2_adds_planned_met():
    rows = [Zone2Row(date="2026-06-02", activity="Rower", duration_min=35)]
    out = enrich_zone2(rows, PROGRAM, START)
    assert out[0]["week"] == 1
    assert out[0]["planned_min"] == 30           # looked up from program
    assert out[0]["planned_met"] == "Yes"


def test_enrich_zone2_unknown_week_blank_planned_met():
    # date maps to week 99, no program row -> planned_met blank
    rows = [Zone2Row(date="2027-06-02", activity="Rower", duration_min=35)]
    out = enrich_zone2(rows, PROGRAM, START)
    assert out[0]["planned_met"] == ""
    assert out[0]["planned_min"] is None


def test_weekly_zone2_volume_sums_by_week():
    rows = [
        Zone2Row(date="2026-06-02", activity="Rower", duration_min=20),
        Zone2Row(date="2026-06-03", activity="Bike", duration_min=15),
        Zone2Row(date="2026-06-09", activity="Rower", duration_min=40),
    ]
    enriched = enrich_zone2(rows, PROGRAM, START)
    vol = weekly_zone2_volume(enriched, PROGRAM)
    # week 1 actual = 35 (20+15), planned = 30 ; week 2 actual = 40, planned 30
    assert vol[1] == {"actual": 35, "planned": 30}
    assert vol[2] == {"actual": 40, "planned": 30}


def test_enrich_recovery_adds_score_and_status():
    rows = [RecoveryRow(week=1, avg_sleep=8, energy=10, fatigue=2, soreness=2)]
    out = enrich_recovery(rows)
    assert out[0]["score"] is not None
    assert out[0]["status"] in {"On Track", "Caution", "Back Off"}
