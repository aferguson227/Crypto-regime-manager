from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_activity_strip_does_not_call_getsaved_before_storage_constants_initialise():
    text=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    act=text.index("const act=$('#crm-activity')")
    storage=text.index("const legacyAckKey=")
    between=text[act:storage]
    assert "getSaved().length" not in between
    assert "crm_recommended_bots_v1" in between

def test_staged_status_has_container_aware_fit():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert ".crm-staged-row .crm-status" in css
    assert "font-size:clamp(.68rem,2.7cqi,.88rem)" in css
