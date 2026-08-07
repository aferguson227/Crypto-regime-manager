from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_release_validation_installs_ci_dependencies_before_pytest():
    text = (ROOT / ".github/workflows/crm-release-validation.yml").read_text(encoding="utf-8")
    install = "python -m pip install --disable-pip-version-check -r requirements-ci.txt"
    pytest = "python -m pytest -q"
    assert install in text
    assert pytest in text
    assert text.index(install) < text.index(pytest)

def test_ci_requirements_include_pytest_and_cryptography():
    lines = {
        x.strip()
        for x in (ROOT / "requirements-ci.txt").read_text(encoding="utf-8").splitlines()
        if x.strip() and not x.strip().startswith("#")
    }
    assert "pytest" in lines
    assert "cryptography==46.0.7" in lines
