# STRUCTURE_RESULTS.md — the structure programme's ledger

**Append-only.** Every work package adds a dated section; nothing above is rewritten. This
is the single results ledger `New Docs/STRUCTURE_MODEL.md` requires, and it carries the
multiplicity count that feeds the deflated Sharpe if the programme reaches WP5.

**What this programme tests:** whether the five components of a discretionary retail
day-trading strategy — change of character, the flipped level, the 61.8% Fibonacci
retracement, the fair value gap, and RSI — carry information about forward price behaviour
on BTC and ETH 15m bars, separately and in combination, once each is mechanised precisely
enough that a machine can find it without a human drawing the lines.

**Spec and pre-registration:** `New Docs/STRUCTURE_MODEL.md` (D204), committed before any
detector existed.

---

## Inherited disclosure — the terrain programme

The predecessor programme spent **259 looks** establishing that price-derived maps of
resting supply and demand carry no directional or reversal information on this data
(`TERRAIN_RESULTS.md`; S1 closed by D194, the S6 reversal line by D200, the S6 map by
D203). Its unifying mechanism was that **fading lost in every form measured** — 16 of 16
cells, 16 of 16, 8 of 8, and 11 years of 11.

Three of the five components tested here (the flipped level, the Fib retracement, the fair
value gap) are pullback-fade entries. **The prior for this programme is bad, and it is
stated here rather than after the result.**

That count is disclosed adjacent and is **not** added to this ledger — a different
construction and a different claim, per the condition `TERRAIN_RESULTS.md` closes with.
The one exception is pre-committed in Disclosure D1 of the spec: **if the flipped-level
component is the only survivor, D196's 20 looks are inherited into the total below**,
because in that world the two studies are reading the same swing structure.

---

## Multiplicity ledger — running

| Work package | looks |
|---|---:|
| WP0 pre-registration (no runs) | 0 |
| **Total** | **0** |

Never reset. Retired and failed cells count. Budget estimated in the plan at ~118 looks
for the full programme; the estimate is not a licence and the actual count is what feeds
the deflated Sharpe.

---

## WP0 — pre-registration

**Produced:** 2026-08-24 · **Reproduce:** n/a — no runs.

`New Docs/STRUCTURE_MODEL.md` written and committed, recorded as D204. It fixes, before
any code exists: the five mechanical definitions; the confirmation-lag requirement; the
pre-registered parameter sets and the named primary cell; the three hurdles with the
percentile-beside-the-delta requirement from D202; the per-WP stop conditions; seven
pre-registered predictions with confidences; and four disclosures — the S5/D196 overlap on
the flipped level, the zero-hit grep establishing the other components as new
construction, the statement that nothing has been seen, and D199's calibration note
capping baseline-relative predictions at moderate confidence.

**Looks: 0.** Nothing was run.

### Parking lot

Ideas raised and deliberately not in scope. Triaged between work packages, never mid-WP.

- A 5m fixture. The 486 MB of raw Binance 1m archives are already cached locally, so it is
  an offline re-run of `scripts/fetch_binance_fixture.py`. The course is explicitly a 5m
  strategy. Deferred because it doubles the multiplicity count and needs its own empty-bar
  census (5m's worst major-month rate is 3.34% against 15m's 0.32%), and because the rules
  are timeframe-agnostic as written.
- The `XEMUSDT` / `BTGUSDT` failure universe, already in the committed fixture. "A path
  tested only on majors is a path tested only where it works" (D140/D180). Deferred to keep
  the cell count honest; the caveat is stated rather than the test skipped silently.
- Daily bars as an independent-era cross-check on whether any surviving component is
  timeframe-general or an intraday artefact.
