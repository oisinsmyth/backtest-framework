# D440 RESULT — the Gaussian was worth five-sixths of the account's value, and what destroys it is CLUSTERING, not kurtosis

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D440-RESULT-the-gaussian-was-worth-five-sixths-of-the-value-and-it-is-clustering-not-kurtosis.md`. The H1 above is the full title.*

**Pre-registration:** [`D440`](D440-the-measured-path-through-the-lifecycle-model.md), committed
before the runner existed. **Runner:** `scripts/d440_lifecycle.py`. **Evidence:**
`data/d440_holds.csv.gz` (12,985 holds), `data/d440_lifecycle.json` (101 cells).
**Five of seven predictions wrong**, §6.

---

## THE HEADLINE

> **`T1` UNRESOLVED · `T2` FAIL · `T3` UNRESOLVED → NOT A CANDIDATE.**

**D386 valued a Gaussian trader at `$770` per evaluation on MFFU Rapid EOD 50K. The same account,
same rules, same fees, driven by C1's MEASURED path at the same mean and the same vol, is worth
`$78`.** The Gaussian assumption was carrying **88% of the value**.

**And the mechanism is not the one anybody named.** D386's own assumptions list flagged the risk as
fat tails. It is not:

| | SPY | QQQ | IWM | DIA |
|---|---:|---:|---:|---:|
| **GAUSS** — d386's own draw, matched mean and vol | **770** | 727 | 425 | 542 |
| **SHUF** — the same holds, i.i.d.: fat marginal KEPT, clustering destroyed | **654** | 610 | 353 | 474 |
| **MEASURED** — the historical sequence | **92** | 69 | **−77** | 98 |
| shortfall | 88.1% | 90.4% | **118.0%** | 81.9% |
| **share of the gap explained by the fat marginal** | **17.1%** | 17.8% | 14.4% | 15.3% |

> **The fat marginal costs 14–18% of the gap. SERIAL STRUCTURE COSTS THE OTHER 82–86%.**
> Kurtosis of 8.2 to 18.6 is nearly free. Bad holds *arriving together* is what empties the
> account.

**Named and dated, because a concentration report is not finished until the top trade is:** SPY's
worst hold in sixteen years is **2020-03-12, −9.53%**; its best is **2020-03-13, +11.27%**.
**Consecutive sessions.** That is the finding in two rows of the fixture.

---

## 1. The gates, all of which had to pass first

| | |
|---|---|
| **`[REP]`, upstream** | `run_overnight_decomposition.py` re-ran and reproduced its committed `OVERNIGHT_DECOMPOSITION_RESULTS.md` with a **zero `git diff`** |
| **`[REP]`, here** | the rebuilt holds reproduce D259 on **20 published statistics** — 12,985 holds, the three era counts, mean/p50/p90/p95/p99/worst MAE, breach at 1×/2×/3×, three era p99s, three era breach rates, four per-symbol breach rates |
| **`[P1]`** | the injected Gaussian reproduces `d386_full_lifecycle.simulate` **bit-identically**, 12 cells × 5 fields |
| **`[A1]`–`[A5]`** | lag audit against an independent re-derivation (and a peeking sigma caught); sign audit in money; EOD-vs-INTRADAY right-quantity; `SHUF` eligibility; `GAUSS` moment matching — **each with its deliberate break caught** |

**`scripts/d386_full_lifecycle.py` was not edited.** One invariant was hoisted in the D440 copy of
the loop — a clamped tuple lookup rebuilt per path per day — which took a cell from ~3 s to
**0.12 s**. `[P1]` proves the hoist value-identical rather than asserting it.

## 2. The measured series

| symbol | holds | mean/hold | sd/hold | ann Sharpe | skew | **kurtosis** |
|---|---:|---:|---:|---:|---:|---:|
| **SPY** | 3,266 | 0.0503% | 1.058% | **0.754** | 0.29 | **14.96** |
| QQQ | 3,266 | 0.0587% | 1.276% | 0.730 | 0.27 | 10.78 |
| IWM | 3,265 | 0.0470% | 1.374% | 0.543 | 0.05 | 8.16 |
| DIA | 3,188 | 0.0397% | 1.012% | 0.623 | 0.28 | 18.56 |
| POOLED | 12,985 | 0.0490% | 1.190% | 0.653 | 0.20 | 11.95 |

**The distribution, SPY, per `CLAUDE.md` rule 2.** Win rate **54.4%**, payoff **0.96**, and **the
mean 0.000503 sits BELOW the median 0.000682** — the tell that the left tail is doing the work.
**All three trims:** ex-top-1% **0.000082**, ex-bottom-1% **0.000911**, **symmetric trim
0.000489.** The symmetric trim barely moves the mean, so this is a genuinely two-sided fat book and
not a lottery; the ex-top-1% collapse is what a one-sided trim would have frightened us with.
**46 of 3,266 holds (1.41%) breach 4% inside themselves.**

## 3. Value, every cell

**MFFU Rapid EOD 50K, `V` per evaluation purchased, by provider and daily vol as a fraction of
account size.** Full grid in `data/d440_lifecycle.json`.

```
symbol rule    provider      0.2%    0.4%    0.7%    1.1%     best
SPY    static  GAUSS           53     770     448     347      770
SPY    static  MEASURED      -205    -138     -88      92       92
SPY    static  SHUF            14     654     319     210      654
SPY    voltgt  MEASURED      -168     -23      78       3       78
SPY    voltgt  SHUF           102     344     201     137      344
```

**Two things in that block are worth more than the headline.**

1. **`MEASURED` is below `GAUSS` at every one of the sixteen grid points, on all four symbols.**
   The direction of `X-a` is unambiguous.
2. **Vol targeting helps the measured path and HURTS the shuffled one** — `SHUF` falls 654 → 344
   when vol targeting is switched on. **Vol targeting is an instrument for exploiting clustering,
   so on a series with the clustering removed it is pure cost.** That is an internal consistency
   check nobody designed, and it points the same way as the `SHUF` result.

## 4. The bar

### `T1` — `V > 0` by 2 SE, circular block bootstrap on the hold sequence · **UNRESOLVED**

The naive across-path SE is **not usable and was not used**: the 8,000 paths are overlapping
rolling windows over 3,266 holds. Resampling the sequence in circular blocks:

| `b` | `V` | SE | [p05, p95] | margin | `P(V > 0)` |
|---:|---:|---:|---|---:|---:|
| 1 | 254 | 257 | [−76, 758] | **0.99 SE** | 0.845 |
| 20 | 153 | 212 | [−96, 527] | **0.72 SE** | 0.740 |
| 60 | 134 | 194 | [−109, 465] | **0.69 SE** | 0.730 |

**Nowhere near 2 SE, so `T1` is UNRESOLVED rather than PASS or FAIL.**

> **AND THE BOOTSTRAP'S CENTRE IS OPTIMISTIC, BY THE STUDY'S OWN MECHANISM.** Resampling in blocks
> partially destroys the clustering that does the damage, which is why the bootstrap mean falls
> monotonically as `b` grows — **254 → 153 → 134** — toward the historical sequence's own 78.
> **The clustering signature appears a third time, inside the error bar.**

### `T2` — P4, expected life > 3 years · **FAIL**

**Funded life at the `V`-maximising size (0.7%): 34 days = 0.14 years. Nothing on the grid clears
three years:**

```
0.2% = 1.01 yr     0.4% = 0.31 yr     0.7% = 0.14 yr     1.1% = 0.06 yr
```

**Not one path of 3,266 is alive at the 600-day horizon.**

> **D259 reported 6.40 years for this arm and both numbers are computed correctly.** D259's is
> `1 / (per-hold breach rate)` — a **per-trade** statistic. This is the **account's** life against a
> floor that ratchets up and never down, through an evaluation and a funded phase. **They are not
> the same quantity, and hurdle P is written about the second one.** This is `FINDINGS.md` §10's
> two lenses arriving on the prop track: **inverting a per-trade rate overstated account life by
> more than an order of magnitude.**

### `T3` — `V > 0` by 2 SE in 2021–2026 alone · **UNRESOLVED**

**1,109 holds, `V` = 51 ± 223, 0.23 SE, `P(V > 0)` = 0.445.**

### The era split is the part to carry forward

| era | holds | `V` | `P(pass)` | `P(paid)` |
|---|---:|---:|---:|---:|
| **2010–2019** | 1,959 | **+245** | 0.373 | 0.160 |
| **2020** | 198 | **−203** | 0.298 | 0.005 |
| **2021–2026** | 1,109 | **−135** | 0.252 | 0.053 |

> **All of the positive value is the calm decade.** The era D259 called stable on the *return* is
> not stable on the *account*: **2021–2026 is negative.**

### All five MFFU plans, MEASURED, SPY, voltgt, best risk

```
MFFU Rapid EOD/25      V   -13     MFFU Rapid/100     V  -102
MFFU Rapid EOD/50      V    78     MFFU Rapid/150     V   -77
MFFU Rapid/50          V    51
```

**D386's ordering survives** — Rapid EOD 50K is still the best MFFU cell, and it still beats Rapid
intraday at the same size (78 against 51, D386 said `$73` apart and got the sign right). **The
ordering is robust to the path; the LEVELS are not.**

## 5. Why the value goes, since it is not survival

**Funded life under the measured path is only modestly shorter than Gaussian at matched vol** —
1.35×, 1.21×, 1.04× and 0.75× across the grid. **So the account does not mostly die sooner. It
mostly never gets paid.** `P(pass)` falls 0.474 → 0.379 at 0.4%, and `P(ever paid)` with it.

**The mechanism, stated so it can be attacked:** both the evaluation (0 → +3,000 without touching
−2,000) and the first payout (0 → +2,500 with the safety net maintained) are **cumulative races
against a floor that ratchets up on gains and never down.** A run of correlated bad holds gives
back weeks of accumulation from a floor that has already risen behind it. **Kurtosis alone does not
do that — a fat tail in isolation is as likely to finish the race as to end it, which is exactly
what `SHUF` shows. Serially clustered losses do.**

## 6. Predictions — **five of seven wrong**, and they were wrong in one direction

| | prediction | outcome |
|---|---|---|
| **X-a** | MEASURED below GAUSS at every grid point | **CONFIRMED**, 16/16 points, four symbols |
| **X-b** | shortfall **25–60%** | **WRONG** — **81.9% to 118.0%**, roughly double the top of the band |
| **X-c** | SHUF between the two, **fat marginal explaining MORE than clustering** | **half right**: SHUF is between, but the marginal explains **14–18%**. **The mechanism claim is backwards** |
| **X-d** | `V`-maximising vol **0.3–0.5%**, near D259's 0.4% | **WRONG** — the argmax is **0.7%**; D259's 0.4% gives **−23** |
| **X-e** | 2020 supplies most of the gap; 2021–2026 within 25% of Gaussian | **WRONG** — **2021–2026 is NEGATIVE** |
| **X-f** | breach 1.5–4× the Gaussian at matched size | **WRONG** — funded life ratio **1.35× to 0.75×**. The damage is not through survival |
| **X-g** | **T1 passes**, T3 the one at risk | **WRONG** — T1 UNRESOLVED, and **T2, which I did not flag as at risk at all, failed outright** |

**Every miss is in the same direction: I expected the measured path to cost something and modelled
it as a tail problem.** It cost far more than predicted, through a channel I named and then ranked
backwards. **X-c is the one that matters** — had it been right, the remedy would be tail insurance;
being wrong, the remedy is anything that breaks the serial dependence, and vol targeting is already
that and is not enough.

## 7. What this does NOT claim

- **It is not an admission test and never could be.** D259 read the whole 2010–2026 window, so no
  honest holdout exists on this fixture. §1 of the pre-registration said so before the runner
  existed. **The out-of-sample test is the futures re-run, separately pre-registered.**
- **It does not close C1**, and under [R15](../RULES.md#r15) it could not. **`T2` fails on the
  account statistic; the per-hold statistic D259 measured is untouched and still reads 6.40 years.**
  Which is the right bar for hurdle P is the principal's call, and §4 states both.
- **It does not refute D386.** D386's Gaussian was declared in its own assumptions list. This
  measures what that assumption was worth.
- **It says nothing about ES.** The proxy covers 16 of 23 futures hours, and the 20:00–04:00 window
  is **unobserved rather than measured**, which makes every MAE here a lower bound and every `V` an
  upper one — the same direction as D386's own conservatism, so **the two are not independent
  margins.**
- **Four symbols, one construction, one venue.** IWM is negative everywhere; DIA and SPY are the
  only two positive at any grid point under both sizing rules.

## 8. What it leaves

1. **The settlement check is now load-bearing.** If the overnight drift is a T+1 artefact, this
   whole series has no counterpart in the instrument. It was a kill-check on the input before; it is
   the next thing to run.
2. **`T2`'s two lenses need adjudicating** — per-hold breach inverted, or account life. **They differ
   by more than an order of magnitude and hurdle P does not say which it means.**
3. **The remedy implied is not tail insurance.** Anything that breaks serial dependence in the
   *sequence the account experiences* — an abstention rule, a regime gate — is what the `SHUF`
   result points at, and O1 in the prop ledger is exactly that shape.
