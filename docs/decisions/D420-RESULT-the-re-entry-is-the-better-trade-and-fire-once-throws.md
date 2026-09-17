# D420 RESULT — the re-entry is the better trade, and "fire once" throws it away

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D420-RESULT-the-re-entry-is-the-better-trade-and-fire-once-throws-it-away.md`. The H1 above is the full title.*

**FAILS THE BAR on all three gates, and T1 fails with the wrong sign — as predicted.**
Pre-registration `7cc52eb` predates the runner and this file (R8). **The ledger does not move.
Nothing was admitted. No holdout was read (the principal's standing decision).**

Cost: 216 s, of which 13 s were the 24 books.

**Note on scope:** the principal clarified after the pre-registration that a cooldown was not the
rule they had in mind — the intended rule derives the exclusion from a *structure-stop-out*, not
from any exit — and asked that this study be completed as built. It is. The structural version is
a separate question and is not tested here; §5 says what this result implies for it.

---

## 1. The book is D419's, and the rule sits inside it

```
[ALIGN]  D413's event table matches D419's cache; arming days attached
P2       rule off == D419's FIXED book: 40,977 trades, gross +2.817, net -3.616  -- bit-identical
[RECON]  every book;  [ONCE]  every EPISODE ledger;  [CHUNK]  worker draw 0 == in-process
```

---

## 2. THE PER-TRADE LENS — T1 fails with the sign reversed

```
                    re-entry     FIRST entries                RE-ENTRIES                   first − re
                    share      mean    median   trim       mean    median   trim
EPISODE  pooled     51.8%     +9.47    +4.20   +8.29     +16.70   +12.96  +17.46      -7.22 ± 2.95   -2.5 SE
EPISODE  cell 2     72.0%    +28.27   +17.78  +26.34     +31.04   +22.90  +29.03      -2.77 ± 8.20   -0.3 SE
COOLDOWN5  pooled   47.1%    +10.54    +5.82   +9.69     +16.22   +12.08  +16.84      -5.69 ± 2.97   -1.9 SE
COOLDOWN20 pooled   65.0%    +12.05    +6.65  +10.32     +13.84   +10.01  +14.51      -1.80 ± 3.03   -0.6 SE
```

**A re-entry pays +16.70 bp; a first entry pays +9.47.** The medians say it more plainly — +12.96
against +4.20 — and the symmetric 1% trims agree, so it is not a tail. **"Fire once per episode"
keeps the worse half of the book and discards the better half**, and at 51.8% it is literally
half: **more than one touch in two on this construction is a re-entry.**

X-a called the share at 20–35%; it is 52% pooled and **72% in cell 2**. The direction was right —
deep declines stack zones — and the size was badly under. In cell 2 nearly three touches in four
are the name's second, third or fourth zone in a continuing decline.

**X-b was the prediction that mattered, and it held:** the re-entry is a name that fell into zone
A, was held five days, and fell further into a deeper zone B — the deep-decline population that
D416's late stalls and D418's through-the-zone closes had already shown pays more. Consumed
zones had been armed a median 9 days (p10 1, p90 31) before the exit that consumed them.

---

## 3. THE BOOK LENS — the rule does exactly what removing half the events at random does

```
50 slots         gross     net     cost    trades   turnover    util    skipped / considered   per trade
FIXED           +2.817   -3.616   6.434    40,977   19.90%/d   99.5%          0 / 40,977         +14.16
EPISODE         +2.548   -4.022   6.570    40,686   19.76%/d   98.8%     13,485 / 54,171         +12.89
COOLDOWN5       +2.734   -3.760   6.494    40,858   19.84%/d   99.2%      5,375 / 46,233         +13.78
COOLDOWN20      +2.395   -4.155   6.550    40,343   19.59%/d   98.0%     22,680 / 63,023         +12.22
```

**§1 of the pre-registration, measured:** utilisation stays at 98.8%, turnover at 19.76%/day,
cost per bar *rises* from 6.43 to 6.57. **The rule does not reduce turnover on a full book. It
swaps which names hold the slots** — and it swaps out the better ones. The per-trade mean falls
from +14.16 to +12.89.

| | condition | outcome |
|---|---|---|
| **T1** | first entries beat re-entries | **FAIL — reversed**, −7.22 bp, −2.5 SE |
| **T2** | EPISODE net beats FIXED net | **FAIL** — −0.377 ± 0.465 bp/bar, −0.8 SE, over three seeds |
| **T3** | EPISODE beats a matched-count random exclusion | **FAIL** — margin −11.1 SE |

**T3 is the sharpest line.** Against 50 books that remove a random 51.8% of events, EPISODE's net
of −4.022 sits at the control's **median** (−4.077). On the cell-2 book, −1.089 against a median
of −1.087. **The re-entry identification carries no information for the book at all; the rule is
indistinguishable from thinning the pool blindly at the same rate.**

The cell-2 secondary fails all three the same way (T1 −0.3 SE, T2 −0.2 SE, T3 −11.6 SE).

---

## 4. The one thing the control table says that the rule does not

```
random exclusion, 50 slots    p5 -4.751   p50 -4.077   p95 -3.173     FIXED -3.616
random exclusion, cell 2      p5 -2.062   p50 -1.087   p95 +0.335     FIXED -0.718     util 62.4%
```

**The random-exclusion control's p95 is *better* than the full FIXED book, on both books** — and
on cell 2 it is **net-positive, +0.335 bp/bar, at 62% utilisation.** That is not the rule; it is
the p95 of fifty random thinnings and it is selection. But it is D419's closing sentence arriving
from another direction: **when the marginal trade loses to its round trip, a book that takes fewer
of them is better net, and it is better by cost, not by selection.** The random control thinned
utilisation to 62%; EPISODE, thinning structurally, kept it at 89%. The random control's
advantage is that it traded less; the rule's disadvantage is that it did not.

---

## 5. Predictions, and what this implies for the question the principal actually asked

| | prediction | outcome |
|---|---|---|
| X-a | re-entry share 20–35%, higher in cell 2 | **size wrong** — 52% / 72%; direction right |
| **X-b** | **T1 fails with the wrong sign** | **correct — −2.5 SE, medians and trims agree** |
| X-c | utilisation > 98%, turnover within 1 pt | correct — 98.8%, 19.76% |
| X-d | T2 fails inside 2 SE | correct — −0.8 SE |
| X-e | T3 fails | correct — at the control's median |
| X-f | COOLDOWN20 removes more and does worse in both lenses | **half** — removes more and is worse on the book; per trade it is *less* wrong than EPISODE, because a plain clock discards fewer of the good re-entries |

Four of six on the letter, six on direction.

**For the revisit.** The principal said the goal is *to capture the deeper zone*, and that the
momentum-stall study (D416) was an earlier attempt. This record says the deeper zone is
**identifiable at the touch** — it is a re-entry, a name whose earlier zone was touched recently
and is now touching a lower one — and that **it pays 77% more than a first entry, pooled, with the
median three times higher.** Every rule discussed so far — the cooldown, the episode, and the
structural stop-out consumption the principal described — *excludes* that population. **The
condition that captures it is the inverse: a name's second or later zone in a continuing decline,
as an entry preference or an entry requirement.** That is knowable at `t`, it is a selection
condition rather than an exit, and it has not been tested. D416's stall entered *later in time*;
this would enter *deeper in price*, on the day of the touch, at the close.

It is not built here. It is the question to write when this is revisited.

**Disposition is the principal's.**

---

## 6. R13

Twentieth look by object on price levels; seventh on execution. No new data spent.

**Evidence:** `data/d420_episode.json` — both lenses, all three rules, the 24 books, the control
distributions, and P4's ledger for KIM (which also shows a data property worth knowing: distinct
zones on one name can share an arming day and a touch day, and the book's one-position-per-name
rule is what keeps them from double-entering). Runner `scripts/run_d420_episode.py`, whose
simulator with the rule off reproduces D419's FIXED book bit-identically.
