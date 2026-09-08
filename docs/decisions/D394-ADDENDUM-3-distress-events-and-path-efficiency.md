# D394 ADDENDUM 3 — distress, event volume and signed path efficiency all fail the asymmetry test, and a clairvoyant delisting filter would make things WORSE

**Status:** ADDENDUM 3. **DESCRIPTIVE** — no null, no hurdle, nothing selected, fitted or admitted
(R15). **Nothing closed.**
**Date:** 2026-09-09 · Runner: `scripts/run_d394_asymmetry_candidates.py` · Artifact:
`data/d394_asymmetry_candidates.json` · 59 s · **Holdout reads: 0.**

Tests the three candidates the principal named against
[Addendum 2](D394-ADDENDUM-2-the-oracle-tail-bound.md)'s criterion: **a filter must be scored on
asymmetry — `spread_left − spread_right` — not on how well it predicts losses.**

---

## 1. The verdict: four candidates, no asymmetry

| candidate | what it is | P(left) spread | P(right) spread | **asymmetry** |
|---|---|--:|--:|--:|
| **`DD_252`** | drawdown from the 252-bar high — **distress** | **9.7 pp** | **9.6 pp** | **+0.1** |
| `ER_signed_21` | **signed path efficiency** — net ÷ travel | 1.9 | 2.8 | **−0.9** |
| `ER_21` | A1's unsigned efficiency, as contrast | 0.8 | 1.4 | −0.6 |
| `DV_spike` | dollar volume ÷ its own trailing mean — **event** | 0.8 | 1.7 | −0.9 |

*(cap 20; cap 5 gives −0.3, −0.5, −0.7, −0.7 — the same picture.)*

> **`DD_252` is a powerful left-tail predictor: names deepest in drawdown produce a bottom-decile
> trade 15.4% of the time against 5.7% for the shallowest. It predicts the RIGHT tail at 15.8%
> against 6.2%. Distress predicts catastrophe and recovery equally.**

**Every candidate lands within 1 pp of zero asymmetry** — the same result the five observables in
Addendum 2 gave. **Nothing yet found separates the two tails.**

---

## 2. Path efficiency: the hypothesised mechanism is not there

The a-priori case was that **a name falling in a straight line is being sold with conviction and
keeps falling, while a name falling choppily is noise and reverts.** Signed ER expresses that;
A1's unsigned version cannot, since it scores a straight-line riser and a straight-line faller
identically.

**It is not supported.** At cap 20, the straight-line fallers (`lo` band) earn **+23.09** against a
book mean of +22.06 — indistinguishable. The band that earns least is `hi`, the straight-line
*risers* (+4.12), which is a different observation and not the mechanism proposed.

**`[ER]` confirms the construction:** `|signed| == a1_er_stage0.er_grid` on **4,091,416 cells,
exactly**, with the denominator summed directly rather than differenced from cumulative sums —
A1's recorded defect, which broke the triangle inequality on 329 cells.

---

## 3. THE STRONGEST RESULT — a clairvoyant delisting filter would LOSE money

Bars from entry to each name's **last live bar**. **This is look-ahead and can never be a filter** —
nobody knows it at entry. It is computed only to ask whether the left tail is delisting-driven.

| cohort | median bars to delist | P(left) | P(right) | **mean, cap 20** |
|---|--:|--:|--:|--:|
| **soon** | 403 | 12.0% | 12.2% | **+21.03** |
| mid | 1,317 | 10.7% | 11.1% | **+29.47** |
| **far** | 2,420 | **7.3%** | **6.8%** | **+15.69** |

**Names closer to delisting do have fatter tails — in BOTH directions — and the cohort furthest
from delisting earns the LEAST (+15.69 against +29.47).**

> **So even with perfect foresight about which names die, you would not exclude them. The dying
> names are not the problem; they are part of where the return is.**

That is consistent with everything else this study has found — the edge lives in the cheap, volatile,
distressed cohort ([Addendum 6](D393-ADDENDUM-6-the-ten-cells-and-the-price-split.md): cheap tercile
+59.04; [Addendum 2](D394-ADDENDUM-2-the-oracle-tail-bound.md): high-vol tercile +66.79) — **and it
is a reversal book, so distress is the setup, not the hazard.**

**This closes the intuition, not the avenue:** "filter out the dangerous names" is answered NO by a
filter strictly better than any tradeable one.

---

## 4. And the best band-drop is not a mechanism

| | best drop | resulting mean | bar |
|---|---|--:|--:|
| cap 5 | `DV_spike` — drop **mid** | +8.46 | 61.48 |
| cap 20 | `DD_252` — drop **mid** | +35.84 | 61.19 |

**Nothing reaches the round trip.** And on every candidate the best band to drop is the **middle**
one, not a tail — dropping the cohort that happens to earn least on this ledger. **A U-shaped
mean across an ordered variable is a hallmark of noise, not of mechanism**, and a "drop the middle
tercile" rule is a fit to this sample rather than a filter with a reason.

---

## 5. What is now known not to separate the tails

**Nine observables, none asymmetric:** the score itself, `rsi`, `rev_21`, `rvol21`, price
(Addendum 2), and `DD_252`, `ER_signed_21`, `ER_21`, `DV_spike` (here) — **plus a look-ahead
delisting oracle that points the wrong way.**

**This closes nothing (R15).** Nine observables is not the space. But the pattern is now consistent
enough to state as a working hypothesis rather than a run of bad luck:

> **On this construction the two tails appear to be the same phenomenon seen twice. Everything that
> makes a large loss likely makes a large gain likely, in near-equal measure — which is what a
> payoff of 1.024 and a skew of +0.33 already said. A left-tail filter needs a variable that is
> one-sided in the OUTCOME, and distress, event volume, drawdown and path shape are all one-sided
> in the SETUP while remaining two-sided in the outcome.**

**A note on cost:** this run rebuilt the panel a second time to reach the close grid, peaking at
1.76 GB rather than the ~0.4 GB the other diagnostics use. Avoidable, and worth fixing if this
runner is extended.

---

**Status footer.** Descriptive. No null, no holdout read, nothing admitted, nothing retired.
`docs/BOOK.md` holds S1 and S2, neither at capital; `docs/BOOK_PROP.md` is empty.
