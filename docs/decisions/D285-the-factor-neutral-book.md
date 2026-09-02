# D285 — The factor-neutral book

**Status:** PRE-REGISTERED. Committed **before the runner exists**. Nothing here is a result.
**Date:** 2026-09-02
**Area:** Strategy research · **personal track**

---

## Why this, and why it is the last structurally different idea

[FINDINGS §9](../FINDINGS.md) has carried the factor-neutral branch as live through **eight studies
that all returned no survivors** — D256, D264, D279, D280, D281, D282, D283, D284. It is the only
remaining construction that changes the **mechanism** rather than a parameter of one already
measured to fail.

**The arithmetic is why.** Every construction tested has been **net directional in a market with
positive drift**, paying `−μ − σ²` before a dollar of cost:

| | gross, before any fee |
|---|---:|
| D279 `S1_short\|top25` | **−0.432 Sharpe** |
| D282 `base\|all` — short every name overnight | **−21.92% CAGR** |

**These are not cost failures.** They lose at zero fees. **A factor-neutral book removes the `−μ`
term by construction**: if the market rises, the long leg gains what the short leg loses. What
remains is only the difference between the two baskets, so **the short leg no longer has to beat
drift plus costs — it only has to underperform the long leg.**

**D251 closed this on ETFs and that closure does not transfer.** It failed at breadth **2.2
effective instruments** across 57 ETFs — the *universe* failing, not the construction. This fixture
carries **1,573 names and 10.06 effective independent instruments over a held book**.

## AND IT IS NOT A NOVEL IDEA — it is short-term reversal, and that must be said first

Long the lowest `hist_L` and short the highest is **cross-sectional short-term reversal**, a
documented effect since Lehmann (1990) and Lo–MacKinlay (1990). **It is also documented as being
concentrated in small, illiquid, low-priced names and largely consumed by the bid-ask spread** —
which is precisely what [D284](D284-the-overnight-long.md) measured on this fixture: a **$1.92
tenth-percentile stock, 25.7% of positions under $5, and a breakeven half-spread of 11.36 bp/side
against a 15 bp floor.**

**So the prior is not "an undiscovered edge". The prior is "a known effect that usually does not
survive costs", and this study exists to measure whether it survives HERE.**

---

## The construction

```
fixture    us_shorts_daily_raw.csv.gz -- 1,573 names, 35.7% dead, ragged
score      hist_L from signals_ragged, LAGGED ONE BAR (R9)

arm        LONG  the N LOWEST  lagged hist_L
           SHORT the N HIGHEST lagged hist_L
           equal dollars per leg, equal weight within a leg
           N in {10, 25, 50} PER LEG

hold       daily bars, close to close. Re-ranked each bar, so a name persists
           while it stays in its tail -- D279 measured a mean holding run of
           ~9 bars under exactly these semantics.
```

**The direction is taken from measurement, not from intuition.** D283, in short bp on the ALL
universe: shorting the lowest tail loses **−19.42**, shorting the highest loses **−9.93**. Both
tails rise; **the lowest rises more.** So long the lowest, short the highest.

**Costs.** 5 bp/side, `rf` 4% on the long leg, borrow 3%/yr on the short leg, PPY 252. **Both legs
are charged. A two-leg book pays roughly twice the fees of a one-leg book and that is the price of
neutrality**, stated here rather than discovered in the result.

### The price floor, declared in advance and disclosed as suggested by a failure

**Universe variant A: no floor.** The population every prior study used.
**Universe variant B: entry close ≥ $5.00.**

**Variant B was suggested by D284's failure**, and R13 requires that be said rather than presented
as an independent design choice. It is legitimate here because it is a **universe constraint
declared before this study runs**, not a filter added to rescue a result. **Both variants are run
and both are reported**, so the reader sees exactly what the floor bought and what it cost.

**Cells: 3 N × 3 modes × 2 universes = 18.** Counted in full.

---

## Controls

| | |
|---|---|
| `rnd-N` | N long and N short drawn **at random from the whole universe**, matched count |
| **`tail-N`** | N long and N short drawn **at random from the 2N most extreme \|lagged hist_L\| names** — matched on the volatility tail, random on **which** tail |

**`tail-N` is the binding control and it is here because D283 and D284 proved the other one is not
enough.** `hist_L` is *signed acceleration*, so both tails are the volatile names. D283 measured a
**direction-blind tail tax of −14.68 / −9.80 / −6.58 bp** against a **directional component of
+4.75 / +4.66 / +3.60**. A control drawn from the whole universe is beaten by the tax alone.
**Without `tail-N`, D284's hurdle C would have passed on the nuisance** — that is measured, not
hypothetical.

**A long/short book on the same score should cancel most of the tail tax by itself**, because both
legs sit in the tail. **`tail-N` is what proves it did.**

---

## Hurdles

| | standard |
|---|---|
| **M** | **Mean move per trade ≥ 2c = 10 bp** per name round trip. D265's form |
| **B** | **Breakeven half-spread ≥ 15 bp/side.** D284 died here and it is the known killer of short-term reversal |
| **NEU** | **\|correlation of the book's daily return to the equal-weight universe return\| ≤ 0.20.** **A study that claims neutrality must demonstrate it**; a book that is not neutral is not testing this hypothesis |
| **V** | **Positive net CAGR** after fees, financing and borrow |
| **C** | **Beats `rnd-N` AND `tail-N`** on Sharpe *and* money, **gross and net** |
| **F** | **Best-of-18 floor** (D228), one shared offset vector |
| **E′** | Effective independent instruments ≥ 3.0 over the held book, ≥500 trades. **Expected to degenerate to ≈ N and to be uninformative when it does** — D279 scored 28.00 on 28 names, D281 63.00 on 63, D284 63.00 on 63. The runner must say so |
| **H** | Rotation null — **REPORTED, NOT DECISIVE.** Four measured demonstrations of R7's corollary now exist, including random controls clearing at the 100th percentile while losing money |

---

## A declared diagnostic, reported whatever the verdict

**THE PERSISTENCE OF `d`.** The directional component is measured at **+4.66 bp (D283) and +4.18 bp
(D284)** for the **first** night after the signal. **Whether it accrues on every night of a ~9-bar
hold or only the first is unmeasured, and it is the single quantity that decides the arithmetic:**

```
per round trip, two legs        cost 20 bp
d persists all 9 bars     9 x 9.3 = 84 bp    ratio 4.2x
d is first-bar only               9.3 bp     ratio 0.5x
```

**Reported at horizons 1, 2, 5, 10 and 15 bars, for both tails separately and for the spread.**
It is a diagnostic and not a hurdle, because it is not a pass/fail of the book — **but if it shows
first-bar-only decay, that is the explanation of whatever the book scores and it must be read
together with the verdict.**

**It is deliberately NOT measured before this record is committed**, because a holding period chosen
after seeing a decay curve is a fitted parameter. The hold semantics are frozen to D279's.

---

## Predictions

| | prediction | direction | confidence |
|---|---|---|---|
| **F1** | **NEU clears at all three N** — the book is genuinely market-neutral. Near-determined by construction and **not to be scored as a success** | neutral | **very high** |
| **F2** | **Gross Sharpe is POSITIVE at all three N on at least one universe variant** — the first positive gross of the programme. This is what removing `−μ` is supposed to buy | **for** | **moderate** |
| **F3** | **Hurdle B fails on universe A**, because the unfloored book holds the same cheap names D284 held | **AGAINST** | **high** |
| **F4** | **On universe B the price floor removes most of the edge along with the cheap names**: the spread between `book` and `tail-N` on gross Sharpe is **smaller** on B than on A at every N | **AGAINST** | **moderate-high** |
| **F5** | **`d` decays: the 5-bar horizon carries less than half the per-bar edge of the 1-bar horizon** | **AGAINST** | **moderate** |

**F3, F4 and F5 are all declared against the construction, and F4 is the load-bearing one.** If the
floor keeps the edge, this is tradeable in a way nothing else in the programme has been. **What
would falsify F4: the `book − tail-N` gross Sharpe gap being LARGER on universe B than on A at N =
25.**

---

## Ledger

| | |
|---|---:|
| carried under [R13](../RULES.md#r13) — D256 21, D279 20, D281 10, D282 19, D283 26, D284 13 | **109** |
| fresh — 3 N × 3 modes × 2 universes | **18** |
| **total** | **127** |

**D280's 165 statistics are disclosed and shaped this search space.** The best-of-18 floor prices
this study's own cells and **cannot price the choice of direction, which came from D283's
decomposition.** That is stated here rather than left for the F hurdle to imply.

---

## Stop

**If NEU fails, the study is void rather than negative** — it did not test the hypothesis, and it is
re-run once with the neutrality construction corrected.

**If B fails on both universes, the factor-neutral book is closed**, and with it the directional
short programme in every form this fixture can express. No third universe variant, no fourth N, no
alternative score, no sector or beta refinement bolted on afterwards.

**If it clears, it is not a book entry.** Under [R8](../RULES.md#r8) it needs a pre-registered
out-of-sample test, and **D246's reserved wide-universe cohort is unspent** and is the candidate.
