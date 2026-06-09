"""Render the dashboard view dict to a self-contained HTML string via Jinja2."""
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def render_dashboard(view: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("dashboard.html.j2")
    # Embed computed data as JSON for Chart.js; tojson handles escaping safely.
    return template.render(view=view, view_json=json.dumps(view))
