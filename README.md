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

Add a row to the relevant file in `data/`. Each section below shows the header
and one example row you can copy, adapt, and paste under it.

A typical training week (the examples below use week 1 of the current
`program_start = 2026-06-09`):

| Day | Date | Session | File |
|-----|------|---------|------|
| Tue | 2026-06-09 | Starting Strength | `strength.csv` |
| Wed | 2026-06-10 | Ruck | `ruck.csv` |
| Thu | 2026-06-11 | Starting Strength | `strength.csv` |
| Fri | 2026-06-12 | Hill repeats | `hill.csv` |
| Sat | 2026-06-13 | Starting Strength | `strength.csv` |
| Mon | 2026-06-15 | Zone 2 spin bike | `zone2.csv` |
| Sun | — | Rest | — |

Record recovery once per week (`recovery.csv`). Leave any cell blank if you
didn't measure it — blanks become "no value" and are skipped in calculations.

### Strength (`strength.csv`)

`date, workout, lift, weight, sets, reps, bodyweight, notes` — **one row per
lift**. Enter the work-set weight, the number of `sets`, and the `reps` per set;
e1RM is computed per lift via the Epley formula using your actual reps. Standard
Starting Strength is 3×5 (`sets=3, reps=5`), except the deadlift, which is 1×5
(`sets=1`). Record `bodyweight` once per day on the first row; leave it blank on
the rest. A full Workout A day (squat / press / deadlift) is three rows:

```csv
date,workout,lift,weight,sets,reps,bodyweight,notes
2026-06-09,A,squat,225,3,5,180,felt easy
2026-06-09,A,press,115,3,5,,
2026-06-09,A,deadlift,275,1,5,,across the back
```

### Zone 2 (`zone2.csv`)

`date, activity, duration_min, avg_hr, distance, resistance, rpe, notes` —
aerobic base work. Week 1 plans 30 min; logging 30+ marks it "met".

```csv
date,activity,duration_min,avg_hr,distance,resistance,rpe,notes
2026-06-15,Spin Bike,30,135,,8,4,kept HR in zone 2
```

### Ruck (`ruck.csv`)

`date, pack_weight, duration_min, distance, elevation, terrain, notes` — week 1
plans 30 min @ 20 lb; the dashboard marks it "met" when both pack weight and
duration reach the plan, and computes ruck load = pack weight × duration.

```csv
date,pack_weight,duration_min,distance,elevation,terrain,notes
2026-06-10,20,30,2,150,Trail,run uphill / walk down
```

### Hill repeats (`hill.csv`)

`date, repeats, hill_len_sec, rpe, walk_down, notes` — week 1 plans 4 repeats.
Run up, walk down to recover, aim for RPE 7–8, finishing like you had 1–2 more
in the tank.

```csv
date,repeats,hill_len_sec,rpe,walk_down,notes
2026-06-12,4,45,8,Yes,walked down between each
```

### Recovery (`recovery.csv`)

`week, bodyweight, avg_sleep, energy, fatigue, soreness, notes` — one row per
week. `avg_sleep` is hours; `energy`, `fatigue`, `soreness` are 1–10. These feed
the recovery score and the Back Off / Caution / On Track status.

```csv
week,bodyweight,avg_sleep,energy,fatigue,soreness,notes
1,180,7.5,8,3,3,recovering well
```

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
