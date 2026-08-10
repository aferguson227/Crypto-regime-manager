# CRM V67.0.0 — KuCoin Live Trading Data Service & Multi-Bot Capital Control

V66 replaces the repeated short-lived private-data pattern with a resident, read-only KuCoin Live Trading Data Service.

## Live trading truth
- Resident Windows task starts at logon under the same Windows user that owns the encrypted KuCoin credentials.
- Public prices and active-order truth refresh approximately every 20 seconds.
- Private balances/fills/accounting refresh approximately every 60 seconds.
- Heavy research remains completely separate.
- The dashboard also marks the currently open position from KuCoin's public price every 15 seconds in the browser, so Open P/L and Total P/L can move between publication cycles.
- Open P/L carries an active-capital percentage. Realised and total P/L show a clearly labelled percentage relative to current portfolio value.

## Order visibility
- Order-state collection now queries the official all-open HF Spot endpoint in addition to symbol-scoped HF, Classic compatibility and stop-order coverage.

## Deployment & DCA
- Deployment plans render only optimised strategy fields in Recommended DCA Settings and only execution-policy fields in Governed Controls; irrelevant blank rows are removed.
- A failed unseen-validation run is shown as completed failure and enters a fresh-research queue. CRM does not tune directly against the failed unseen sample.

## Multi-bot capital
- Conservative safe allocation remains the deployment gate.
- CRM also calculates conditional multi-bot capacity using validated average safety-order depth, but labels it advisory only and never uses it to unlock automated deployment.
- Live TEL revalidation records whether the latest validated strategy would still be selected today, while keeping the active deal frozen.

## Reliability
- Schedule health covers Local Agent, Live Data Service and Research Worker separately.
- System Health can restart the resident service safely if its heartbeat disappears.
- The dashboard's V63/V65 data-loader mismatch has been corrected so Portfolio Capital V2, Integrity, Live Revalidation, Fast Live Truth, Canonical KuCoin, live prices and service heartbeat map to the correct files.

Native KuCoin live order placement/cancellation remains HARD LOCKED.
