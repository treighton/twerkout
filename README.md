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

A typical training week (with `program_start = 2026-06-01`, a Monday):

| Day | Session | File |
|-----|---------|------|
| Mon | Zone 2 spin bike | `zone2.csv` |
| Tue | Starting Strength | `strength.csv` |
| Wed | Ruck | `ruck.csv` |
| Thu | Starting Strength | `strength.csv` |
| Fri | Hill repeats | `hill.csv` |
| Sat | Starting Strength | `strength.csv` |
| Sun | Rest | — |

Record recovery once per week (`recovery.csv`). Leave any cell blank if you
didn't measure it — blanks become "no value" and are skipped in calculations
(notice the empty `bench` cell in the strength example below).

### Strength (`strength.csv`)

`date, workout, bodyweight, squat, press, bench, deadlift, reps, notes` — enter
the weight for each lift you did and the **actual reps** performed; e1RM is
computed per lift via the Epley formula. Starting Strength alternates workout A
(squat / press / deadlift) and B (squat / bench / deadlift), so some lift
columns are blank on any given day.

```csv
date,workout,bodyweight,squat,press,bench,deadlift,reps,notes
2026-06-02,A,180,225,115,,275,5,felt easy
2026-06-04,B,180,230,,135,,5,bench was a grind
```

### Zone 2 (`zone2.csv`)

`date, activity, duration_min, avg_hr, distance, resistance, rpe, notes` —
aerobic base work. Week 1 plans 30 min; logging 30+ marks it "met".

```csv
date,activity,duration_min,avg_hr,distance,resistance,rpe,notes
2026-06-01,Spin Bike,30,135,,8,4,kept HR in zone 2
```

### Ruck (`ruck.csv`)

`date, pack_weight, duration_min, distance, elevation, terrain, notes` — week 1
plans 30 min @ 20 lb; the dashboard marks it "met" when both pack weight and
duration reach the plan, and computes ruck load = pack weight × duration.

```csv
date,pack_weight,duration_min,distance,elevation,terrain,notes
2026-06-03,20,30,2,150,Trail,run uphill / walk down
```

### Hill repeats (`hill.csv`)

`date, repeats, hill_len_sec, rpe, walk_down, notes` — week 1 plans 4 repeats.
Run up, walk down to recover, aim for RPE 7–8, finishing like you had 1–2 more
in the tank.

```csv
date,repeats,hill_len_sec,rpe,walk_down,notes
2026-06-05,4,45,8,Yes,walked down between each
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
