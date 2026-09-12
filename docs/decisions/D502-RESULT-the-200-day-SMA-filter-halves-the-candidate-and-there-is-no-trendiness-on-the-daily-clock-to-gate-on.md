# D502 — RESULT: the 200-day SMA filter **halves** the candidate, the one cell that clears is an artifact of six traded sessions, and there is **no trendiness on the daily clock to gate on**

**2026-09-13.** Runner [`scripts/d502_daily_regime_confluence.py`](../../scripts/d502_daily_regime_confluence.py) ·
artifact [`data/d502_daily_regime_confluence.json`](../../data/d502_daily_regime_confluence.json) ·
pre-registration [D502 PRE-REG](D502-PRE-REG-an-orthogonal-daily-clock-confluence-on-the-hourly-MACD-the-200-day-SMA-regime-daily-trendiness-and-the-volatility-regime.md).
State machine from D491, signal code from D484, panel from D495 — all unchanged.

---

## 1. The headline, in one line

**Nothing that passes its own premise clears its own null**, and the principal's 200-day SMA
filter applied in the textbook direction takes the candidate from **+0.801 to +0.303**.

## 2. First, the good news: these conditioners ARE orthogonal

This is what D495's AGREE was not. **U-f held on every root**: the largest correlation between
any conditioner's state and the MACD's own sign is **|ρ| = 0.093** (ES/R1), and most are under
0.05. The three conditioners carry information the MACD does not. **The orthogonality the
principal asked for is real — it simply does not pay.**

## 3. Every cell improves NET and damages GROSS. That decides the reading.

| cell | net lift | **gross lift** | trips/session (plain 1.69) |
|---|---:|---:|---:|
| R1_GATE_UP | **+0.295** | **−0.692** | 0.93 |
| R1_GATE_DOWN | +0.131 | −0.856 | 0.76 |
| R1_DIR_ALIGN | +0.125 | −0.147 | 0.84 |
| R1_DIR_COUNTER | +0.225 | −0.052 | 0.88 |
| R2_GATE_TREND | +0.568 | −0.419 | 0.50 |
| R2_GATE_CHOP | −0.018 | −1.005 | 1.19 |
| R3_GATE_LOWVOL | +0.352 | −0.635 | 0.86 |
| R3_GATE_HIGHVOL | +0.089 | −0.898 | 0.83 |

**Eight cells, eight negative gross lifts.** Direction gets *worse* in every single one. The net
improvement is entirely the cost-cutting channel — not paying commission on sessions the signal
would have traded at a loss after cost. CLAUDE.md asks which moved, edge per unit exposure or
cost per trade: **it is cost per trade, in all eight.**

**And the null prices exactly that channel.** The rotation's **p50 is +0.13 to +0.25** — a
*random* persistent gate of the same duty cycle and run-length structure gains about +0.2 net
Sharpe for free. That is why the null had to rotate rather than shuffle, and it is why seven of
the eight cells sit inside it.

## 4. The one cell that clears is an artifact, and the premise caught it before the null did

| cell:arm | observed | null p95 | margin | verdict |
|---|---:|---:|---:|---|
| **R2_GATE_TREND:B2** | +0.660 | +0.426 | **+37.7 SE** | **NOT A TEST** |
| **R2_GATE_TREND:AGREE** | +0.568 | +0.430 | **+36.4 SE** | **NOT A TEST** |
| R2_GATE_TREND:B1 | +0.543 | +0.473 | +5.9 SE | **NOT A TEST** |
| R1_GATE_UP:B1 | +0.345 | +0.340 | +1.9 SE | **NOT A TEST** *and* UNRESOLVED (inside 2 SE) |
| R3_GATE_LOWVOL:AGREE | +0.352 | +0.353 | −0.0 SE | **UNRESOLVED** |

The runner prints the verdict itself, and it is the headline:

    NOT A TEST  R1_GATE_UP:B1         +1.9 SE   premise 2/8   min traded 613
    NOT A TEST  R2_GATE_TREND:AGREE  +36.4 SE   premise 5/8   min traded 6
    NOT A TEST  R2_GATE_TREND:B1      +5.9 SE   premise 5/8   min traded 6
    NOT A TEST  R2_GATE_TREND:B2     +37.7 SE   premise 5/8   min traded 6
    NOTHING that passes its premise on every root clears its null.

**R2 fails §5's duty-cycle premise on ES (7.7%), NQ (0.4%) and ZB (run 3).** §0d says what that
means in sessions:

    sessions R2_GATE_TREND actually trades   ES 117   NQ 6   YM 238 ... of ~1,600
    sessions the plain arm trades            ES 1,491  NQ 1,480  YM 1,468

**NQ's R2_GATE_TREND trades six sessions out of 1,625.** A Sharpe on a series that is 99.6%
zeros is not a Sharpe, and three such cells are what produced the family-max clearance. **The
pre-registered premise check is the only reason this is not being reported as a finding** — the
null was fooled and the premise was not.

## 5. And the reason R2 is degenerate is itself the answer to the question

The principal asked for a confluence that **complements momentum**. R2 was the attempt: a
momentum rule needs follow-through, and the variance ratio measures follow-through directly.

| root | median VR | p10 | p90 | share VR > 1 |
|---|---:|---:|---:|---:|
| ES | **0.869** | 0.672 | 0.987 | 7.4% |
| NQ | **0.839** | 0.669 | 0.921 | **0.4%** |
| YM | 0.932 | 0.849 | 1.035 | 15.5% |
| ZN | 0.885 | 0.795 | 1.116 | 25.0% |
| ZB | 0.922 | 0.775 | 1.146 | 28.0% |
| GC | 0.989 | 0.891 | 1.195 | 45.3% |
| CL | 1.001 | 0.820 | 1.103 | 50.3% |
| 6E | 0.949 | 0.823 | 1.472 | 32.3% |

**The median variance ratio is below 1 on seven of eight roots.** On the daily clock these
markets are mildly **mean-reverting essentially always** — NQ's 5-day variance ratio was above 1
in **0.4%** of sessions across 2017–2023. **There is no trendiness to gate on.** That is a
premise failure and not a result, and it is the honest answer to the question: the follow-through
a momentum rule wants is not a state the daily clock visits.

It also does **not** contradict [D471](D471-RESULT-the-spread-barely-widens-and-path-efficiency-is-the-random-walk-value.md),
which read the variance ratio at 0.82 → 1.00 on the **tick** clock at 1 s → 15 s. Different
clock, same conclusion from the other side: no follow-through above the random-walk value at
either end.

## 6. R1 — the principal's filter — fails on persistence, and the diagnosis is the boundary

| root | duty (above) | crossings/yr | median run above | below | **mean run** |
|---|---:|---:|---:|---:|---:|
| ES | 79.9% | 11.5 | 2 | 2 | 21.7 |
| NQ | 82.0% | **7.4** | 3 | 3 | 33.2 |
| YM | 81.7% | 10.6 | 11 | 2 | 23.5 |
| ZN | 41.5% | 8.1 | 3 | 4 | 30.3 |
| 6E | 38.3% | 3.0 | 6 | 30 | 80.3 |

**The dominant state is long-lived (mean run 22–80 sessions) and the boundary flickers** — 7 to
12 crossings a year. So the pooled-run median reads 2–4 and R1 fails §5's persistence
requirement on **6 of 8 roots**.

**My premise statistic was the wrong instrument for an asymmetric-duty regime**, and I am
recording that rather than swapping it: a median over pooled runs reads the flicker, not the
regime. But the verdict does not change, because the flicker is *real* — a gate on this state
stands the book down for one to three sessions dozens of times a year. **The obvious fix, a
hysteresis band around the SMA, is a new construction and not a re-read of this one.**

## 7. The candidate cell, which is where the principal's question gets answered

**Restated plain AGREE on the reduced window: +0.801** (D495's full-window figure was +0.723 —
see §9, this is a warning and not a bonus).

| cell | net | gross | trips/session | worst day |
|---|---:|---:|---:|---:|
| **plain (no filter)** | **+0.801** | — | 1.01 | −1,315 |
| R1_DIR_ALIGN — **the textbook filter** | **+0.303** | +0.510 | 0.48 | −987 |
| R1_DIR_COUNTER — its mirror | **+0.774** | +0.985 | 0.56 | −897 |
| R1_GATE_UP | +0.593 | +0.593 | 0.84 | −888 |
| R1_GATE_DOWN | +0.537 | +0.537 | 0.18 | −1,315 |
| R2_GATE_TREND | +0.409 | +0.409 | **0.00** (6 sessions) | −191 |
| R2_GATE_CHOP | +0.774 | +0.774 | 1.01 | −1,315 |
| R3_GATE_LOWVOL | +0.510 | +0.510 | 0.52 | −852 |
| R3_GATE_HIGHVOL | +0.617 | +0.617 | 0.50 | −1,315 |

**Two things to read off this table.**

1. **The 200-day SMA filter applied the canonical way cuts the candidate from +0.801 to
   +0.303** — it is the single most damaging thing tested. And **its mirror does better
   (+0.774)**, which is the signature of no information rather than of inverted information. The
   pre-registration put DIR_COUNTER in the family precisely so this would be legible as a sign
   artifact instead of a discovery.
2. **Not one of the eight cells beats the unfiltered candidate.** The best is +0.774 against
   +0.801.

## 8. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **U-a** | R1 duty 70–85% on NQ, and within [0.55, 0.90] on every root | **BROKEN** (2nd clause) | NQ 82.0% held; ZN 41.5%, ZB 44.2%, 6E 38.3% |
| **U-b** | R1_DIR_ALIGN does not clear | HELD | −57.0 SE |
| **U-c** | R3_GATE_LOWVOL positive ≥ +0.05, does not clear | HELD in direction; **UNRESOLVED** on clearance | +0.352 against a p95 of +0.353 — a margin of 0.0 SE |
| **U-d** | \|R2 lift\| < 0.10 | **BROKEN** | +0.568 — and broken by six traded sessions, not by a signal |
| **U-e** | ≥1 cell beats the restated NQ baseline; none clears the family null | **BROKEN** (1st clause); held (2nd) | best +0.774 vs +0.801; nothing premise-passing clears |
| **U-f** | every conditioner \|ρ\| < 0.10 against the MACD sign | HELD | max 0.093 |

Three of six broken. **U-d's break is the one that matters, and it broke in the direction of a
false positive** — which is what the premise check existed to catch.

## 9. One thing that is not about the confluence at all

**The candidate's restated baseline is +0.801 on 2017–2023 against +0.723 on 2016–2023.**
Dropping the first 248 sessions *raises* it. That is a **concentration-in-time warning, not an
upgrade**: the edge is stronger in the later, more volatile part of the window, which is the same
direction as [D501](D501-the-worst-day-is-a-regime-not-a-habit.md)'s finding that the loss tail
lives in one regime. **Both the edge and the risk are concentrated in the same years.** Nothing
here settles whether that is one phenomenon; the sealed 2024+ read is the only thing that can.

## 10. Checks

21 checks, all passing. The ones that did work:

- **`[OPT]`** — the claim that sessions are independent, and therefore that a whole-session gate
  is a *mask* rather than a re-simulation, is asserted **bit-identical to the state machine on
  all 8 roots × 3 arms** (max \|diff\| exactly 0.0) and raises otherwise. It cut 192 simulations
  a draw to 48. Six of the eight cells would have been fabricated by an unproven equality here.
- **No look-ahead**, re-derived at four sessions in a second implementation that never calls the
  conditioner, with the unshifted state proven to disagree on 22 of 600 sessions.
- **The roll-neutral index** proven to carry no roll jump where the naive index carries 10.2.
- **The variance ratio** proven ≈1 on iid, >1.25 under positive autocorrelation and <0.80 under
  negative — so §5's reading of it is anchored.
- **A shuffle proven to destroy the median run length (20 → 1.5) that the rotation preserves
  exactly** — the property the whole null rests on.
- The premise gates proven to **fire** on an always-on conditioner and on a flickering one.

## 11. What this changes, and what it does not

- **The 200-day SMA regime is answered on the day-session MACD**: it does not help, it halves the
  candidate in its canonical direction, and its mirror is better. **Answered, not closed** — only
  the principal closes an avenue, and a hysteresis band is untested.
- **Daily trendiness is answered by a premise failure**: the state barely exists, so the question
  "does follow-through complement momentum" cannot be asked of this clock.
- **The volatility regime is UNRESOLVED at 0.0 SE** — the single cell worth re-reading, and the
  one whose in-sample motivation means it deserves the least trust.
- **Nothing is admitted** ([R15](../RULES.md#r15)). No ledger entry, no book entry. The
  candidate stands exactly as it did before this record, with no filter attached.
- 2024+ remains sealed. Fills remain open-of-next-segment at the measured half-spread; every
  figure is an upper bound.
