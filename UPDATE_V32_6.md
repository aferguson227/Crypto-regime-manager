# V32.6.0 - Outcome Intelligence

V32.6.0 adds a read-only feedback layer that reconciles immutable recommendation IDs with observable active 3Commas deals and optional manual outcome annotations. It tracks pending, active, completed, ignored, expired, cancelled and superseded outcomes; calculates realised return, hold time, correctness and confidence calibration only when evidence exists; and never invents missing prices, returns or outcomes.

The new `outcome.html` page displays outcome status and calibration. Manual trading control and the strict read-only 3Commas boundary are unchanged.
