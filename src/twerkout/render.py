"""Render the dashboard view dict to a self-contained HTML string via Jinja2."""
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"


def render_dashboard(view: dict) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        keep_trailing_newline=True,
    )
    template = env.get_template("dashboard.html.j2")
    # Embed computed data as a JSON island for the charts. json.dumps produces
    # valid JSON; escape "</" so a stray "</script>" in a notes field can't
    # terminate the <script> element early.
    view_json = json.dumps(view).replace("</", "<\\/")
    return template.render(view=view, view_json=view_json)
