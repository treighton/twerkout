from twerkout.models import ProgramWeek, StrengthRow, Zone2Row, RecoveryRow, Config
from twerkout.rollups import (
    enrich_strength, enrich_zone2, weekly_zone2_volume, enrich_recovery, enrich_ruck,
    build_view,
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


def test_enrich_ruck_picks_up_both_planned_fields():
    from twerkout.models import RuckRow
    from twerkout.rollups import enrich_ruck
    # program week 1: ruck_planned_min=30, ruck_planned_weight=20
    rows = [RuckRow(date="2026-06-02", pack_weight=25, duration_min=45)]
    out = enrich_ruck(rows, PROGRAM, START)
    assert out[0]["planned_min"] == 30
    assert out[0]["planned_weight"] == 20
    assert out[0]["load"] == 25 * 45
    assert out[0]["planned_met"] == "Yes"   # weight 25>=20 and duration 45>=30

    # weight under target -> "No" even though duration is met
    rows2 = [RuckRow(date="2026-06-02", pack_weight=15, duration_min=45)]
    out2 = enrich_ruck(rows2, PROGRAM, START)
    assert out2[0]["planned_met"] == "No"


def test_build_view_assembles_all_sections():
    cfg = Config(program_start="2026-06-01")
    view = build_view(
        config=cfg, program=PROGRAM,
        strength=[StrengthRow(date="2026-06-02", workout="A", squat=225, reps=5)],
        zone2=[Zone2Row(date="2026-06-02", activity="Rower", duration_min=35)],
        ruck=[], hill=[],
        recovery=[RecoveryRow(week=1, avg_sleep=8, energy=10, fatigue=2, soreness=2)],
    )
    assert "summary" in view
    assert view["summary"]["current_week"] >= 1
    assert len(view["strength"]) == 1
    assert view["zone2"][0]["planned_met"] == "Yes"
    assert "e1rm_series" in view  # chart data
    assert "zone2_volume" in view
    assert view["summary"]["latest_recovery_status"] in {"On Track", "Caution", "Back Off", ""}


def test_summary_latest_e1rm_is_by_date_not_position():
    cfg = Config(program_start="2026-06-01")
    # rows deliberately out of chronological order
    view = build_view(
        config=cfg, program=PROGRAM,
        strength=[
            StrengthRow(date="2026-06-09", workout="A", squat=250, reps=5),  # later
            StrengthRow(date="2026-06-02", workout="A", squat=225, reps=5),  # earlier
        ],
        zone2=[], ruck=[], hill=[],
        recovery=[
            RecoveryRow(week=2, avg_sleep=5, energy=4, fatigue=8, soreness=8),  # later, low
            RecoveryRow(week=1, avg_sleep=8, energy=10, fatigue=2, soreness=2), # earlier, good
        ],
    )
    # latest e1rm squat must come from the 2026-06-09 row (squat=250), not list order
    assert view["summary"]["latest_e1rm"]["squat"] == round(250 * (1 + 5 / 30), 1)
    # latest recovery status must come from week 2 (the low-recovery week)
    assert view["summary"]["latest_recovery_status"] != ""


def test_summary_current_week_from_zone2_only():
    cfg = Config(program_start="2026-06-01")
    # no strength, a zone2 row in week 2 (2026-06-08 -> week 2)
    view = build_view(
        config=cfg, program=PROGRAM,
        strength=[], zone2=[Zone2Row(date="2026-06-08", activity="Rower", duration_min=30)],
        ruck=[], hill=[], recovery=[],
    )
    assert view["summary"]["current_week"] == 2
    assert view["summary"]["latest_recovery_status"] == ""   # empty recovery -> ""
