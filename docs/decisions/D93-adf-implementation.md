# D93 — Own ADF implementation, statistic only, anchored against statsmodels

**Status:** Committed
**Date:** 2026-07-14
**Category:** Validation & research integrity
**Source:** Implementation session (study v2)

## Decision

`research/cointegration.py::adf_stat` implements the Augmented Dickey-Fuller
t-statistic directly (numpy lstsq: Δs_t on s_{t−1} plus lagged differences, no
constant — the Engle-Granger-residual convention, since step-1 residuals are
mean-zero by construction). **No p-values, by design**: D29's rule is
rank-and-take-top-N, never threshold on significance, so only the ordering statistic
is needed — and the MacKinnon critical-value machinery (the part of an ADF
implementation that would justify a heavy dependency) is unnecessary for ranking.

**External anchor**: statsmodels 0.14.6 installed cleanly as a dev-dependency
against pandas 3.0.3, and `tests/unit/test_cointegration.py::
test_adf_matches_statsmodels_exactly` ties our statistic to
`adfuller(series, maxlag=k, autolag=None, regression='n')` at 1e-9 relative
precision across seeded series — a reference we didn't write, per the house X-test
discipline (D41/D79/D83/D86). Property tests additionally pin the behavior that
matters for selection: a stationary AR(1) scores decisively below −5 while a random
walk stays above −2.5.

## Rationale

A 40-line numpy implementation whose every output is checked to float precision
against the reference beats importing the reference into production: statsmodels
stays a dev-dependency (test-only), the production path has no hidden estimation
choices (autolag heuristics, trend terms) that a reader would need statsmodels
documentation to understand, and the rank-only design keeps the D29 discipline
structurally — there is no p-value anyone could be tempted to threshold on.
