import pytest
from pathlib import Path

from twerkout.models import ProgramWeek, StrengthRow
from twerkout.data import load_config, load_program, load_strength

FIX = Path(__file__).parent / "fixtures"


def test_program_week_fields():
    pw = ProgramWeek(
        week=1, zone2_planned_min=30, ruck_planned_min=30,
        ruck_planned_weight=20, hill_planned_repeats=4,
        notes="Start easy",
    )
    assert pw.week == 1
    assert pw.zone2_planned_min == 30


def test_strength_row_new_per_lift_shape():
    row = StrengthRow(date="2026-06-09", workout="A", lift="squat",
                      weight=225, sets=3, reps=5, bodyweight=180, notes="ok")
    assert row.lift == "squat"
    assert row.weight == 225
    assert row.sets == 3
    assert row.reps == 5


def test_strength_row_defaults():
    row = StrengthRow(date="2026-06-09", lift="press")
    assert row.weight is None
    assert row.sets is None
    assert row.bodyweight is None
    assert row.workout == ""


def test_load_config_reads_program_start():
    cfg = load_config(FIX / "config.csv")
    assert cfg.program_start == "2026-06-01"


def test_load_program_parses_numbers_and_blank_notes():
    weeks = load_program(FIX / "program.csv")
    assert len(weeks) == 2
    assert weeks[0].week == 1
    assert weeks[0].zone2_planned_min == 30.0
    assert weeks[1].notes == ""


def test_load_strength_per_lift_rows():
    rows = load_strength(FIX / "strength.csv")
    assert len(rows) == 2
    assert rows[0].lift == "squat"
    assert rows[0].weight == 225.0
    assert rows[0].sets == 3.0
    assert rows[0].reps == 5.0
    assert rows[0].bodyweight == 180.0
    # second row: blank bodyweight -> None
    assert rows[1].lift == "press"
    assert rows[1].bodyweight is None


def test_load_strength_lowercases_lift(tmp_path):
    csv_path = tmp_path / "strength.csv"
    csv_path.write_text(
        "date,workout,lift,weight,sets,reps,bodyweight,notes\n"
        "2026-06-09,A,SQUAT,225,3,5,180,\n"
    )
    rows = load_strength(csv_path)
    assert rows[0].lift == "squat"   # lowercased


def test_load_strength_blank_lift_raises(tmp_path):
    csv_path = tmp_path / "strength.csv"
    csv_path.write_text(
        "date,workout,lift,weight,sets,reps,bodyweight,notes\n"
        "2026-06-09,A,,225,3,5,180,\n"
    )
    with pytest.raises(ValueError, match="blank lift"):
        load_strength(csv_path)


def test_load_strength_bad_weight_raises(tmp_path):
    csv_path = tmp_path / "strength.csv"
    csv_path.write_text(
        "date,workout,lift,weight,sets,reps,bodyweight,notes\n"
        "2026-06-09,A,squat,not_a_number,3,5,180,\n"
    )
    with pytest.raises(ValueError, match="weight"):
        load_strength(csv_path)


def test_load_program_rejects_duplicate_weeks(tmp_path):
    csv_path = tmp_path / "program.csv"
    csv_path.write_text(
        "week,zone2_planned_min,ruck_planned_min,ruck_planned_weight,hill_planned_repeats,notes\n"
        "1,30,30,20,4,\n"
        "1,35,40,20,5,\n"
    )
    with pytest.raises(ValueError, match="duplicate week 1"):
        load_program(csv_path)
