from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]


def test_v22_version_files_are_consistent():
    assert (ROOT / "VERSION").read_text(encoding="utf-8").strip() == "26.0.0"
    version = json.loads((ROOT / "docs" / "version.json").read_text(encoding="utf-8"))
    assert version["version"] == "26.0.0"
    config = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
    assert config["version"] == "26.0.0"


def test_research_queue_uses_v22_mobile_design_and_guardrails():
    html = (ROOT / "docs" / "research_queue.html").read_text(encoding="utf-8")
    assert 'href="v22.css"' in html
    assert "Evidence " in html
    assert "Forward test" in html
    assert "Compare all" in html
    assert "LIVE CHANGES DISABLED" in html
    assert "Automatic production changes" in html


def test_v22_css_has_mobile_layout():
    css = (ROOT / "docs" / "v22.css").read_text(encoding="utf-8")
    assert "@media(max-width:620px)" in css
    assert ".v22-candidate.winner" in css
    assert ".v22-stage" in css
