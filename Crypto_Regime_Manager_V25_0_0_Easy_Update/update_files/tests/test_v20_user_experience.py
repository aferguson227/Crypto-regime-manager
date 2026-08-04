from pathlib import Path

def test_v20_release_and_primary_nav():
    root=Path(__file__).parents[1]
    assert tuple(map(int,(root/'VERSION').read_text().strip().split('.'))) >= (20,0,0)
    for name in ['index.html','cockpit.html','data.html','more.html']:
        text=(root/'docs'/name).read_text()
        assert 'V25.0.0' in text
        assert 'v20.css' in text
    assert 'v20-nav' in (root/'docs/research.html').read_text()
    assert 'table-scroll' in (root/'docs/settings.html').read_text()
