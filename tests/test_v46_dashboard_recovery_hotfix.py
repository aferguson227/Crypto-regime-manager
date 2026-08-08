from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def test_formatter_money_contract_exists():
    text=(ROOT/'docs/design-system.js').read_text(encoding='utf-8')
    assert "money(v,c='USDT'" in text

def test_dashboard_uses_quote_formatter_for_accounting():
    text=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "CRMFormat.money(" not in text
    assert "accounting.open_pnl_quote" in text

def test_dashboard_late_sections_are_isolated():
    text=(ROOT/'docs/unified_dashboard.js').read_text(encoding='utf-8')
    assert "function safeRender(name,fn,selector)" in text
    assert "safeRender('Recommended Bots'" in text
    assert "safeRender('V46 intelligence'" in text

def test_card_layout_is_container_responsive():
    css=(ROOT/'docs/design-system.css').read_text(encoding='utf-8')
    assert ".crm-card{container-type:inline-size}" in css
    assert "grid-template-columns:minmax(8rem,1.05fr) minmax(6rem,.8fr)" in css

def test_hero_actions_align_status_and_refresh():
    html=(ROOT/'docs/index.html').read_text(encoding='utf-8')
    assert 'class="crm-hero-actions"' in html
