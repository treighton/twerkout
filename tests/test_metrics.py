import pytest
from twerkout.metrics import (
    week_for_date, e1rm, planned_met_zone2, planned_met_ruck,
    planned_met_hill, ruck_load, recovery_score, status_for_score,
)


def test_week_for_date_matches_spreadsheet_formula():
    # INT((date - start)/7)+1 ; start is week 1 day 1
    assert week_for_date("2026-06-01", "2026-06-01") == 1
    assert week_for_date("2026-06-07", "2026-06-01") == 1  # day 7 still week 1
    assert week_for_date("2026-06-08", "2026-06-01") == 2  # day 8 -> week 2
    assert week_for_date("2026-06-22", "2026-06-01") == 4


def test_e1rm_epley_with_actual_reps():
    # Epley: weight * (1 + reps/30)
    assert e1rm(225, 5) == pytest.approx(225 * (1 + 5 / 30))
    assert e1rm(100, 1) == pytest.approx(100 * (1 + 1 / 30))  # ~103.33, not 100.0


def test_e1rm_blank_inputs_return_none():
    assert e1rm(None, 5) is None
    assert e1rm(225, None) is None


def test_planned_met_zone2_compares_duration_to_plan():
    assert planned_met_zone2(actual_min=35, planned_min=30) == "Yes"
    assert planned_met_zone2(actual_min=25, planned_min=30) == "No"
    assert planned_met_zone2(actual_min=None, planned_min=30) == ""
    assert planned_met_zone2(actual_min=35, planned_min=None) == ""


def test_planned_met_ruck_requires_weight_and_duration():
    # spreadsheet: AND(pack_wt >= planned_wt, duration >= planned_min)
    assert planned_met_ruck(30, 25, 45, 40) == "Yes"
    assert planned_met_ruck(20, 25, 45, 40) == "No"   # weight short
    assert planned_met_ruck(30, 25, 30, 40) == "No"   # duration short
    assert planned_met_ruck(None, 25, 45, 40) == ""


def test_planned_met_hill_compares_repeats():
    assert planned_met_hill(actual_repeats=9, planned_repeats=8) == "Yes"
    assert planned_met_hill(actual_repeats=7, planned_repeats=8) == "No"
    assert planned_met_hill(actual_repeats=None, planned_repeats=8) == ""


def test_ruck_load_is_weight_times_duration():
    assert ruck_load(30, 45) == 1350
    assert ruck_load(None, 45) is None
    assert ruck_load(30, None) is None


def test_recovery_score_formula():
    # (sleep/8*4)+(energy/10*3)-((fatigue+soreness)/20*3)
    score = recovery_score(sleep=8, energy=10, fatigue=2, soreness=2)
    expected = (8 / 8 * 4) + (10 / 10 * 3) - ((2 + 2) / 20 * 3)
    assert score == pytest.approx(expected)


def test_recovery_score_blank_returns_none():
    assert recovery_score(sleep=None, energy=10, fatigue=2, soreness=2) is None


def test_status_thresholds():
    assert status_for_score(1.0) == "Back Off"   # < 1.5
    assert status_for_score(1.5) == "Caution"     # >=1.5, <2.5
    assert status_for_score(2.4) == "Caution"
    assert status_for_score(2.5) == "On Track"    # >= 2.5
    assert status_for_score(None) == ""
