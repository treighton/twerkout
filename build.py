"""Entrypoint: load data/, compute the view, render dashboard.html.

Usage: python build.py [--data DIR] [--out FILE]
Defaults: --data ./data  --out ./dashboard.html
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

import argparse

from twerkout import data
from twerkout.rollups import build_view
from twerkout.render import render_dashboard


def run(data_dir: Path, out: Path) -> Path:
    view = build_view(
        config=data.load_config(data_dir / "config.csv"),
        program=data.load_program(data_dir / "program.csv"),
        strength=data.load_strength(data_dir / "strength.csv"),
        zone2=data.load_zone2(data_dir / "zone2.csv"),
        ruck=data.load_ruck(data_dir / "ruck.csv"),
        hill=data.load_hill(data_dir / "hill.csv"),
        recovery=data.load_recovery(data_dir / "recovery.csv"),
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render_dashboard(view))
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--data", default="data", type=Path)
    parser.add_argument("--out", default="dashboard.html", type=Path)
    args = parser.parse_args()
    written = run(args.data, args.out)
    print(f"Wrote {written}")


if __name__ == "__main__":
    main()
