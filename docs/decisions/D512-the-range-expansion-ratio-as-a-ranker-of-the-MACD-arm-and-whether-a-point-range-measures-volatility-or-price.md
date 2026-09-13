# D512 — the range-expansion ratio, log(EMA50(range) / SMA200(range)), as a ranker of the MACD arm — and whether a point range measures volatility or price

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file.
**In-sample 2016-01-04 → 2023-12-29 only**; the arm's 2024+ slice is SPENT (D503) and is not scored.

## 0. The standing limitation, unchanged

The arm has **no unread slice on NQ** (D503). As in D508 and D509, nothing here can be a discovery;
the ceiling is a measurement. Stated so no later reading mistakes a ranking for a licence to gate.

## 1. What this follows, and why it is not a repeat

**D502 declared a volatility-regime cell and left it as the one unresolved result on this arm.** Its
R3 was **20-session realised volatility against its own median**, applied as a **binary** gate:
`R3_GATE_LOWVOL` read **+0.352 against a rotation p95 of +0.353 — a margin of 0.0 SE, UNRESOLVED**,
and D502 called it *"the single cell worth re-reading, and the one whose in-sample motivation means
it deserves the least trust."*

**This record is that re-read, on a different and better-posed construction**, at the principal's
direction: a **continuous ratio of a fast to a slow average of the daily range**, rather than a
binary split of realised return volatility at its median. Different input, different windows,
continuous rather than binary.

## 2. The construction, and the flaw it must not have

The principal's construction is `log( EMA50(high − low) / SMA200(high − low) )` on daily bars.
**Taken literally in points, that measure is contaminated by the price level**, and this record
refuses to run it that way as the primary.

**Why.** NQ ran from roughly 4,500 to 16,000 over the window. A *point* range grows with the level
even at constant percentage volatility, and a 50-day average tracks that growth while a 200-day
average lags it. So `log(EMA50/SMA200)` of a point range is **positive whenever price has been
rising**, whatever volatility did. It would be a slow price-momentum measure wearing a volatility
label — the same price-level artefact D503 and D504 found in every pooled σ figure.

**The declared primary is therefore the scale-free range:**

- `r_d = log(high_d / low_d)` — the daily log range (Parkinson's), invariant to the price level.
- **`V_d = log( EMA50(r) / SMA200(r) )`**, both averages ending at **d−1**, so the conditioner is
  known before session d opens. EMA with span 50, α = 2/51; SMA over 200 daily values.
- Positive `V` = the recent range is wide against its own long-run level, volatility expanding.

**The principal's literal point-range version is run as a declared secondary**, beside a direct
measurement of the contamination: the correlation of each version with `log(price)`. If the point
version is a price proxy, that correlation shows it, and the record will say by how much.

**Which "daily bar".** The arm trades the day session, and D508/D509 built their conditioner on the
day-session close, so the primary uses the **day-session range** (`h09 … h15`). The **full 23-hour
session range** is a declared secondary, because "daily bar" could reasonably mean either.

**Four cells in the family:** {day-session, 23-hour} × {log range, point range}.

## 3. The primary statistic, one (R14)

**Δ = mean net P&L per session in the TOP quintile of `V` minus the mean in the BOTTOM quintile, in
dollars at one MNQ**, on the day-session log range. The same statistic as D509, deliberately, so the
three studies on this arm are directly comparable.

Reported beside it: the five-quintile shape in net and gross, gross per trade, trades per session,
hit, worst day and P3a per quintile, and the monotonicity of the quintile means.

## 4. Nulls and controls

- **N1, exact enumerated rotation** of `V` against the arm's P&L, re-forming the quintiles at every
  offset, ≈ 1,875 offsets, p95 sampling error exactly zero. **As D509 proved, this subsumes a
  hand-built run-length-matched persistent gate**: rotation preserves the duty cycle and the
  run-length multiset exactly. No separate matched-gate band is built.
- **N2, family maximum** over the four cells under common offsets.
- **N3, the within-year decomposition.** Δ inside each calendar year. D508 and D509 both found the
  200-day stretch reversed sign between pooled and within-year (−$10.71 within against +$13.82
  pooled, negative in seven years of eight). A volatility conditioner is even more likely to track
  *which year it is*, since the arm's P&L concentrates in 2020 and 2022 and those are the volatile
  years. **This is the control most likely to decide the record.**
- **N4, the contamination measurement.** ρ(`V`, log price) for each of the four cells, and the same
  for the point-range versions specifically. Not a pass/fail gate; a number the record must carry.

## 5. Decision rule (pre-registered)

**PROCEED** — recorded, not acted on, since no unread slice exists — if Δ clears the N1 p95, clears
the N2 family p95, and keeps its sign within year. **PICK** if it clears N1 but fails N2 or N3.
**CLOSE** otherwise. The principal closes.

## 6. Predictions (checkable in the runner's quantities)

- **X-a** The **point-range** version correlates with log price at **ρ > +0.35**, and the **log-range**
  version at **|ρ| < 0.20**. The contamination is real and the scale-free form removes most of it.
- **X-b** Δ on the primary is **positive, between +$5 and +$25 a session** — the arm earns more when
  the range is expanding, because its P&L concentrates in 2020 and 2022.
- **X-c** The N1 rotation p95 is **wide, between +$20 and +$35 a session**, for the same reason it
  was in D509: a rotated volatility conditioner is a persistent gate that catches or misses whole
  regimes. **Δ does not clear it.**
- **X-d** The within-year mean Δ is **below +$5** and **negative in at least five of the eight
  years**, reproducing the pooled-versus-stratified reversal D508 and D509 both found.
- **X-e** The day-session and 23-hour versions agree within **$6 a session** on Δ; the choice of
  daily bar is second-order.
- **X-f** The verdict is **CLOSE**.

## 7. Files

This record · `scripts/run_d512_range_expansion.py` (`--run`, `--selftest`; imports the frozen arm
and D509's primary) · `data/d512_range_expansion.json` · RESULT (separate). Runtime seconds.
