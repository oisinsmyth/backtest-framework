# D528 ADDENDUM 15 — the retrace stop on the decoupling, and a window artefact larger than the edge

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D528-ADDENDUM-15-the-retrace-stop-on-the-decoupling-and-a-window-artefact-larger-than-the-edge.md`. The H1 above is the full title.*

Date: 2026-09-15. Runners: `working/d528_decouple_retrace.py`, `d528_tod_probe.py`.

**Nothing admitted (R15). Reserved slice NOT read.** Wide 5-minute fixture, 2010 → 2026-04-10,
corrected chain. Out of time throughout: forecast fitted on days < 2020-01-01, every figure on
days ≥ 2020-01-01. Both lenses, as the principal asked. Design enumerated as E1–E11 and the
confounds as R1–R6 in the runner's docstring, printed beside the result.

`limit_bounce` was drafted and removed at the principal's instruction. Recorded because the
reading matters: for a short at the high extreme a sell **limit** must sit at or above the market,
so an order filling on a downward retrace cannot be a resting limit — it is a **stop**, which
becomes a market order and crosses. Every fill here pays the full crossing plus $3.00.

---

## 1. The room mask was wrong in the direction, and the guard caught it

The first build reserved `max(W)` bars at the **end** of each session for a window that looks at
the **beginning**. A backward-looking grace window consumes bars *before* the signal, so nothing
forward needs reserving for it. That mask kept only the session's **first 14 candidate bars** —
precisely the bars whose look-back is truncated by the open, which is the confound the reservation
existed to remove. The REQUIRED-OUTPUTS guard added in ADDENDUM 14 refused to print: 30 of 96
declared cells came back under 200 rows. Corrected to a **trailing** reservation of `STALE + TAU`
(the trade's own requirement) and a **leading** exclusion of `max(W)` (a complete look-back at
every eligible bar), both asserted per session.

`d528_decouple.py` carries the same defective mask, so ADDENDUM 14's `fresh` arms were measured on
the session's first 24 bars with truncated look-back. That biases the grace effect **downward**, so
its "unresolved, marginal trades slightly better" reading understates rather than overstates.

## 2. The finding that matters: the measurement is window-sensitive by more than the effect

Correcting the mask moved the eligible signal bars from session bars 20–44 to 40–54, and the
comparable micro cell went from gross **−$1.11 to −$3.23**. Two explanations were possible — a real
time-of-day gradient, or two builds that simply are not comparable. Both were tested.

**The builds are comparable, proved on their overlap.** Session bars 40–43 are in both masks:

| universe | build | n | gross $ | median | P(target) |
|---|---|---:|---:|---:|---:|
| micro | ADDENDUM 14 | 317 | −2.96 | −8.0 | 16.7% |
| micro | corrected | 317 | −2.96 | −8.0 | 16.7% |

Bit-identical. So the entire difference is bar position.

**But time of day does not resolve.** Splitting ADDENDUM 14's own window four ways, block
bootstrapped over (root, day), micro:

| arm | late − early | SE | boot p5 | boot p95 |
|---|---:|---:|---:|---:|
| `noforecast` | **+0.46** | 1.31 | −1.65 | +2.61 |
| `fresh_q25_w0` | **−1.89** | 2.27 | −5.62 | +1.67 |

Neither resolves, and they disagree in sign. **My hypothesis that the edge is concentrated near
the open is not supported and is withdrawn.**

**What is established is worse than a gradient.** The same construction, same cost line, same
universe, same stop convention, reads **−$1.11 or −$3.23 depending on which fourteen to twenty-four
bars of the session it is measured on.** That $2.12 swing is **three to seven times the forecast
edge being chased** ($0.30–0.62 across the study). It is not a defect in the retrace order; it is a
statement about every per-trade figure D528 has produced at this resolution. Note also that the
detector's 2H warm-up means **session bar 20 (~11:10 ET) is the earliest bar this study has ever
been able to trade** — the opening hour has never been in the sample at all.

## 3. The grace-window axis is degenerate on this fixture — not underpowered, degenerate

With a 20-bar leading exclusion and a 30-bar trailing reservation, an 84-bar session leaves
**fourteen eligible signal bars**. The consequence is visible in the signal counts:

| W | signals (micro, q25) | every reported statistic |
|---|---:|---|
| 0 | 1,334 | |
| 10 | 2,201 | |
| 15 | **2,221** | identical to W=20 |
| 20 | **2,221** | identical to W=15 |

W=15 and W=20 select the same bars and produce identical numbers to two decimals. **The principal's
{10, 15, 20} ladder cannot be distinguished on 5-minute bars**, and no amount of data fixes it:
every reservation is denominated in bars and the session is only 84 of them. A 390-bar 1-minute
session leaves ~320 eligible signal bars — a **23× gain on this exact design**, against the ~5× a
bar count alone suggests. This is the one construction in D528 the 5-minute fixture *structurally*
cannot answer.

## 4. The retrace stop itself: conservation of hit × payoff, for the sixth time

Micro, X=2.0, out of time, path-invariant. `ysig → yfill` measures R4 directly:

| cell | fill% | n | P(tgt) | win% | ysig | **yfill** | gross $ | net $ | ctl gross | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market, q25 w0 | 100% | 1,334 | 15.7% | 22.3% | 3.07 | 3.07 | −3.23 | −7.81 | −2.45 | −0.78 |
| stop_retrace 0.25, q25 w0 | 74.2% | 990 | 24.8% | 29.1% | 3.14 | **2.10** | −3.63 | −8.18 | −4.44 | **+0.81** |
| stop_retrace 0.50, q25 w0 | 69.9% | 933 | 25.9% | 30.5% | 3.16 | **1.99** | −3.75 | −8.29 | −4.93 | **+1.18** |
| market, q10 w0 | 100% | 607 | 17.5% | 25.2% | 3.22 | 3.22 | −2.60 | −7.18 | −3.28 | +0.68 |
| stop_retrace 0.50, q10 w0 | 69.7% | 423 | 27.9% | 33.6% | 3.34 | **2.11** | **−1.38** | −5.93 | −1.58 | +0.20 |

**37% of the excursion is surrendered to obtain the confirmation** (3.16σ → 1.99σ). P(target) rises
1.65× and the win rate by 8 points, exactly as designed — and gross is *worse* at q25 (−3.23 →
−3.75) and better at q10 (−2.60 → −1.38). The dial moved; the product did not. That is the sixth
appearance of the conservation law, after the stop ladder, the geometry sweep, the forecast, the
confirmation entry and the depth sweep.

**One consistent pattern is worth recording.** `stop_retrace` beats its count-matched control in
**every** q25 cell (+0.47 to +1.18) while `market` **loses** to its control (−0.25 to −0.78) — the
forecast picks better bars for a confirmation entry than for a market entry. But every gross is
negative, and "beats the control" is empty below zero, so this is a direction to remember, not a
result.

## 5. Both lenses, and the opportunity cost is negative

Path-variant leg reuses `d528_book_and_sides.run_book` unchanged (same slots, same
one-position-per-root rule, same `er_usd` ranking); the perf mirror changes only the session
denominator to `total_bars // 84` for this clock, and its guard is kept and proved to raise
(self-test [6]). Micro, X=2.0:

| cell | slots | n | expo | gross $ | net $ | win% | hold | Sh_g | Sh_n | maxDD | ×limit |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| market q25 w0 | 1 | 998 | **0.3%** | −2.63 | −7.27 | 22.1% | 5.0 | −0.22 | −0.60 | 7,382 | 3.7× |
| market q25 w0 | 3 | 1,287 | 0.1% | −3.25 | −7.83 | 21.2% | 5.1 | −0.30 | −0.71 | 10,094 | 5.0× |
| stop_retrace 0.50 q25 w0 | 1 | 769 | 0.2% | −3.39 | −7.96 | 25.1% | 3.8 | −0.36 | −0.80 | 6,125 | 3.1× |
| market q10 w0 | 3 | 598 | 0.1% | −2.77 | **−7.36** | 23.9% | 5.0 | −0.21 | **−0.53** | 4,455 | **2.2×** |

Three things the two lenses say that neither says alone:

1. **The ranking is worth about half a dollar a trade.** market q25 w0: per-trade net −7.81,
   book at 1 slot −7.27 → **+$0.54** from `er_usd` selection. stop_retrace 0.50: −8.29 → −7.96,
   **+$0.33**. That is the only positive contribution measured in this addendum, and it is an
   allocation effect, not a signal one.
2. **The marginal slot is negative.** 3 slots is worse than 1 in every cell (−7.83 vs −7.27).
   Opportunity cost here is negative: the second and third positions are worse than idling.
3. **Exposure is 0.1–0.5%.** With 14 eligible bars a session and one position per root, the book
   is in a trade essentially never. A book that is on 0.3% of the time cannot be a component at
   any Sharpe, and the best cell is still Sharpe −0.53 with a drawdown **2.2× the $2,000 trailing
   limit**.

## 6. Disposition

1. **The retrace stop adds nothing on top of the decoupling.** It works mechanically — P(target)
   1.65×, win rate +8 points — and surrenders 37% of the move to get it. Sixth conservation result.
2. **The grace-window ladder is unanswerable on the 5-minute fixture** and no further 5-minute run
   should be spent on it. W=15 and W=20 are the same experiment.
3. **The window artefact is the binding problem, not cost.** A ±$2 sensitivity to which fourteen
   bars are measured swamps a $0.3–0.6 edge. Until that is reduced, no per-trade figure in D528
   distinguishes the constructions being compared.
4. **The 1-minute fixture is now the only sensible next step on this axis** — 23× on this design,
   and it also opens the first 100 minutes of the session, which D528 has never been able to trade.
5. **No component line, no promotion.** Best micro book: Sharpe −0.53, maxDD 2.2× the limit,
   exposure 0.1%. The axis remains the principal's to close.

**Withdrawn in this addendum:** my hypothesis that the reversion edge is concentrated near the
session open. The time-of-day split does not resolve and the two arms disagree in sign.

**Outstanding for the principal:** whether the reserved slice (2026-04-11 → 2026-09-09) is
considered spent after five months of it were read in the ADDENDUM 12 defect.
