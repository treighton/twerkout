# Strength Sets/Reps Schema — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Change the strength log from one-row-per-day (single weight+reps per lift) to one-row-per-lift with explicit weight/sets/reps, so it faithfully records standard 3×5 Starting Strength sessions.

**Architecture:** `StrengthRow` becomes a per-lift record. `load_strength` parses the new columns and lowercases `lift`. `enrich_strength` emits one dict per lift-row with a single `e1rm`. `_e1rm_series` and `_summary.latest_e1rm` group dynamically on the `lift` field but keep their existing output shapes, so the chart JS and summary cards are unchanged. The strength table renders one row per lift entry. Seeded CSV header and README example updated.

**Tech Stack:** Python 3.13, Jinja2, pytest (existing).

---

## Task 1: Update StrengthRow model

**Files:**
- Modify: `src/twerkout/models.py`
- Test: `tests/test_data.py`

- [ ] **Step 1: Write the failing test** (append to `tests/test_data.py`)

```python
def test_strength_row_new_per_lift_shape():
    from twerkout.models import StrengthRow
    row = StrengthRow(date="2026-06-09", workout="A", lift="squat",
                      weight=225, sets=3, reps=5, bodyweight=180, notes="ok")
    assert row.lift == "squat"
    assert row.weight == 225
    assert row.sets == 3
    assert row.reps == 5

def test_strength_row_defaults():
    from twerkout.models import StrengthRow
    row = StrengthRow(date="2026-06-09", lift="press")
    assert row.weight is None
    assert row.sets is None
    assert row.bodyweight is None
    assert row.workout == ""
```

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_data.py::test_strength_row_new_per_lift_shape -v`
Expected: FAIL with `TypeError` (unexpected keyword `lift`).

- [ ] **Step 3: Replace `StrengthRow` in `src/twerkout/models.py`**

Replace the existing `StrengthRow` dataclass with:

```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_data.py -v`
Expected: the two new tests PASS. NOTE: the OLD `test_strength_row_optional_fields_default_none` (from earlier work) references `row.squat` / `row.reps` and will now FAIL because `squat` no longer exists. DELETE that old test (`test_strength_row_optional_fields_default_none`) — it tests the obsolete schema and is replaced by `test_strength_row_defaults` above.

- [ ] **Step 5: Run full data test file**

Run: `.venv/bin/python -m pytest tests/test_data.py -v`
Expected: all pass (old obsolete test removed). The `load_strength` tests will still fail until Task 2 — that's expected; if they error on collection, proceed to Task 2 which fixes the loader and its tests together.

- [ ] **Step 6: Commit**

```bash
git add src/twerkout/models.py tests/test_data.py
git commit -m "feat: StrengthRow becomes per-lift (lift/weight/sets/reps)"
```

---

## Task 2: Update load_strength + fixtures + loader tests

**Files:**
- Modify: `src/twerkout/data.py` (`load_strength`)
- Modify: `tests/fixtures/strength.csv`
- Modify: `tests/test_data.py` (the `test_load_strength_blanks_become_none` test + the bad-number test reference the old columns)

- [ ] **Step 1: Update the fixture** `tests/fixtures/strength.csv` to the new per-lift shape (two lifts on one day, plus a blank-bodyweight second row):

```csv
date,workout,lift,weight,sets,reps,bodyweight,notes
2026-06-09,A,squat,225,3,5,180,felt strong
2026-06-09,A,press,115,3,5,,
```

- [ ] **Step 2: Write the failing/updated loader tests.** In `tests/test_data.py`, REPLACE the body of `test_load_strength_blanks_become_none` with the new shape, and update the bad-number test to use a column that still exists. New tests:

```python
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


def test_load_strength_lowercases_lift():
    import tempfile, os
    from pathlib import Path as _P
    content = ("date,workout,lift,weight,sets,reps,bodyweight,notes\n"
               "2026-06-09,A,SQUAT,225,3,5,180,\n")
    d = _P(tempfile.mkdtemp())
    (d / "s.csv").write_text(content)
    rows = load_strength(d / "s.csv")
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
```

Also DELETE the old `test_load_strength_blanks_become_none` test (it references `squat`/`press` columns that no longer exist) and the old `test_load_strength_bad_number_raises_with_context` if it references `bodyweight` in the OLD column layout — actually that one used `bodyweight` which still exists, but the OLD fixture had a different header. Re-point it: ensure any remaining strength loader test uses the NEW header. Simplest: delete `test_load_strength_blanks_become_none` and `test_load_strength_bad_number_raises_with_context`, replaced by the four tests above.

- [ ] **Step 3: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_data.py -k strength -v`
Expected: FAIL (load_strength still builds the old StrengthRow with squat/press/etc.).

- [ ] **Step 4: Replace `load_strength` in `src/twerkout/data.py`**

```python
def load_strength(path: Path) -> list[StrengthRow]:
    out = []
    for r in _rows(path):
        lift = (r.get("lift") or "").strip().lower()
        if not lift:
            raise ValueError(f"{path.name}: blank lift on row dated {r.get('date', '?')!r}")
        out.append(StrengthRow(
            date=r["date"].strip(),
            lift=lift,
            workout=(r.get("workout") or "").strip(),
            weight=_num(r["weight"], field="weight", source=path),
            sets=_num(r["sets"], field="sets", source=path),
            reps=_num(r["reps"], field="reps", source=path),
            bodyweight=_num(r["bodyweight"], field="bodyweight", source=path),
            notes=(r.get("notes") or "").strip(),
        ))
    return out
```

- [ ] **Step 5: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_data.py -v`
Expected: all data tests pass.

- [ ] **Step 6: Commit**

```bash
git add src/twerkout/data.py tests/fixtures/strength.csv tests/test_data.py
git commit -m "feat: load_strength parses per-lift rows; lowercases lift; errors on blank lift"
```

---

## Task 3: Update enrich_strength, _e1rm_series, _summary

**Files:**
- Modify: `src/twerkout/rollups.py`
- Modify: `tests/test_rollups.py`

- [ ] **Step 1: Write the failing/updated tests.** In `tests/test_rollups.py`, the existing `test_enrich_strength_adds_week_and_e1rm` uses the old shape — REPLACE it, and add series/summary coverage:

```python
def test_enrich_strength_per_lift_adds_week_and_e1rm():
    from twerkout.models import StrengthRow
    from twerkout.rollups import enrich_strength
    rows = [
        StrengthRow(date="2026-06-09", workout="A", lift="squat", weight=225, sets=3, reps=5, bodyweight=180),
        StrengthRow(date="2026-06-09", workout="A", lift="deadlift", weight=275, sets=1, reps=5),
    ]
    out = enrich_strength(rows, START)
    assert out[0]["week"] == 1
    assert out[0]["lift"] == "squat"
    assert out[0]["sets"] == 3
    assert round(out[0]["e1rm"], 1) == round(225 * (1 + 5 / 30), 1)
    assert round(out[1]["e1rm"], 1) == round(275 * (1 + 5 / 30), 1)


def test_enrich_strength_blank_weight_gives_none_e1rm():
    from twerkout.models import StrengthRow
    from twerkout.rollups import enrich_strength
    rows = [StrengthRow(date="2026-06-09", lift="press", sets=3, reps=5)]
    out = enrich_strength(rows, START)
    assert out[0]["e1rm"] is None
```

Note: `START` and `PROGRAM` are already defined at the top of test_rollups.py. The existing `test_build_view_assembles_all_sections` and `test_summary_latest_e1rm_is_by_date_not_position` construct `StrengthRow(date=..., workout="A", squat=225, reps=5)` — these will break. UPDATE every `StrengthRow(...)` call in test_rollups.py that uses `squat=`/`reps=` (old kwargs) to the new per-lift kwargs `lift="squat", weight=225, sets=3, reps=5`. Specifically:
- In `test_build_view_assembles_all_sections`: change the strength list to `[StrengthRow(date="2026-06-02", workout="A", lift="squat", weight=225, sets=3, reps=5)]` and update its assertion `view["summary"]["latest_e1rm"]` to expect a "squat" key.
- In `test_summary_latest_e1rm_is_by_date_not_position`: the two out-of-order rows become `StrengthRow(date="2026-06-09", lift="squat", weight=250, sets=3, reps=5)` and `StrengthRow(date="2026-06-02", lift="squat", weight=225, sets=3, reps=5)`; the assertion `view["summary"]["latest_e1rm"]["squat"] == round(250 * (1 + 5/30), 1)` stays valid.

- [ ] **Step 2: Run to verify failure**

Run: `.venv/bin/python -m pytest tests/test_rollups.py -v`
Expected: FAIL (enrich_strength still emits e1rm_squat etc.).

- [ ] **Step 3: Replace `enrich_strength` in `src/twerkout/rollups.py`**

```python
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
```

- [ ] **Step 4: Replace `_e1rm_series` in `src/twerkout/rollups.py`** (group dynamically by the `lift` field; keep the same output shape `{lift: [{date,value},...]}`; preserve chronological order):

```python
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
```

- [ ] **Step 5: Replace the `latest_e1rm` block in `_summary`** in `src/twerkout/rollups.py`. Find the block:

```python
    latest_e1rm = {}
    for lift in ("squat", "press", "bench", "deadlift"):
        vals = [r[f"e1rm_{lift}"] for r in strength_by_date if r.get(f"e1rm_{lift}") is not None]
        latest_e1rm[lift] = round(vals[-1], 1) if vals else None
```

Replace it with (group by the `lift` field; last by date wins):

```python
    latest_e1rm: dict[str, float] = {}
    for r in strength_by_date:  # already sorted by date ascending
        if r.get("e1rm") is not None:
            latest_e1rm[r["lift"]] = round(r["e1rm"], 1)
```

(`strength_by_date` is already defined earlier in `_summary` as `sorted(strength, key=lambda r: r["date"])`. Since it's ascending, the last assignment per lift is the most recent. Leave the rest of `_summary` unchanged.)

- [ ] **Step 6: Run to verify pass**

Run: `.venv/bin/python -m pytest tests/test_rollups.py -v`
Expected: all rollup tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/twerkout/rollups.py tests/test_rollups.py
git commit -m "feat: per-lift strength enrichment, e1rm series, and latest_e1rm"
```

---

## Task 4: Update the dashboard strength table

**Files:**
- Modify: `templates/dashboard.html.j2`

- [ ] **Step 1: Replace the Strength (derived) table block.** Find:

```html
<details>
  <summary>Strength (derived)</summary>
  <table>
    <tr><th>Date</th><th>Wk</th><th>e1RM Sq</th><th>e1RM Pr</th><th>e1RM Be</th><th>e1RM Dl</th></tr>
    {% for r in view.strength %}
    <tr><td>{{ r.date }}</td><td>{{ r.week }}</td>
      <td>{{ r.e1rm_squat|round(1) if r.e1rm_squat is not none else "" }}</td>
      <td>{{ r.e1rm_press|round(1) if r.e1rm_press is not none else "" }}</td>
      <td>{{ r.e1rm_bench|round(1) if r.e1rm_bench is not none else "" }}</td>
      <td>{{ r.e1rm_deadlift|round(1) if r.e1rm_deadlift is not none else "" }}</td></tr>
    {% endfor %}
  </table>
</details>
```

Replace with (one row per lift entry; Weight×Sets×Reps cell; single e1RM):

```html
<details>
  <summary>Strength (derived)</summary>
  <table>
    <tr><th>Date</th><th>Wk</th><th>Workout</th><th>Lift</th><th>Weight × Sets × Reps</th><th>e1RM</th></tr>
    {% for r in view.strength %}
    <tr><td>{{ r.date }}</td><td>{{ r.week }}</td><td>{{ r.workout }}</td><td>{{ r.lift }}</td>
      <td>{% if r.weight is not none %}{{ r.weight }} × {{ r.sets if r.sets is not none else "?" }} × {{ r.reps if r.reps is not none else "?" }}{% endif %}</td>
      <td>{{ r.e1rm|round(1) if r.e1rm is not none else "" }}</td></tr>
    {% endfor %}
  </table>
</details>
```

(The summary e1RM cards loop `view.summary.latest_e1rm.items()` and the e1RM chart reads `VIEW.e1rm_series` — both keep their shape, so NO change is needed to those parts of the template.)

- [ ] **Step 2: Render check**

Run:
```bash
.venv/bin/python build.py --out /tmp/strength_check.html && grep -c "Weight × Sets × Reps" /tmp/strength_check.html
```
Expected: prints `Wrote /tmp/strength_check.html` then `1`.

- [ ] **Step 3: Commit**

```bash
git add templates/dashboard.html.j2
git commit -m "feat: strength dashboard table shows one row per lift (weight×sets×reps, e1RM)"
```

---

## Task 5: Reseed data/strength.csv + update smoke test + README

**Files:**
- Modify: `data/strength.csv`
- Modify: `tests/test_build_smoke.py`
- Modify: `README.md`

- [ ] **Step 1: Replace the header of `data/strength.csv`** (header-only seeded file) with the new schema:

```csv
date,workout,lift,weight,sets,reps,bodyweight,notes
```

- [ ] **Step 2: Update the smoke test.** `tests/test_build_smoke.py` runs the pipeline over `tests/fixtures/` (whose strength.csv was updated in Task 2). Add an assertion for the new shape and ensure existing assertions still hold. After the existing assertions, add:

```python
    # strength is now per-lift: first fixture row is squat 225×3×5
    assert view["strength"][0]["lift"] == "squat"
    assert view["strength"][0]["e1rm"] == pytest.approx(225 * (1 + 5 / 30), rel=1e-3)
```

(`import pytest` is already present in this file from earlier work; if not, add it.)

- [ ] **Step 3: Run the smoke test + full suite**

Run: `.venv/bin/python -m pytest -v`
Expected: ALL pass.

- [ ] **Step 4: Update the README strength example.** In `README.md`, replace the strength example block:

```csv
date,workout,bodyweight,squat,press,bench,deadlift,reps,notes
2026-06-09,A,180,225,115,,275,5,felt easy
2026-06-11,B,180,230,,135,,5,bench was a grind
```

with the per-lift version, and update the surrounding prose to describe lift/weight/sets/reps and once-per-day bodyweight:

```csv
date,workout,lift,weight,sets,reps,bodyweight,notes
2026-06-09,A,squat,225,3,5,180,felt easy
2026-06-09,A,press,115,3,5,,
2026-06-09,A,deadlift,275,1,5,,across the back
```

Also update the column list near the top of "Logging a workout" for `strength.csv` from the old columns to:
`date, workout, lift, weight, sets, reps, bodyweight, notes`

And adjust the strength prose to explain: one row per lift; standard 3×5 means sets=3 (deadlift sets=1); bodyweight on the first row of the day; e1RM uses actual reps.

- [ ] **Step 5: Verify the README example through the real pipeline**

Run this to confirm the README rows parse and compute (squat 3×5 → e1RM, deadlift 1×5 → e1RM, week 1):
```bash
TMP=$(mktemp -d); cp data/program.csv data/config.csv "$TMP/"
printf 'date,workout,lift,weight,sets,reps,bodyweight,notes\n2026-06-09,A,squat,225,3,5,180,felt easy\n2026-06-09,A,press,115,3,5,,\n2026-06-09,A,deadlift,275,1,5,,across the back\n' > "$TMP/strength.csv"
for f in zone2 ruck hill recovery; do head -1 data/$f.csv > "$TMP/$f.csv"; done
.venv/bin/python -c "
import sys; sys.path.insert(0,'src')
from pathlib import Path
from twerkout import data
from twerkout.rollups import build_view
d=Path('$TMP')
v=build_view(config=data.load_config(d/'config.csv'),program=data.load_program(d/'program.csv'),
 strength=data.load_strength(d/'strength.csv'),zone2=data.load_zone2(d/'zone2.csv'),
 ruck=data.load_ruck(d/'ruck.csv'),hill=data.load_hill(d/'hill.csv'),recovery=data.load_recovery(d/'recovery.csv'))
for r in v['strength']: print(r['lift'], r['weight'], 'x', r['sets'], 'x', r['reps'], '-> e1rm', round(r['e1rm'],1), 'week', r['week'])
print('latest_e1rm:', v['summary']['latest_e1rm'])
"; rm -rf "$TMP"
```
Expected: three lifts printed with e1RM values, all week 1; `latest_e1rm` has squat/press/deadlift keys.

- [ ] **Step 6: Commit**

```bash
git add data/strength.csv tests/test_build_smoke.py README.md
git commit -m "feat: reseed strength.csv to per-lift schema; update smoke test and README example"
```

---

## Self-Review Notes

- **Spec coverage:** model (T1), loader+lowercase+blank-lift error (T2), enrichment/series/summary keeping output shapes (T3), dashboard table per-lift (T4), reseed+smoke+README (T5). All spec sections mapped.
- **Backward-incompatible test cleanup:** old tests referencing `squat=`/`reps=`/`e1rm_squat` kwargs/keys are explicitly updated or deleted in T1–T3 (not left to rot).
- **Output-shape stability:** `_e1rm_series` and `latest_e1rm` keep `{lift: ...}` shape so the template chart JS and summary cards need no change — only the strength table changes (T4).
- **e1RM unchanged:** still Epley on actual reps; one e1RM per lift row.
