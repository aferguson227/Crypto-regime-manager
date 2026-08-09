# Crypto Regime Manager V56.0.0 — KuCoin Historical Research & Universal Responsive UI

## KuCoin-first autonomous research
- Local Agent now incrementally downloads public KuCoin 4h candles for the strongest USDT research candidates.
- BTC-USDT is always included as universal historical market evidence.
- Raw historical data is stored outside Git under C:\Crypto\CRM_Data\KuCoin\4h by default.
- A small number of pages/symbols are acquired per 15-minute cycle so live refresh remains responsive.
- Experimental BTC-quoted pairs are acquired only for serious USDT candidates and remain research-only.

## TEL-style research at scale
- KuCoin histories feed the existing seven entry-trigger families and DCA parameter search.
- New KuCoin walk-forward engine optimises only on a chronological training window, freezes settings, validates on unseen KuCoin data, and observes a later forward window.
- Longest trade, drawdown and unresolved-position penalties remain part of the objective.
- Kraken is now independent cross-exchange robustness evidence; absence of Kraken BTC/XBT no longer blocks KuCoin BTC historical evidence.

## Universal responsive UI
- All cards use role-based, container-aware typography.
- Long categorical values may wrap/shrink within their own cards without forcing numeric values and labels to share one font rule.
- Research Activity now shows historical-data acquisition progress and KuCoin walk-forward readiness.

## Safeguards
Research is read-only. V47 never creates, edits, starts or stops a bot and never places orders.
