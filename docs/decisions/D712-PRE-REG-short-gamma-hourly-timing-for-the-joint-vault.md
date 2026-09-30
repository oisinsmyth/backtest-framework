# D712 PRE-REGISTRATION — the hourly continuation on ES-book short-gamma days, for the joint vault run: its side choice (the timing term) is the primary, MES net the second gate

*2026-09-30.*
- *The principal, after [D708](D708-STAGE-0-RESULT-the-side-choice-is-the-signal-not-the-drift.md): "Yes, write it"
  (the joint-vault pre-registration, on the timing term as the gate).*
- *Numbered D712. D711 is the other session's, and it confirmed 712 is free and that programme slot 10 is free on its
  side.*
- ***Committed alone, before its runner exists.** Nothing in this record reads a price dated 2024-01-01 or later.*

**What this record does.**
- It registers D708's rule as one family for the **joint vault run** (AITODO's programme rule, A10), scored on data the
  rule has never seen.
- It writes the construction down completely (§1).
- The runner comes next, `scripts/vault_d712_short_gamma_timing.py`. It reproduces D708 in-sample exactly, computes the
  power and freezes the rule (the hashes and known answer, as D707).

## 0. The ruling and the selection path

**D708's verdict: SIGNAL, GO for a joint-vault pre-registration.** All five gates passed. The principal's objection
("it is always on, it's not really a signal?") was answered by the numbers: the side choice earns +$3.09 a MES trade
over the time-matched drift, on both legs. The drift is 2% of the profit.

**The selection path, disclosed in full:**

| step | record | what was chosen |
|---|---|---|
| 1 | D684 | short-gamma continuation at 30–60 minutes beyond volatility, post hoc |
| 2 | D689 | the hourly grid (h = 60, k = 0, 10:30–14:30) on G_SUM-short days; its V1 volatility-matched null priced it (98.5th) |
| 3 | D690, D692 | oracle profiles of the grid. The ES-book cells were the strongest (SPX ≥ 0, ES < 0: +$3.68, t 4.00) |
| 4 | D693 | a per-cell MES filter, anti-calibrated (not carried) |
| 5 | D706 | the unseen short-gamma counts (conditioner only) |
| 6 | the five-agent round, proposal E | the ES book alone as the gate, for its unseen count |
| 7 | D708 | the timing term; priced by its day-rotation null (99.9th) and the gamma-label null (99.8th) |
| 8 | this record | carried to unseen data on the principal's word |

- **The switch from G_SUM to the ES book (steps 3 and 6) is not priced by any null.** It was read off a profiled table.
- **So D708's +$3.09 is an upper estimate.** §5 states the power at 100%, 50% and 25% of it.

## 1. The construction, in its entirety

### 1.1 Instrument and data

| item | value |
|---|---|
| instrument | **ES**, traded as **one MES** ($5 a point) |
| price data | `data/fixtures/fut_ES_rth_1m.csv.gz`: one-minute RTH bars (`day`, `hhmm` = bar START, ET, `open`, `close`, `contract`) |
| session | an ES session with **at least 380 one-minute bars** in `fut_index_sessions.csv.gz` (D581's calendar) |
| grid (D689) | P(09:30) = the open of the 09:30 bar; P(hh:mm) for later grid points = the close of the bar starting one minute earlier |
| the gamma label | **G_ES**, the ES options book's dealer gamma at the prior settlement (D581's Black-76 on `fut_es_options_eod.csv.gz`, open interest keyed before 10:00, D688's construction), computed exactly as D706's `count_slice` does |
| the population | sessions with G_ES < 0 |

### 1.2 The signal and the trade

| item | definition |
|---|---|
| decisions | t = 10:30, 11:30, 12:30, 13:30, 14:30 ET |
| signal | m = 10⁴ · ln(P(t) / P(t − 60)) in bp |
| side | s = sign(m). **m = 0 is no trade** |
| hold | 60 minutes, from P(t) to P(t + 60). Time exit only; no stop, no target. **The last exit is 15:30** |
| size | one MES |
| gross | s · (P(t + 60) − P(t)) · $5 |
| cost | **$4.42 a round trip** (D685's `cost_spec("ES", "micro")`, as D689 and D708) |
| net | gross − $4.42 |

A decision needs finite P(t − 60), P(t) and P(t + 60), and **(A1) every 5-minute grid price from the open to t finite**.

**Amendment A1 (2026-09-30, before the runner exists).** D689's and D708's trade rows also required a finite log of
the day's realised variance to t, `lrv`, so a missing 5-minute grid price anywhere from the open to t drops the
decision. The drift μ's rows did not need it.
- A count, with no outcome read, found this binds on **17 of 10,115** in-sample decisions (2016–2023).
- The rule keeps the condition, so that D708's trades are reproduced exactly (§6). It is a data-quality rule, not a
  signal.
- The drift μ still uses every row with finite P(t − 60), P(t) and P(t + 60), as D708 did.

### 1.3 The timing term (the primary statistic)

- **The drift:** μ(y, t) is the mean dollar move x = (P(t + 60) − P(t)) · $5 over **every** decision row of the
  population at clock t in calendar year y, both sides, m = 0 included. It is computed within the scored span, from
  that span's own population rows.
- **The timing residual:** τ = s · (x − μ(y, t)).
- **T:** the mean of τ over the span's trades, with a day-clustered t (OLS on a constant, clusters = sessions).
- **The legs:** the long leg is the mean τ over s = +1, and the short leg over s = −1.

### 1.4 In-sample, as scored by D708 (2016-01-05 → 2023-12-29, D688's panel)

| | value |
|---|---|
| days / trades | 858 / 4,240 (4.94 a day) |
| **T** | **+$3.0925 a MES trade, t 3.17** |
| long / short leg | +$2.98 / +$3.22 |
| raw mean of s · x | +$3.16 (t 3.22) |
| MES net, daily Sharpe (Sortino) | −0.45 (−0.62); gross +1.14 (+1.73) |
| long-gamma days (the contrast) | T −$0.18 (t −0.38) |
| nulls | day-rotation p95 +$1.68 (99.9th); gamma-label p95 +0.93 bp (99.8th) |

## 2. The unseen data

**One look, in the joint run:** every population session from **2024-01-01 through 2026-09-18**.

| part | span | status for this trade |
|---|---|---|
| the held slice | 2024-01-01 → 2025-02-28 | **unread for this trade.** D689 and D706 read only its gamma label (no ES bar, price or return). Other ES constructions have read these bars; none selected this rule |
| the vault | 2025-03-01 → 2026-09-18 | sealed; read only in the joint run (A10) |

- **D706 counted the population's size without reading any price:** 101 ES-book-short sessions in the held slice and
  187 in the vault to 2026-09-09. That is **288 sessions, about 1,420 trades**.
- **The fixtures end 2026-09-09.** The last seven vault sessions are missing, and the runner counts them.
- **Both parts are read together, once.** Scoring the held slice first would be a second look.

## 3. The test

**On the trades in §2's span:**

| verdict | condition |
|---|---|
| **PASS** | at least 300 trades; **T > 0 with one-sided day-clustered t ≥ 1.2816**; both legs > 0 (point estimates); **and the MES net mean > 0** (point estimate) |
| **MECHANISM ONLY** | the T and both-leg conditions hold, and the MES net mean ≤ 0 |
| **FAIL** | at least 300 trades, and T's condition or a leg's fails |
| **UNRESOLVED** | fewer than 300 trades |

- **Programme promotion** is flagged separately at one-sided t ≥ 2.576 on T, the family's α slot.
- **The slot:** 10, the last free one (confirmed free by the other session). It is registered at freeze time.
- **The statistic is a t with its own standard error.** No input-rotation null gates the test. D711-A1 found that a
  rotation of inputs against fixed outcomes is anti-conservative on a mean statistic when the rule selects large days;
  that does not arise here.
- **Why the bar is 1.2816 and not 2:** the programme's joint-run bar (D680, D707) is a one-sided 10% test per family,
  with promotion at 0.5%. This record keeps it.

## 4. Reported beside the verdict, never gating

- **The two parts separately:** the held slice and the vault, each with its count, T and t.
- **The mechanism contrast:** T on the span's long-gamma sessions (G_ES ≥ 0), which should be near zero. If it is at
  least the short-gamma T, the reading carries the qualifier "(not gamma-specific)".
- **The two sub-populations:** G_SUM-short and G_ES-short-only. Their SPX GEX label is computed only if the SqueezeMetrics
  series covers the span. Otherwise the split is "not computable", stated.
- **All four groups at one MES and one full ES, net and gross side by side:**
  - Sharpe with Sortino, daily;
  - max drawdown, hit rate, median, payoff, skew and kurtosis;
  - the 1% trims: ex-top, ex-bottom, both;
  - by year, by clock, long against short.
- **The one-year question D705 failed on,** in both units: the largest calendar year's share of the dollar net, and
  T by year.
- **The price question:** gross in $ and in bp, and the round trip in bp at the span's prices.
- **The always-long control** on the same windows.
- **The component line:**
  - net daily Sharpe at one MES with its monthly block-bootstrap SE;
  - hit, skew, gross beside net;
  - ρ with the admitted MACD arm, and with F2, wherever each has a daily P&L on the span. F2's clock starts at 15:30,
    where this rule's last exit falls: adjacent, never overlapping.

## 5. Power (a rough estimate now; the runner computes it before the freeze)

**From D708 (§5):** per-trade signal-to-noise 0.052 (crash excluded), a cluster factor of 1.01, about 1,420 unseen
trades.

| effect kept | expected t | PASS on T alone (t ≥ 1.2816) | promotion (t ≥ 2.576) |
|---:|---:|---:|---:|
| 100% (+$3.09) | ≈ 1.98 | ≈ 0.76 | ≈ 0.26 |
| 50% | ≈ 0.99 | ≈ 0.39 | ≈ 0.06 |
| 25% | ≈ 0.49 | ≈ 0.22 | — |
| 0% | 0 | 0.10 by construction | 0.005 |

**The net condition lowers PASS.** At the span's prices (ES about 4,700–6,900) the round trip is 1.3–1.9 bp against
D708's mean gross of about 1.8 bp. The runner states the joint probability.

**The runner's `--power` states three things:**
1. **The test's size:** 20,000 draws of 288 sessions, resampled with replacement from D708's in-sample population
   sessions, with every session's τ demeaned to a zero total. The share with t ≥ 1.2816 must be **at most 0.12**.
2. **The power, by the same resampling:** τ is shifted so that its mean is 100 / 50 / 25 / 0% of D708's. It reports
   the PASS rate on T and legs, and the joint rate with the net condition at the span's projected price levels (gross
   in bp × the $ value of a bp at ES 5,800, the unseen span's approximate mid, against $4.42).
3. **Contiguous windows:** in-sample windows of 288 population sessions, starting every 10, scored with the full rule
   (the drift re-estimated within the window by year). The 0% line will not read 0.10; it shows time concentration
   and is reported, not gated.

**The rule, written now:** if check 1 fails, the test is miscalibrated, nothing is frozen, and the principal is told.
Otherwise the rule is frozen on the principal's ruling, whatever checks 2 and 3 say.

## 6. Prerequisites for the vault look

1. **The inputs are on disk to 2026-09-09.** `fut_ES_rth_1m.csv.gz`, `fut_es_options_eod.csv.gz`, the settlement strip
   and the session calendar. No vault-input build is needed.
2. **The vault frame is built without D688's panel.** The panel needs SqueezeMetrics GEX and LETF AUM, which this rule
   does not use. So the runner has two paths:
   - **the D708 path** (D688's panel), for the in-sample known answer;
   - **the rule path** (ES sessions ≥ 380 bars, G_ES from D706's `count_slice` machinery, D689's grid), which is the
     frozen rule and the one scored on the span.
   - **Path equality:** on D708's panel days the rule path's trades, sides, moves and τ equal D708's exactly. The
     rule path's own in-sample T, on its own day set, is the frozen known answer.
3. **Prefix stability:** in `--vault`, the rule path's in-sample part is rebuilt on the extended inputs and must equal
   the frozen known answer (trades, sessions hash, T) before a single unseen trade is scored.
4. **The freeze** holds:
   - the sha256 (LF-normalised) of this record, the runner and every script whose functions it calls (D688, D689,
     D708, D706, D581);
   - the fixtures' sha256, for information;
   - the known answers and the power figures;
   - slot 10 registered.
5. **The principal's word** for the joint run, on the command line.

## 7. The runner's assertions (each shown to raise in `--selftest`, or proved in `--known-answer`)

- **Known answers:**
  - D688's β_G;
  - D708's P_ES T (+$3.0925…, 4,240 trades, t 3.17…) through D708's own functions;
  - the rule path equal to the D708 path on D708's panel days, trade by trade.
- **Lag:**
  - D708's lag audit (a second implementation from the raw 1-minute bars) on 40 sampled decisions per span;
  - a canary that takes the side from the outcome hour must raise.
- **The gamma label is prior-only:** open interest keyed before 10:00 and the prior settlement, as D706 asserts. A canary
  that reads the same-day settlement must raise.
- **Sign, in money:** a favourable move pays long and short positively. τ of a trade whose move equals the drift is 0.
- **The seal:**
  - in every mode except `--vault`, no session ≥ 2024-01-01 reaches the rule path's bars;
  - `--vault` refuses without the principal's word, the freeze verifying (every hash) and a first opening. A second
    opening is refused.
- **The statistic, on synthetic data:** an injected timing effect PASSes; a pure drift fails T; noise PASSes about 10%
  of the time; fewer than 300 trades reads UNRESOLVED.

## 8. Predictions (about the unseen span, checked only in the joint run)

1. **T is positive but below the in-sample +$3.09.** The unpriced switch to the ES book implies shrinkage.
2. **Both legs are positive.** The short leg's raw gross stays small (in-sample +$1.82), because the drift is against
   it.
3. **Long-gamma sessions show T near zero.**
4. **The MES net is within about $1 of zero either way.** The price level helps (the round trip is fewer bp), but the
   gross is small.
5. **ρ with the MACD arm stays below 0.1 in absolute value.**

## 9. The ledger

- **D708's component line is in `docs/COMPONENTS_PROP.md` as "SCORED, NOT ENTERED".** At MES in-sample, C-a fails
  (net Sharpe −0.45).
- **This record does not enter it.** It is carried to unseen data as a mechanism with a thin net, on the principal's
  word. A PASS with the net condition would put it in front of the principal for entry. MECHANISM ONLY would not enter
  it at MES.
- **Disclosure:** this rule and V1 (D699) trade the same days and trend in the same direction. D699 is not carried, so
  the two are not counted as two confirmations.

## WITHDRAWN, 2026-09-30, before any look, on the principal's word

The principal: "Did I tell you to add E to the 10th slot? We can't afford to trade on ES so it doesn't matter if its
profitable there". And: "Park C while we look into E."

**What was undone:**
- **Programme slot 10 is unregistered.** `data/programme_registry.json`, `docs/results/PROGRAMME_REGISTRY.md` and
  `tests/unit/test_programme.py` are restored to their state before `6bcbd793`. Slot 10 is free again.
- **The freeze file** `data/FROZEN_vault_d712_short_gamma_timing.json` is removed. It stays in history at `6bcbd793`.
- **The runner and its power output** stay in the repo as evidence.

**Why it is a withdrawal, not a release:** no unseen data was read, and the family was never evaluated. So this is not
the registry's `release` (which bars a family from being registered again). The rule can be pre-registered again,
changed or unchanged.

**What was wrong with the registration:**
- **The account trades micro contracts only.** D708's rule nets −0.45 (daily Sharpe) at one MES in-sample, and only
  2023 nets positive. Its positive full-ES line is irrelevant to this account.
- **§3's MES net gate** rested on a projection at the unseen span's prices, not on an in-sample MES result.
- **It spent the programme's last α slot** without the principal being told that it was the last one, or that the rule
  loses at the size the account can trade.

**What stands:** D708's in-sample finding stands: the side choice carries +$3.09 a MES trade over the drift, on both
legs. What follows is the principal's "look into E": its economics at MES.
