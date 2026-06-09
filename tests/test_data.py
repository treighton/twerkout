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


def test_strength_row_optional_fields_default_none():
    row = StrengthRow(date="2026-06-02")
    assert row.date == "2026-06-02"
    assert row.squat is None
    assert row.reps is None


def test_load_config_reads_program_start():
    cfg = load_config(FIX / "config.csv")
    assert cfg.program_start == "2026-06-01"


def test_load_program_parses_numbers_and_blank_notes():
    weeks = load_program(FIX / "program.csv")
    assert len(weeks) == 2
    assert weeks[0].week == 1
    assert weeks[0].zone2_planned_min == 30.0
    assert weeks[1].notes == ""


def test_load_strength_blanks_become_none():
    rows = load_strength(FIX / "strength.csv")
    assert rows[0].squat == 225.0
    assert rows[0].bodyweight == 180.0
    assert rows[1].bodyweight is None   # blank cell
    assert rows[1].press is None        # blank cell
    assert rows[1].squat == 225.0


def test_load_strength_bad_number_raises_with_context(tmp_path):
    csv_path = tmp_path / "strength.csv"
    csv_path.write_text(
        "date,workout,bodyweight,squat,press,bench,deadlift,reps,notes\n"
        "2026-06-02,A,not_a_number,225,95,185,275,5,\n"
    )
    with pytest.raises(ValueError, match="bodyweight"):
        load_strength(csv_path)
