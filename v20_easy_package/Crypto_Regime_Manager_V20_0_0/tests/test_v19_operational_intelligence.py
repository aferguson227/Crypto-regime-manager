from pathlib import Path

def test_v19_pages_exist():
 p=Path(__file__).parents[1]/"docs"
 for f in ["explainability.html","timeline.html","integrity.html","v19.css"]: assert (p/f).exists()

def test_version():
 assert (Path(__file__).parents[1]/"VERSION").read_text().strip()=="19.0.0"
