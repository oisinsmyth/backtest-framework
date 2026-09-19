# D563 — the time-series **trend** line and the **carry-timing** line on the futures fixtures are CLOSED by the principal, 2026-09-19

*Closed on the principal's word after D562's forward read ("This does not seem to have
sufficient edge" — "Close the trend and carry lines"). Nothing admitted (R15). This record
states what is closed, on what evidence, what it does not close, and what survives as
instruments. Under R15 a closure is the principal's; this is its record.*

---

## 1. What is closed

**The time-series trend line**: MOP's 12-month sign book on the 36-root breadth fixture and
every variant scored here — the 1m / 3m / 3+12 / 1+3+12 lookbacks (D555), the leverage-capped
books (D561 S2), the published return-space and minimum-size dollar forms — on any window of
these fixtures.

**The carry-timing line**: KMPV's sign of the front–next annualised basis on the same roots —
cells A (sign), B (demeaned) and C (trend + carry at equal weights) of D556 — and with it the two
carry-timing items still on the deposit's list: the continuous trend + carry forecast of
`PUBLISHED_STRATEGIES.md` §8 (which contains both closed signals) and a seasonal-adjusted carry
for NG and the grains (a carry-timing construction).

Operationally: no new pre-registration on either construction on these fixtures; their
`COMPONENTS_PROP.md` rows stand as scored (append-only); their 2024+ slice is already spent
(D562) so nothing containing them could be confirmed in any case.

## 2. The evidence, in one table

| | trend (12m published) | carry timing (cell A) |
|---|---|---|
| 2016–2023 gross Sharpe / Sortino | +0.30 / +0.43, rank 0.78 in its purged rotation null (p95 +0.95) — D555 | −0.20 / −0.28, rank 0.38, below the null's median — D556 |
| 2011–2023 | +0.46, rank 0.68; the 13-year null is as wide as the 8-year one (sd 0.51 vs 0.58) and its median moves to +0.11 — D561 S1 | +0.38, driven by 2011–2015 (+1.61); not nulled |
| **2024-01 → 2026-09 (forward, spent)** | **+0.51 / +0.71, rank 0.69** (null p50 +0.18, p95 +1.30); harness ρ 0.73 with AQR; the whole P&L is 2026 — D562 | **−0.56 / −0.82**; 2025 alone −1.69 — D562 |
| family / speed | ten cells, family best +0.34 at its N2 null's median — D555 | six cells, family best +0.25 at its N2 median — D556 |
| sizing | monotone: every cap lowers the Sharpe; the worst day is the same macro session at every cap — D561 S2 | — |
| concentration | 2–3 roots reach half the P&L on every window; top 1 % of root-months 86–111 % of P&L | 16 of 36 roots positive on 2016–2023 |
| role beside equities | +0.26 σ on ES's worst days in sample (rank 0.94, bar 0.95); **−1.29 σ forward, rank 0.05**, ρ with ES −0.13 → +0.31 — D561 S3, D562 | — |
| role beside each other | ρ 0.18 in the body; **−0.56 σ on carry's worst days, below all 1,562 rotations** in sample; −0.45 σ forward — D561 S3, D562 | same pair |
| vehicle at minimum size | σ $8,762 in sample, $10,920 forward; C-d sub-book +0.24 / −0.08; the dollar Sharpe is three full-size contracts — D555, D562 | σ $7,341; +0.20 is one contract of palladium — D556 |
| harness | ρ 0.815 with AQR in sample, 0.733 out: the construction is right — D555, D562 | G1–G4 gates green: the strip is right — D556 |

**The reading:** trend on this universe is a real, small, rare effect — one excess of about
+0.35 over a tilt-laden null on three windows, never above the 78th percentile, its P&L two
events per window — that hedges one shape of equity drawdown and amplifies the other, and has no
vehicle at the account's size. Carry timing did not deliver on either window. The deposit's
combined book rested on their being uncorrelated, which holds in the body and fails on the days.

## 3. What this record does not close

- **The three cross-sectional sorts (D557 term structure, D558 12-1 momentum, D559 the double
  sort)**, all DOES NOT PASS on 2016–2023 with their 2024+ slice unread. D557 and D559 rank on the
  same `carry_ann` the closed carry-timing line signs on, cross-sectionally rather than in time;
  the principal's word covered the two lines named, and this record leaves the sorts' status as
  scored. If the closure is meant to reach them, it is a one-line addendum here.
- **The other published futures premia the deposit itself names and parks** (§0 of
  `PUBLISHED_STRATEGIES.md`): hedging pressure (Basu–Miffre, on COT positioning; the legacy report is on disk as `cftc_cot_raw`, 28 symbols, 1986 → 2026-08, commercial / non-commercial split),
  basis-momentum (Boons–Prado, `BASIS_MOMENTUM.md` is a pre-registration draft; the settlement
  strip already holds every listed month), commodity skewness and commodity value. None has been
  tested here; none is closed by this record.
- **The fixtures and the harness**: the breadth grid, the settlement strip, the curve table, the
  AQR monthly factor and the loader amendments stay, and are the calibration baseline the deposit
  asked for — the harness reproduced a published factor at 0.82 and 0.73 and is trusted for what
  comes next.

## 4. What survives as instruments

1. **The purged rotation null** (D555 §2): offsets within a lookback of either cycle end are
   look-ahead or stale momentum; store the offset profile.
2. **The null's median is tilt, not zero** (D561 S1, D562): +0.11 / +0.18 on the Sharpe and −0.68
   / −0.55 σ on equities' worst days. A name-randomised null would separate it from timing;
   still unrun, still recommended for any persistent-sign book.
3. **A longer window does not buy power** for a persistent-sign book; more independent
   instruments might.
4. **ρ is a body statistic.** Any pair considered for the components ledger carries the overlay's
   mean on the base's worst 5 % of days, in the overlay's σ, and the vol-matched blend's drawdown
   ratio, each against the overlay's rotation null, beside C-b's ρ (D561 S3, D562 §4).
5. **The one-contract dollar book across roots is a bet on the largest dollar σ**: decompose by
   root before quoting a component line (D556, D562).
