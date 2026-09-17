# D486 — RESULT: cost cutting closes ~70% of the gap and stops, and only NQ gets anywhere

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D486-RESULT-cost-cutting-closes-70-percent-of-the-gap-and-stops-and-only-NQ-gets-anywhere.md`. The H1 above is the full title.*

**2026-09-12.** Runner [`scripts/d486_cost_levers.py`](../../scripts/d486_cost_levers.py) ·
artifact [`data/d486_cost_levers.json`](../../data/d486_cost_levers.json)

**NO NEW MEASUREMENT.** Every input is already committed — D484's edge, D465's crossing,
D466's commission, D472's volume-clock lift, CME's specs, `COMPONENTS_PROP.md`'s C-a and C-d.
This is arithmetic on them, answering the principal's question: *where does our cost cutting
take us?* Nothing is opened, closed or admitted ([R15](../RULES.md#r15)).

---

## 1. The structure of the problem, which decides which levers matter

Cost has two parts and **they respond to completely different levers**:

- **commission is FIXED per contract** → beaten by trading **less often**, or paying less;
- **crossing is PROPORTIONAL to notional** → beaten by **passive execution**, and not at all by
  holding longer.

**At micro size the fixed part dominates**, because every CME micro's tick is worth **$0.50**
except MES's **$1.25**, while a full contract's is $5.00–$12.50:

| root | best D484 cell | gross | commission | crossing | **commission share** | net | gross/cost |
|---|---|---:|---:|---:|---:|---:|---:|
| ES | B1 H=5 | 0.922 tk | 2.40 tk | 1.009 tk | **70.4%** | −2.487 | 0.27 |
| NQ | B2 H=5 | 3.849 tk | 6.00 tk | 1.009 tk | **85.6%** | −3.160 | 0.55 |
| YM | B2 H=5 | 1.978 tk | 6.00 tk | 1.009 tk | **85.6%** | −5.031 | 0.28 |

**$3 is 6.00 ticks on MNQ and 0.60 on full NQ — a tenfold difference in the same market.**

**And Sharpe is scale-free**, which is the non-obvious consequence: doubling the contract
doubles edge and risk alike, so **contract size enters only through the fee's size in ticks**.
At zero commission a micro and its full contract give *identical* Sharpe. The full contract's
whole advantage is that $3 is a smaller fraction of a bigger tick.

## 2. Where the levers take it

| root | scenario | net ticks | **Sharpe** | clears C-a? |
|---|---|---:|---:|---|
| **NQ** | as measured (micro, $3) | −3.160 | **−0.50** | no |
| | + volume-clock exit | −2.760 | −0.43 | no |
| | + passive fills | −1.751 | −0.27 | no |
| | **FULL contract, $3** | **+2.240** | **+0.35** | no |
| | FULL + volume clock | +2.640 | +0.41 | no |
| | micro at **zero** commission | +3.240 | **+0.51** | **YES** |
| | **FULL + volume clock + passive** | +3.649 | **+0.57** | **YES** |
| ES | best available (FULL + clock + passive) | +0.778 | +0.42 | no |
| YM | best available (FULL + clock + passive) | +1.584 | +0.39 | no |

**Only NQ reaches C-a, and only in two scenarios — one of which is an unreachable bound.**

## 3. The three numbers that answer the question

**(a) Cost cutting closes about 70% of the gap and then stops.** On NQ it moves the Sharpe from
**−0.50 to +0.35** just by getting off the micro — the entire distance from losing money to
making it. But +0.35 is short of C-a's 0.5, and **no further cost lever that is actually
measured closes the rest.**

**(b) The breakeven commissions, which price the lever exactly:**

    MNQ  $1.62   against the declared $3.00   -- a 46% cut reaches BREAKEVEN, not C-a
    MYM  $0.59
    MES  $0.01   -- ES is hopeless at ANY commission

**MES's gross of 0.922 ticks is below the 1.009-tick crossing alone**, so a zero-fee broker
still loses on ES. That is not a fee problem; that is too little edge.

**(c) The account C-d would need for a full contract**, which is what forces the micro in the
first place:

    full NQ  daily sigma $2,327  ->  $232,679
    full ES  daily sigma $1,707  ->  $170,698
    full YM  daily sigma $1,469  ->  $146,865

**At ~$233k the fee problem disappears — but a $233k account is not a $50k prop evaluation.**
The constraint that creates the cost problem is the account size itself.

## 4. The ordering of levers, which is not what I would have guessed

**Passive execution is nearly worthless at micro size and dominant at full size.** Crossing is
only **14%** of MNQ's cost but **63%** of full NQ's. So:

1. **Fix the fee first** — 86% of the problem at micro size. Either a bigger contract (needs
   the account) or a cheaper broker (needs ≤ $1.62 on MNQ just for breakeven).
2. **Then passive execution** — worth +0.16 Sharpe on full NQ (0.41 → 0.57), and +0.02 on the
   micro. It only becomes the main lever once the fee is already small.
3. **The volume-clock exit throughout** — +0.06 to +0.08 Sharpe, free, and the only lever here
   that is *measured* rather than assumed (D472, 8 of 8 years).

## 5. What this does not license

**Every positive row is conditional on a cost change that has not been obtained**, and the two
rows that clear C-a both depend on **passive fills, which are measured nowhere.** D471 §1 says
so explicitly: it measured the *quoted* spread and stated that queue position, partial fills and
latency need `mbp-10`, which was not bought. **Those rows are upper bounds, not results.**

Also standing: D484's edge is **in-sample** (2016–2023, 2024+ sealed); the 1.009-tick crossing
is an **ES** measurement assumed for NQ and YM; the volume-clock lift is an **ES** measurement
assumed to transfer; and **holding beyond H=5 is untested** — D484's grid stopped there and the
edge was still rising with H at its edge, which is a ceiling of my design and not of the effect.

**Nothing enters `COMPONENTS_PROP.md` or either book.**

## 6. What is worth doing next, in order

1. **Extend H past 5 hours.** The cheapest untested lever, and the one the arithmetic most
   favours: commission is fixed, so halving trade frequency halves 86% of the cost, and D484's
   edge was still growing at the grid's edge. This needs a pre-registration.
2. **Cost GC and CL**, whose D484 edges (+0.0326, +0.0337 σ) are the largest measured and which
   §5 could not price because MGC and MCL are absent from
   `data/futures_contract_specs.json`.
3. **Measure passive fills**, which would turn the two C-a-clearing rows from bounds into
   results — and needs `mbp-10`, a purchase decision for the principal.
4. **Get the real commission schedule.** $3.00 is D466's declared line, not a quote. The whole
   table above is a function of it, and MNQ needs $1.62 for breakeven alone.

## 7. Checks

13 self-test checks, all on the arithmetic rather than on data: Sharpe proven scale-free in tick
value, linear in the net edge, √N in the trade count, and negative on a negative edge; the
commission-budget identity proven to go to zero at gross = crossing and **negative below it**
(MES's case, −$0.109); the fee-in-ticks ratio proven to be 10× between MNQ and NQ; C-d proven to
invert correctly; and the volume-clock lift proven to touch gross only and never cost.
