# Twerkout

A static training dashboard generated from hand-edited CSV files. Replaces the
Starting Strength Endurance Tracker spreadsheet.

## How it works

1. You edit the CSVs in `data/` (text editor, Excel, or Google Sheets).
2. `git push` triggers GitHub Actions, which runs `build.py`.
3. The dashboard is published to GitHub Pages.

The CSVs are the single source of truth and hold **only measured values**.
Everything derived (week number, e1RM, planned-vs-actual, recovery score/status,
weekly rollups) is computed by `build.py` at build time.

## Logging a workout

Add a row to the relevant file in `data/`:

- `strength.csv` — `date, workout, bodyweight, squat, press, bench, deadlift, reps, notes`
  (enter the actual reps performed; e1RM uses them via the Epley formula)
- `zone2.csv` — `date, activity, duration_min, avg_hr, distance, resistance, rpe, notes`
- `ruck.csv` — `date, pack_weight, duration_min, distance, elevation, terrain, notes`
- `hill.csv` — `date, repeats, hill_len_sec, rpe, walk_down, notes`
- `recovery.csv` — `week, bodyweight, avg_sleep, energy, fatigue, soreness, notes`

Leave any cell blank if you didn't measure it — blanks become "no value" and
are skipped in calculations.

### Planned targets

Planned values live ONLY in `data/program.csv` (one row per week). Each log row's
week is derived from its date and `program_start` in `data/config.csv`. To shift
or restart the program, change `program_start` — everything re-aligns.

### Suggested values (not enforced)

- workout: A, B, Other
- activity: Spin Bike, Rower, Outdoor Bike, Other
- terrain: Flat, Rolling, Hilly, Trail, Road

## Local development

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m pytest          # run tests
.venv/bin/python build.py           # generate dashboard.html
open dashboard.html                 # view locally
```

## Deploying (one-time GitHub setup)

After pushing to GitHub, enable Pages: **Settings → Pages → Build and deployment
→ Source: GitHub Actions**. This one-time toggle cannot be set from code. After
that, every push to `main` rebuilds and republishes the dashboard automatically.

## Metrics

| Metric | Formula |
|---|---|
| Week | floor((date − program_start)/7) + 1 |
| e1RM | weight × (1 + reps/30) (Epley) |
| Zone 2 met? | actual duration ≥ planned |
| Ruck met? | pack weight ≥ planned AND duration ≥ planned |
| Hill met? | repeats ≥ planned |
| Ruck load | pack weight × duration |
| Recovery score | (sleep/8×4)+(energy/10×3)−((fatigue+soreness)/20×3) |
| Status | <1.5 Back Off, <2.5 Caution, else On Track |
