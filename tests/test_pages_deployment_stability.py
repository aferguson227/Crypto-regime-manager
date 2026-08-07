from pathlib import Path
ROOT=Path(__file__).parents[1]

def test_single_dedicated_pages_publisher():
    pages=(ROOT/'.github/workflows/pages-deploy.yml').read_text(encoding='utf-8')
    assert 'actions/upload-pages-artifact@v4' in pages
    assert 'actions/deploy-pages@v4' in pages
    assert 'needs: build' in pages
    assert 'group: crm-github-pages' in pages
    assert 'cancel-in-progress: false' in pages
    assert 'timeout-minutes: 30' in pages
    assert "path: docs" in pages
    for name in ('crm-data-refresh.yml','crm-health-self-heal.yml','crm-release-validation.yml'):
        text=(ROOT/'.github/workflows'/name).read_text(encoding='utf-8')
        assert 'actions/deploy-pages' not in text
        assert 'actions/upload-pages-artifact' not in text

def test_cloud_update_uses_runtime_diagnostics_output():
    text=(ROOT/'scripts/cloud_update.py').read_text(encoding='utf-8')
    assert 'build_report, RUNTIME_OUTPUT' in text
    assert 'build_report, OUTPUT' not in text
    assert 'RUNTIME_OUTPUT.write_text' in text
