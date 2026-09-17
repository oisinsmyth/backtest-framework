# D527 — the admitted arm fills at the **worst minute of the day**, and its crossing assumption is optimistic by 2.4×

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D527-the-arm-fills-at-the-worst-minute-of-the-day-and-its-crossing-assumption-is-optimistic-by-two-and-a-half-times.md`. The H1 above is the full title.*

*2026-09-14, on the principal's instruction to check the MNQ spread at the arm's entry timestamps.
Corrects the COST LINE of the ledger's ENTRY #2; the construction is unchanged and no code was
touched. Nothing new is admitted (R15). In-sample only — the spent 2024+ slice was not re-read.*

---

## The one-line answer

**The arm's 1.009-tick crossing is a market-wide average, and the arm does not trade at an average
moment: 66.6 % of its entries land at 10:00, where MNQ's quoted spread averages 3.66 ticks and is
one tick only 19.5 % of the time.** The measured round-trip crossing is **2.411 ticks**, the round
trip is **$4.21 rather than $3.50**, and the in-sample net Sharpe falls from **+0.724 to +0.661**
against C-a's bar of 0.5. **The entry stands; its cost line is amended.**

## 1. Where the arm actually fills

`d491_conditional_hold.simulate` fills at the **open of an hourly segment** and is forced flat at the
**close of h15**. It returns only `(pnl, trips)`, so the loop was re-implemented with the fill
segments recorded and **asserted bit-identical to the committed function** before its histogram was
believed — 1,876 sessions, 1,908 round trips, and the assumed-cost run reproduces **$15,423**, which
is D508's own figure for this window.

| | share of entries | measured spread | one-tick share |
|---|---:|---:|---:|
| **10:00** | **66.6 %** | **3.66 ticks** | **19.5 %** |
| 11:00 | 9.2 % | 1.79 | 48.2 % |
| 12:00 | 6.8 % | 1.49 | 57.3 % |
| 13:00 | 3.8 % | 1.52 | 56.1 % |
| 14:00 | 1.9 % | 3.35 | 54.0 % |
| 15:00 | 11.7 % | 1.46 | 61.0 % |
| **day-session baseline** | — | **1.61** | 51.4 % |
| **the forced flat, 15:59** (75 % of exits) | — | **1.44** | **63.7 %** |

**The concentration is structural.** The arm decides at h09's close and fills at h10's open; two
thirds of the time the signal already agrees at 09:59, so it enters at the first opportunity — which
is the worst quote of the day. **The arm systematically enters at the worst moment and exits at the
best**, because 75 % of its exits are the forced flat at 15:59.

10:00 and 14:00 are the two scheduled-announcement hours of the US session. That is a plausible
mechanism for the two spikes and it is **observed, not tested**.

## 2. The corrected cost

A taker pays half the quoted spread per leg. Entry-weighted **2.997** ticks, exit-weighted **1.825**
(75 % forced flat), so the round trip is `0.5 × 2.997 + 0.5 × 1.825 = 2.411` ticks.

| | assumed | measured |
|---|---:|---:|
| crossing, round trip | 1.009 ticks | **2.411 ticks** |
| round trip in dollars | $3.50 | **$4.21** (+20.3 %) |
| net per trade (gross $13.61) | $10.11 | $9.40 (−7.0 %) |
| **in-sample net Sharpe** | **+0.724** | **+0.661** |
| in-sample total | $15,423 | $14,086 |

The Sharpe is **re-run at the corrected cost, not scaled** — the approximation and the re-run happen
to agree to three digits here, but scaling assumes σ is untouched by a per-trade constant and that is
an assumption, not a fact.

## 3. What this does NOT establish — and the bias favours the arm

**tbbo spans 2025-09-11 → 2026-09-11 and the arm's window is 2016-2023. There is no quote data at the
arm's historical entries.** This prices the arm *today*; it does not reprice the backtest.

**And the error is one-sided.** NQ was ~4,000 in 2016 and is ~27,000 now against a **fixed $0.50
tick** — the tick was relatively **~7× coarser** then, and a coarser tick locks a market at one tick
more often. **The historical spread in ticks was probably tighter than measured**, so $4.21 is nearer
an upper bound on the in-sample cost than an estimate of it. The number bears on **deployment**,
where it is the right one.

Two notes on method, because both were choices:

- **Trade-weighting is correct here rather than a compromise.** The arm's fill *is* a trade print —
  the segment open is the hour's first trade — so weighting by trades samples exactly the moments
  the arm experiences. (For a passive participant the honest instrument would be `bbo-1m`, a
  time-weighted snapshot.)
- **The instrumented copy is asserted against the committed `simulate`**, and the window restriction
  is asserted to select a proper subset, so the spent slice cannot leak in through a date-string slip.

## 4. The generalisable point

**A cost assumption measured as a market-wide average is not the cost at the moments a strategy
actually fills, and the gap is not small: 1.61 ticks baseline against 2.997 at this arm's entries,
a factor of 1.9 — and 2.4× against the assumption in the ledger.** A strategy with a fixed clock
fills at *specific* minutes, and specific minutes are systematically wider or tighter than the
average for reasons (data prints, the close) that have nothing to do with the strategy.

**Measure the spread at the strategy's own fill timestamps, not across the session.** This one had
enough cover to absorb it — gross was 3.9× the assumed cost — but a construction whose gross is
1.5× its assumed cost would have been *reported as viable and been dead*, and nothing in the prior
process would have caught it.

**A mitigation is deliberately not taken.** Entering a few minutes after the hour, or skipping h10,
would avoid the worst quote. That is a **different construction**; this entry is admitted and frozen,
and it would need its own pre-registration rather than an edit to a row already in the ledger.

---

Recomputed by [`scripts/d527_arm_crossing_cost.py`](../../scripts/d527_arm_crossing_cost.py)
(`--spread`, ~14 min on the system interpreter; `--reprice`, seconds) into
[`data/d527_arm_crossing_cost.json`](../../data/d527_arm_crossing_cost.json). Ledger amendment at the
foot of [`docs/COMPONENTS_PROP.md`](../COMPONENTS_PROP.md).
