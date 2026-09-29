# D671 — STAGE 0 DESIGN (development): the break of yesterday's range with a day-size forecast and fixed-sign contraindication vetoes, on ES and NQ, root-specific in its details and one shape across roots

*2026-09-29.*
- *The principal: "Build that full construction and test it on ES/NQ allowing for root specific changes while keeping
  the general shape".*
- *The construction is the synthesis of the five analyst lanes (`docs/research/opening-break-predictor-lanes.md`,
  `db29902f`).*
- *It also builds on D681 and D668's development and oracle reads: `ab49940e`, `f82c859f`, `3f90b2a2`, `f769c43c`.*
- *Numbered D671 because the other session's unmerged branch holds D669 and D670. Its D670 names this plain-break line
  as an overlap.*
- *Committed alone, before its runner.*

## 0. What this is and is not

**ES and NQ are DEVELOPMENT.**
- Their in-sample (2016-01-04 → 2025-02-28) was read for this construction's ingredients: the open class, gap, gamma,
  TICK, A7, the weekday, the hour, the size-of-day oracle.
- **This run can build and describe the construction. It cannot confirm it.** No verdict is issued.
- Its output is the frozen form for a later pre-registration on YM and RTY, which have never been read for this
  construction, and for the vault's joint run.
- D668 is unaffected, and runs as registered.

**Every rule below is fixed now, before the runner exists.** Root-specific details are declared from a mechanism or
from D668's stability gate, never chosen after the run.

## 1. The shape (the same on every root)

1. **Direction:** D666's plain break. Stop orders at yesterday's RTH high + 0.25 A and low − 0.25 A, live from 09:30.
   The first fill of the day is taken, at the stop (or the open through it) + 1 tick; no entry after 15:29. A = D644's
   `atr20`.
2. **Exit:** E4. The initial stop sits at yesterday's level, then trails 0.25 A behind the best price since entry;
   otherwise flat at 15:59. **Variant E4w, reported only:** the trail is 0.375 A on the days in the size forecast's top
   tercile.
3. **A day-size forecast** (§2), made before the open.
4. **Hard skips:** calendar days, and a root-specific side veto (§3).
5. **A confluence score S** (§4). The contraindications count −1 and the confluences +1, each with its sign fixed.
6. **The trading rule:**
   - Trade the break unless a hard skip applies, **or S ≤ −1**, **or the size forecast is in its bottom tercile**.
   - **One micro. No sizing ladder.**
   - The same micro costs as D668 (`futures_costs.json`, `d508_exec`: $3 + crossing + one tick).

## 2. The day-size forecast (layer 3)

**Target, on EVERY usable session** (not only the break sessions): y = ln(R), where R = the session's RTH
(high − low) / A.

**Features,** all known by 09:29 ET, each with a declared sign:

| feature | definition | sign |
|---|---|---|
| g, dealer gamma | −(SPX GEX, the row dated before the session) / V20 (D663's V20). SqueezeMetrics, credited, never output per date. **The same measure on both roots** (lanes A and D) | + |
| overnight two-way range | (high − low of the session's Globex bars 18:00 → 09:29 − \|open − prior close\|) / A | + |
| rv5 | the mean of R over the 5 prior sessions | + |
| \|gap\| | \|open − prior close\| / A | + (for the day's range; its trade effect is handled as a contraindication in §4) |
| event day | CPI, employment situation or FOMC day (`cme_session_calendar`) | + |
| opex Friday | the month's third Friday | − |

**The estimator,** per root:
- walk-forward;
- refitted before every session on all earlier usable sessions, with a burn-in of 250 sessions;
- features standardised on the training rows and multiplied by their declared sign;
- **slopes constrained ≥ 0** (non-negative least squares on the demeaned data), with the intercept free.

No tuning. A feature whose fitted slope is 0 simply drops out.

**The tier:** the forecast's percentile among the root's own previous 250 forecasts (walk-forward). The bottom tercile
is < 1/3, the top > 2/3.

**Validation, reported before any trade result:**
- the out-of-sample Spearman of the forecast against y;
- the same for a persistence-only forecast (rv5 alone);
- an enumerated time-rotation null of the forecast against y, with offsets from 21 to n − 21, giving p50 and p95;
- the mean R by forecast decile (calibration);
- **P(hold) by forecast tercile on the break trades, which must be flat.** A spread above 0.08 between terciles
  is flagged as a directional leak.

## 3. Hard skips (layer 4)

| skip | ES | NQ | mechanism |
|---|---|---|---|
| FOMC day | yes | yes | the expansion comes at 14:00; a morning entry is trailed out in the lull (lane D) |
| monthly opex Friday | yes | yes | expiry gamma pins the day (lane A; Golez & Jackwerth 2012) |
| **short breaks** | **yes** | no | ES's short edge over its null is +0.85 bp against +3.2 long: dip-buying absorbs ES shorts. NQ's edge is two-sided (lane D). **Root-specific** |

## 4. The confluence score S (layer 5)

S = the sum of the terms that apply to the root. Each term is 0 or ±1, with its sign fixed. **The trade is vetoed when
S ≤ −1.**

| term | ES | NQ | definition (known at the entry) | mechanism |
|---|---|---|---|---|
| gap aligned | +1 | +1 | D × (open − prior close) > 0.10 A | the auction has accepted the overnight move |
| breadth aligned | — | +1 | D × TICK-NQ z (09:30 → the bar before entry, D663's definition) > 0.5 | NQ's leaders moving with the break. **Not on ES:** TICK-SP is arbitrage-linked (lanes B, D) |
| cross-index confirmation | +1 | — | the other root's close on the bar before the entry is beyond its own yesterday level on the same side | a complex-wide break is a re-pricing. **Not on NQ,** which leads (lane D) |
| overnight probe | −1 | −1 | the Globex high (for a long) or low (for a short), over 18:00 → 09:29, went beyond the stop level, and the 09:30 open is inside yesterday's range | the stops were run overnight, so the RTH break is a second break (lane C; D666/D681) |
| exhausted gap | −1 | −1 | the gap is aligned and \|gap\|/A is above the 80th percentile of the root's previous 250 sessions | the gap has spent the day's range budget (lanes C, E) |
| spent flow | — | −1 | D × A7 at the latest checkpoint at or before the entry is above the 80th percentile of \|A7\| at that checkpoint over the root's previous 250 sessions | the flow that made the break is spent (lanes B, A, D). **Not on ES:** its D668 sign stability was 0.66 < 0.8 (lane E's gate) |

## 5. What is reported (development, no verdict)

**The size forecast:** its validation (§2), per root.

**The ablation.** All on the same evaluation window: the sessions where the forecast tier exists, from about the
third year on. Each layer is added in turn:
- B0, the base break (D668's unfiltered);
- B1, + the hard skips;
- B2, + the S ≤ −1 veto;
- B3, + the size tier (**the construction**);
- B3w, with E4w.

For each: trades a year, gross and net, win rate, P(hold), $ a year per micro, daily Sharpe and Sortino, maximum
drawdown. **Each layer's removed trades' net is reported beside its kept trades.** A layer is worth keeping only if what
it removes loses.

**The placebo.** The construction against 1,000 random subsets of B0's trades of the same count, drawn within year so
the era mix is kept (seed 671). Reported: p50, p95 and the p95's bootstrap SE, and where B3 ranks.

**The four groups** for B0 and B3, and **the component line** for B3: daily $ Sharpe at one micro, ρ with the rebuilt K8
and between the roots.

**By year:** B0 against B3, trades and net.

**The score's parts:** the share of trades each term fires on, and the net of the trades each term alone would veto.

**The runner's assertions, each shown to raise in `--selftest`:**
- the size forecast uses earlier sessions only (a second implementation that selects by session date);
- the tier uses earlier forecasts only;
- the overnight features use bars before 09:30 only;
- the cross-index close is the other root's bar before the entry minute;
- A7 is taken at a checkpoint at or before the entry.

The runner also reproduces D668's development E4 gross exactly before anything else.

## 6. Expectations, written before the run

1. **The size forecast beats persistence alone.** Its out-of-sample Spearman is 0.20–0.35 on both roots, above the
   rotation null's p95.
2. **P(hold) is flat across the forecast's terciles** (within 0.08).
3. **NQ:** B3's net per trade exceeds B0's by 1–3 bp, at about 60% of B0's trades. Its $ a year are within ±25% of
   B0's, and its daily Sharpe is higher.
4. **ES:** B3 is still net negative, or within 1 bp of zero (the size oracle: ES needs Spearman ≥ 0.6 to break even).
5. **Against the placebo:** B3 ranks above the p95 on NQ, and not on ES.
6. **At least one veto term removes trades whose net is not negative.** It is recorded as a candidate to drop at the
   YM/RTY pre-registration, not dropped here.

## 7. Outputs

- `scripts/stage0_d671_break_construction.py`, with `--selftest` and `--run`;
- `data/stage0_d671_break_construction.json` (statistics only, licence-guarded);
- a RESULT record, crediting SqueezeMetrics.

**The frozen form goes forward to YM/RTY only through a separate pre-registration,** once D668's YM/RTY run is in.
