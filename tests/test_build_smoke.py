import json
from pathlib import Path

import pytest

from build import run

FIX = Path(__file__).parent / "fixtures"


def test_build_produces_dashboard_with_expected_data(tmp_path):
    out = run(FIX, tmp_path / "dashboard.html")
    html = out.read_text()
    assert "<title>Twerkout" in html
    # extract embedded JSON and verify computed values flowed through
    start = html.index('id="data"')
    json_start = html.index(">", start) + 1
    json_end = html.index("</script>", json_start)
    view = json.loads(html[json_start:json_end])
    assert view["summary"]["current_week"] == 1
    assert view["zone2"][0]["planned_met"] == "Yes"   # 35 >= 30
    assert view["ruck"][0]["load"] == 30 * 45
    assert view["recovery"][0]["status"] == "On Track"  # fixture score 5.5
    assert view["hill"][0]["planned_met"] == "Yes"      # 5 repeats >= 4 planned (week 1)
    # strength is now per-lift: first fixture row is squat 225×3×5
    assert view["strength"][0]["lift"] == "squat"
    assert view["strength"][0]["e1rm"] == pytest.approx(225 * (1 + 5 / 30), rel=1e-3)
