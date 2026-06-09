from twerkout.models import ProgramWeek, StrengthRow


def test_program_week_fields():
    pw = ProgramWeek(
        week=1, zone2_planned_min=30, ruck_planned_min=30,
        ruck_planned_weight=20, hill_planned_repeats=4,
        notes="Start easy",
    )
    assert pw.week == 1
    assert pw.zone2_planned_min == 30


def test_strength_row_optional_fields_default_none():
    row = StrengthRow(date="2026-06-02")
    assert row.date == "2026-06-02"
    assert row.squat is None
    assert row.reps is None
