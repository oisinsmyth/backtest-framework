# D469 — RESULT: the scalping re-cost. The spread is not what kills it; a fixed commission against a tenth-sized tick is

**2026-09-12.** Runner [`scripts/d469_scalping_feasibility.py`](../../scripts/d469_scalping_feasibility.py) ·
artifact [`data/d469_scalping_feasibility.json`](../../data/d469_scalping_feasibility.json)

**A FEASIBILITY REVIEW, NOT A SCREEN.** No signal, no entry rule, no edge, no Sharpe of any
construction. Nothing is opened, closed or admitted ([R15](../RULES.md#r15) — that is the
principal's). What is settled is **what a scalp must clear, and why**.

---

## 0. Why this was owed

[R13](../RULES.md#r13) §2, verbatim: constructions excluded on ETF cost arithmetic —
*"scalping, D247's intraday shorts, most of the intraday microstructure literature"* — **clear
their costs by an order of magnitude on futures**, and *"a cross-screen must RE-COST, not
merely re-threshold."*

[D258](D258-the-prop-track-candidates.md) is where scalping was excluded: **31–187%/yr** in
cost on ETFs, against ES futures at *"~$4–5 on ~$250k notional ≈ 0.2 bp"* — **"roughly twenty
times cheaper."** That 0.2 bp is **commission only**; nobody had measured the crossing. D465
did (0.364 bp round trip). So the re-cost has never been run on a measured number, and the
figure it would have been run on was missing its larger half.

---

## 1. The answer, and it is not the one D258 implied

**D258 excluded scalping because the spread was too wide. On futures the spread is fine. The
thing that kills it is the fixed commission — and only at the size the component standard
forces.**

At the measured median ES price of 6,919.50:

| | notional | crossing | commission | total | **= ticks** |
|---|---:|---:|---:|---:|---:|
| **ES** (1 contract) | $345,975 | $12.61 | $4.00 | $16.61 | **1.33** |
| **MES** (1 micro) | $34,598 | $1.26 | $3.00 | $4.26 | **3.41** |

Crossing is **1.01 ticks on both** — the half-spread and the tick value scale together, so
that ratio is **scale-free**. Commission does not scale: it is charged per *contract* while the
micro's tick is worth **one tenth**. So the same $3–4 that is a rounding error on ES
(0.32 ticks) becomes **2.40 of MES's 3.41 ticks — 70% of the cost**.

**The micro is not a conservative choice. It is the only size the standard admits**, and that
is computed rather than asserted: `COMPONENTS_PROP.md` **C-d** caps daily σ at 1% of a $50k
account ($500), and one contract held flat all day runs

    ES    σ ~ $4,070    BREACHES the cap, 8.1x
    MES   σ ~   $407    fits, 0.8x

So a scalp scored as a component faces the **3.41-tick** bar, not the 1.33-tick one. One
contract of ES is untradeable in a $50k account regardless of any edge.

---

## 2. What the instrument offers, against what it costs

121,617,272 ES front-month trades, 2025-09-11 → 2026-09-10, on a one-second last-trade grid;
8.7–9.0 million matched pairs per horizon. Moves in **ticks**, **unconditional**.

| horizon | E\|M\| | RMS | p50 | p90 | p99 | trades/day | **free** | ES p_be | **MES p_be** |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 10 s | 2.46 | 3.75 | 2 | 6 | 13 | 8,280 | 70.5% | 77.1% | **119.4%** |
| 30 s | 4.24 | 6.39 | 3 | 9 | 22 | 2,760 | 61.9% | 65.7% | **90.2%** |
| 1 min | 5.97 | 8.96 | 4 | 13 | 30 | 1,380 | 58.4% | 61.1% | **78.5%** |
| 2 min | 8.45 | 12.63 | 6 | 19 | 43 | 690 | 56.0% | 57.9% | **70.2%** |
| 5 min | 13.32 | 19.86 | 9 | 30 | 67 | 276 | 53.8% | 55.0% | **62.8%** |
| 15 min | 22.83 | 33.94 | 16 | 51 | 115 | 92 | 52.2% | 52.9% | **57.5%** |

`p_be` is the directional accuracy that **nets exactly zero**. **`free` is the accuracy needed
if commission were ZERO** — the half-spread alone. It is the one column no brokerage deal and
no contract size can improve, and it is identical for ES and MES.

**On the micro, a scalp proper is arithmetically impossible.** At 10 seconds the cost
*exceeds* the mean move, so **no accuracy whatsoever breaks even** — p_be is 119.4%, which is
not a hard target but an unreachable one. At 30 seconds it is 90.2%; at one minute, 78.5%.

**E|M| scales as h^0.50** — exactly diffusive, fitted on the 1-minute and 15-minute rows. That
is an independent check that the grid is measuring a random walk and not an artefact. It also
means the cost wall recedes only as √h: **MES needs ~8 minutes to break even at 60% accuracy
and ~34 minutes at 55%.** Cost does not make scalping hard on the micro; it moves the viable
horizon out of scalping and into something else.

**And even free is not cheap.** At 10 seconds the half-spread alone demands **70.5%**, at one
minute **58.4%**. A zero-commission scalp is still a hard problem — which is the part of
D258's instinct that survives.

### The Sharpe bar adds almost nothing, and that is the surprise

With per-trade cost C, gross signed mean q = (2p−1)·E|M| and N independent trades a day:

    annualised Sharpe = sqrt(252*N) * (q - C) / sqrt(RMS^2 - q^2)

Inverting it at C-a's **Sharpe 0.5** adds **0.0 to 0.3 percentage points** to p_be across the
whole grid — because √N is enormous (92 to 8,280 trades a day). **The binding constraint is
breakeven, not the Sharpe hurdle.** A scalp that merely clears cost at these trade rates clears
C-a comfortably; one that does not clear cost is not close.

C-d is likewise slack at micro size: daily σ at 1 MES is $407 against the $500 cap, so trade
*count* is not what the account limits.

---

## 3. Where this leaves the exclusion

**D258's verdict on scalping stands. Its reason does not.**

- **The cost arithmetic that excluded it was ETF arithmetic, and futures are ~20× cheaper as
  D258 said** — 0.364 bp round-trip crossing on ES, 1.01 ticks, against ETF costs of
  31–187%/yr. That part of R13 §2 is confirmed.
- **But the cheapness is in the spread, and the spread is not the binding cost at the only
  tradeable size.** A fixed per-contract commission against a tenth-sized tick is. D258 never
  considered the micro because the component standard that forces it (D466, 2026-09-12) did
  not exist yet.
- **So the re-cost R13 demanded does not reopen sub-minute scalping on this account.** It
  closes it for a *different and sharper reason*, and it says exactly what would change the
  answer: a commission near zero (still needs 58.4% at one minute), a larger contract (blocked
  by C-d at a $50k account), or a horizon of tens of minutes (no longer scalping).

**What this does NOT do.** It renders no verdict on the intraday microstructure literature
D258 excluded alongside scalping — those effects were quoted at **2.65–3.78 bp/trade**, which
against MES's 3.41-tick bar (**1.23 bp** at this price level) is a live question and a
different study. **That re-cost is still owed.** This one covers scalping, which is the
horizon, not the mechanism.

---

## 4. What is measured on what, and the window caveat

**Measured on 2025-09-11 → 2026-09-10**, which is **not** the in-sample window a component is
scored on (2016-01-04 → 2023-12-29, D462) and overlaps the confirmation slice. The
**unconditional** move distribution carries no rule and no selection, so it cannot spend a
holdout — there is nothing here to select on. But **any actual scalp must be scored on the
in-sample window**, and the move distribution of 2016–2023 is not this one.

**Assumptions of the Sharpe identity**, all of them favourable to a scalp:

1. the trade captures the **full** h-second move, signed by the call — an upper bound on any
   exit rule;
2. trades are **independent** across the day (clustered entries lower the effective N);
3. **no slippage beyond the measured half-spread**, and no queue position — a scalp at 8,280
   trades a day would not get filled at the touch every time;
4. the move distribution is **stationary** over the measured year.

Relax any of them and the required accuracy rises. **The bars above are floors.**

---

## 5. Three errors in this review's own first run

**The p99 was 240 ticks at every horizon from 10 seconds to 15 minutes, against a median of
2.** A tail that does not move with the horizon is not a move — it was the ES **calendar
basis**, because D465's tick cache pooled two expiries. That bug and its correction are
[D465 AMENDMENT 3](D465-RESULT-the-cost-line-was-never-what-killed-C1-crossing-costs-a-tenth-of-the-edge-and-the-bar-grid-was-conservative.md);
it moved that record's published MAE p99 by 0.861 pp. **The tell was a statistic that refused
to scale with the axis it was measured against.**

**The first requirement was computed on the mean move among pairs that CLEARED the cost bar.**
That is look-ahead: no rule can select a trade by the move it turned out to make. It flattered
every horizon into a 52–57% requirement — the 10-second row read 54.3% where the honest number
is **119.4%**. The conditional share is retained in the artifact as
`share_exceeding_descriptive_only` and feeds nothing.

**The Sharpe identity was wrong twice, and both wrong versions matched a simulation.** The
first put RMS in place of σ; the second put the net mean where the *gross* one belongs
(Var = E[M²] − q², not RMS² or RMS² − μ²: a fixed cost shifts the mean and leaves the variance
alone). Each agreed to 0.2% at a small edge and was ~7% out at a large one. **An approximation
is at its most convincing exactly where it was first checked** — and the fix was to check all
three branches, including at breakeven, with a tolerance derived from the simulation's own SE
rather than a guessed percentage. A "2%" band had failed the correct formula on a 1.1-SE
discrepancy.

---

## 6. Checks

`--self-test` carries 16 checks, and **every one is proven to fail when the scalar it reads is
perturbed** — four declared breaks, each required to redden exactly the checks it should and no
others. Two of the four break declarations were wrong on their first run, listing only the
direct target while the cascade showed as UNEXPECTED; the declarations were corrected, not the
checks.

- contract geometry is **read from** `data/futures_contract_specs.json` (CME's own spec
  service), with commission declared separately and sourced — CME does not supply brokerage
  numbers, and conflating them would let an assumption borrow CME's authority;
- the crossing is **read from D465's artifact**, not copied. The copy was 0.3664 and went stale
  the moment D465 was re-run at 0.3644;
- the ES:MES tick ratio is asserted to be exactly 10 — the whole commission-dominance argument
  rests on it;
- the input gate refuses a cache without `instrument_id`, refuses any second carrying two
  expiries, and drops pairs whose ends are different contracts;
- the Sharpe identity is checked against a 20,000-day fat-tailed simulation at three accuracy
  levels, and its inversion is checked to round-trip.

## 7. What this does not do

- **It does not close or open anything.** R15.
- **It scores no construction**, so it enters nothing in `COMPONENTS_PROP.md` and touches
  neither book.
- **It does not re-cost the microstructure literature**, only the scalping horizon. Owed.
- **Nothing is elevated** into `FINDINGS.md` or `RULES.md`.
