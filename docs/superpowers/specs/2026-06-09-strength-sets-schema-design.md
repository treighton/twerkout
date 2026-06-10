# Strength Log: Per-Lift Sets/Reps Schema — Design

**Date:** 2026-06-09
**Status:** Approved design, pending implementation plan
**Supersedes:** the strength-log portion of `2026-06-09-twerkout-dashboard-design.md`

## Problem

The current `strength.csv` schema is one row per day with a single weight per
lift and ONE shared `reps` value across all four lifts:

```
date, workout, bodyweight, squat, press, bench, deadlift, reps, notes
```

This cannot represent a real Starting Strength session. SS is performed as sets
across reps — squat/press/bench are 3×5, deadlift is 1×5 — and the current
schema has no notion of sets, forces all lifts on a day to share one rep count,
and stores each lift as a bare number. It was carried over from the original
spreadsheet, which had the same limitation.

## Decision

Move to **one row per lift**, with explicit `weight`, `sets`, and `reps`. The
user trains standard 3×5, so set-level rows would be redundant (every set is
identical); lift-level rows are the smallest unit that varies independently
(weights differ per lift, and deadlift is 1×5 not 3×5).

### New `data/strength.csv` schema

```
date, workout, lift, weight, sets, reps, bodyweight, notes
```

- `date` — ISO date of the session (same date repeated for each lift that day).
- `workout` — "A" / "B" / "Other" (session label; kept for context + A/B view).
- `lift` — the movement: squat, press, bench, deadlift (free text; lowercased
  on load for consistent grouping).
- `weight` — work-set weight (one weight per lift, true for standard SS).
- `sets` — number of work sets (e.g. 3 for squat, 1 for deadlift).
- `reps` — reps per set (5 for standard SS).
- `bodyweight` — session bodyweight; recorded once per day on the FIRST row of
  that date, blank on the others. The build picks up the day's value.
- `notes` — free text.

### Example (Workout A day)

```csv
date,workout,lift,weight,sets,reps,bodyweight,notes
2026-06-09,A,squat,225,3,5,180,felt easy
2026-06-09,A,press,115,3,5,,
2026-06-09,A,deadlift,275,1,5,,across the back
```

## Derived values

| Value | Formula | Notes |
|---|---|---|
| week | `floor((date − program_start)/7)+1` | unchanged |
| e1RM (per lift row) | `weight × (1 + reps/30)` (Epley) | uses the row's actual reps; ONE e1RM per row now, not four columns |
| (optional, NOT building) | tonnage = weight×sets×reps | deferred — YAGNI until requested |

## View shape changes

`enrich_strength` returns one dict per lift-row:
```
{ date, week, workout, lift, weight, sets, reps, bodyweight, notes, e1rm }
```
(was: one dict per day with `e1rm_squat/press/bench/deadlift`.)

The downstream aggregates keep their EXISTING output shapes so the template's
chart JS and summary cards need minimal change:

- `_e1rm_series`: still `{ lift_name: [ {date, value}, ... ] }`, but built by
  grouping rows on the `lift` field (dynamic keys) rather than four fixed
  columns. The e1RM trend chart (one line per lift) is unchanged.
- `_summary.latest_e1rm`: still `{ lift_name: latest_e1rm }`, computed as the
  most-recent (by date) e1RM per distinct `lift`. The summary cards loop over
  this dict unchanged.

## Dashboard table change

The "Strength (derived)" collapsible table becomes **one row per lift entry**:

| Date | Wk | Workout | Lift | Weight×Sets×Reps | e1RM |
|------|----|---------|------|------------------|------|

(was: Date, Wk, e1RM Sq/Pr/Be/Dl). The "Weight×Sets×Reps" cell renders e.g.
`225 × 3 × 5`. The e1RM trend chart and summary e1RM cards are unchanged.

## Error handling

Consistent with the existing "loud failure with context" approach:
- `weight`, `sets`, `reps`, `bodyweight` parse via the existing `_num` helper
  (blank → None; bad number → ValueError naming file+field).
- Blank `lift` on a populated row → the row can't be grouped/charted; treat a
  blank `lift` as an error (`ValueError` naming the file), since every strength
  row must name its lift. (Mirrors the date/week loud-failure precedent.)
- A blank `weight` or `reps` → e1RM is None for that row (skipped in charts),
  same as before.

## Out of scope

- Per-set rows / ramping / AMRAP (not how the user trains).
- Tonnage/volume metrics.
- Migrating historical data (the seeded strength.csv is header-only; just
  replace its header).

## Files affected

- `data/strength.csv` — new header (header-only; no data rows to migrate).
- `src/twerkout/models.py` — `StrengthRow` fields.
- `src/twerkout/data.py` — `load_strength` (new columns; lowercase lift; blank-
  lift error).
- `src/twerkout/rollups.py` — `enrich_strength`, `_e1rm_series`, `_summary`.
- `templates/dashboard.html.j2` — strength table (per-lift rows).
- `tests/` — update strength fixtures + tests for the new shape.
- `README.md` — strength logging example.
