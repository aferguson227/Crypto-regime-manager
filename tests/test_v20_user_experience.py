from pathlib import Path

def test_v20_release_and_primary_nav():
    root=Path(__file__).parents[1]
    assert tuple(map(int,(root/'VERSION').read_text(encoding="utf-8").strip().split('.'))) >= (20,0,0)
    for name in ['index.html','cockpit.html','data.html','more.html']:
        text=(root/'docs'/name).read_text(encoding="utf-8")
        assert 'V42.0.0' in text
        assert 'v20.css' in text
    assert 'design-system.js' in (root/'docs/research.html').read_text(encoding="utf-8")
    assert 'table-scroll' in (root/'docs/settings.html').read_text(encoding="utf-8")
