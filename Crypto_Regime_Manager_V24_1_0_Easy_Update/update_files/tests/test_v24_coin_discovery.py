from scripts.core.coin_discovery import evaluate, analyse_market


def test_v24_eligibility_rejects_configured_symbol():
    cfg = {
        "quote_currency": "USDT",
        "eligibility": {
            "exclude_symbols": ["TEL-USDT"],
            "exclude_stablecoins": True,
            "exclude_leveraged_tokens": True,
            "minimum_24h_quote_volume_usdt": 1_000_000,
            "maximum_spread_pct": 0.6,
        },
    }
    row = {"symbol": "TEL-USDT", "baseCurrency": "TEL", "quoteCurrency": "USDT", "enableTrading": True}
    ticker = {"volValue": "5000000", "buy": "0.001", "sell": "0.001001", "last": "0.001", "changeRate": "0.01"}
    result = evaluate(row, ticker, cfg)
    assert not result.eligible
    assert "already configured" in result.reasons


def test_v24_eligibility_accepts_liquid_asset():
    cfg = {
        "quote_currency": "USDT",
        "eligibility": {
            "exclude_symbols": [],
            "exclude_stablecoins": True,
            "exclude_leveraged_tokens": True,
            "minimum_24h_quote_volume_usdt": 1_000_000,
            "maximum_spread_pct": 0.6,
        },
    }
    row = {"symbol": "ABC-USDT", "baseCurrency": "ABC", "quoteCurrency": "USDT", "enableTrading": True}
    ticker = {"volValue": "5000000", "buy": "10", "sell": "10.01", "last": "10", "changeRate": "0.01"}
    assert evaluate(row, ticker, cfg).eligible
