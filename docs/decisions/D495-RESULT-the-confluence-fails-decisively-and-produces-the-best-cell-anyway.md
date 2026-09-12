# D495 — RESULT: the confluence fails decisively, and produces the best cell anyway

**2026-09-12.** Runner [`scripts/d495_agree_confluence.py`](../../scripts/d495_agree_confluence.py) ·
artifact [`data/d495_agree_confluence.json`](../../data/d495_agree_confluence.json) ·
pre-registration [D495 PRE-REG](D495-PRE-REG-does-requiring-the-two-MACD-variants-to-AGREE-help-and-is-any-help-direction-or-just-fewer-trades.md).
State machine from D491, signal code from D484, both unchanged.

---

## 1. The confluence does not help. This is not close.

| statistic | observed | null p95 | margin |
|---|---:|---:|---:|
| **P2 pooled lift, NET** | **−0.2821** | −0.0587 | **−70.0 SE** |
| **P2 pooled lift, GROSS** | **−0.2794** | −0.0609 | **−112.8 SE** |

**Requiring the two variants to agree makes things WORSE**, and the net lift is negative on
**7 of 8 roots**:

    ES -0.08   NQ +0.14   YM -0.37   ZN -0.18   ZB -0.20   GC -0.04   CL -1.00   6E -0.53

**U-a broke** — I predicted the net lift would clear its null. It did not; it went the other way
by seventy standard errors.

### Why, and it is the number I should have checked first

**The two variants agree 66–71% of the time.** My own self-test measured that *independent*
signs agree ~50%, so at 70% these are strongly correlated — which is obvious in hindsight, since
both are MACDs on the same price series.

So requiring agreement removes only ~30% of bars and **barely reduces trading: 1.64 trips per
session against 1.75, just 6.5% fewer**, where I had predicted ≥15% (**U-c broke**).

**There was no frugality to buy.** §2 of the pre-registration split gross from net precisely to
catch the case where a confluence helps only by trading less — and the answer is that it does not
trade meaningfully less, so it has no channel to help through. It just throws away signal.

## 2. And the best cell measured anywhere is an AGREE cell

**NQ, AGREE, minimum hold 5 hours, day session, 1 MNQ: net Sharpe +0.723.**

| | observed | null p95 | margin |
|---|---:|---:|---:|
| **P1 family-max net Sharpe** over the 37 AGREE cells | **+0.723** | +0.4036 (SE 0.017) | **+18.5 SE** |

**C-a ✓ (+0.723) · C-c ✓ (skew −0.05) · C-d ✓ ($180)** → **COMPONENT CANDIDATE: YES**

**The two results are not in conflict.** P1's null prices picking the best of 37 cells across all
eight roots, so NQ's cell clearing it is not "best of 8 roots" unpriced. What failed is the
general claim that agreement helps; what passed is one specific cell.

### It is materially stronger than D491's candidate on every axis

| | D491 (B1, M=3) | **D495 (AGREE, M=5)** |
|---|---:|---:|
| net Sharpe | +0.583 | **+0.723** |
| distance from zero | 1.59 SE | **1.97 SE** |
| **margin over the null p95** | **0.20** of a Sharpe SE | **0.87** of a Sharpe SE |
| mean across M | +0.491 (**fails C-a**) | **+0.554 (clears C-a)** |
| shape across M | +0.49, +0.43, +0.58, +0.46 — noise | **+0.463, +0.501, +0.530, +0.723 — monotone** |
| trips/session | 1.17 | **1.02** |
| skew | −0.04 | −0.05 |

**The M profile is the important line.** D491's best was a 0.15 bump inside one Sharpe SE — I
called it a lucky draw and it was. **This one rises monotonically with the minimum hold**, and
the mean across M clears C-a on its own. That is a pattern rather than a pick, and it is the
first support the principal's minimum-hold idea has had: **V-b failed on the index roots in D491
because the window gave it no room, and here the same idea shows a clean monotone gradient.**

## 3. Your 30% haircut turns out to be inert, which moves the bar

Best-day share on the NQ cells: **6.7% to 13.3%**, against the 30% cap. **The haircut bites on
1 of 13 profitable cells and on none of NQ's.**

    NQ AGREE M=5   total $15,393   best day $1,031   share 6.7%   haircut $0   recognised $15,393
                   net Sharpe +0.723  ->  recognised +0.723   (unchanged)

**So D496 (`scripts/d496_book_sharpe_bar.py`, `data/d496_book_sharpe_bar.json`)'s bar should be read at its NO-HAIRCUT column.** A $500 fee needs
**S = 0.316**, not the 0.428 the flat-30% assumption implied. Pricing the candidate against the
relaxed P4:

| | Sharpe | E[profit before breach] | E[life] |
|---|---:|---:|---:|
| **NQ AGREE M=5** | **+0.723** | **$1,461** | **178 d (0.71 yr)** |
| NQ AGREE, mean across M | +0.554 | $1,076 | 178 d |
| D491's B1 M=3 | +0.583 | $1,054 | 155 d |

**It clears the relaxed P4 at any realistic fee, and it does so at the honest mean-across-M
level too.** Still short of the preferred ≥1 year, which is not a hard rule.

## 4. CL is not a second component, and the reason is instructive

**CL B2 has the highest GROSS Sharpe measured anywhere — +1.09 — and a net Sharpe of +0.108.**
Cost eats 90% of it. It fails C-a badly, and the AGREE arm destroys it outright (−0.887).

**U-d broke** on exactly this: I predicted CL would be the positive non-index root. **No
non-index root is net positive.**

And the gross column shows the same thing across the board — **ES B2 +0.66, GC B1 +0.60,
ZB B2 +0.49, CL B2 +1.09, all with negative net.** The signal is real in several places and
**cost kills it everywhere except NQ.**

**NQ survives despite having the worst cost in ticks** (MNQ at 7.009 against MES's 3.409),
because its σ is the largest (169–213 ticks). **It is the cost-to-σ ratio that decides, not the
cost** — D486 §1's point, now confirmed by the one root that lives.

**So we have one component, not two.** D496 already showed one is enough for the relaxed P4, so
this is survivable — but there is no second arm in sight and the vault is still empty.

## 5. Predictions

| | prediction | outcome | |
|---|---|---|---|
| **U-a** | net lift clears its null | **BROKEN** | −70.0 SE, the wrong way |
| **U-b** | gross lift does NOT clear | HELD | trivially — it is −112.8 SE |
| **U-c** | AGREE trips ≥15% fewer | **BROKEN** | 6.5%; the variants agree 70% of the time |
| **U-d** | only NQ and CL net positive | **BROKEN** | only NQ; no non-index root |
| **U-e** | ZB fails C-d, ZN fails C-a | HELD | |

## 6. What this changes

- **The confluence is closed as a general lever** — −70 SE pooled, negative on 7 of 8 roots, and
  the mechanism I proposed for it (frugality) does not exist because the variants already agree
  70% of the time.
- **The candidate is upgraded**: +0.723, a 0.87-SE margin over a multiplicity-aware null, a
  monotone M profile, C-a cleared on the mean across M, and **zero haircut**.
- **The minimum-hold idea has its first support** — a clean monotone gradient where D491 had
  none, because AGREE trades less (1.02 trips) and so the hold has room to matter.
- **Nothing is entered.** One cell, in-sample, selected from 37, on one root out of eight. The
  ledger's discipline says **the sealed 2024+ slice promotes or removes a candidate**, and
  2024+ remains unread.

## 7. Checks

26 self-test checks. The AGREE gate is proven to be a strict **subset** of each variant's
entries, to fire ~50% of the time on independent signs (0.498 measured — which is what made the
real 70% agreement rate legible as a finding rather than a bug), and to reproduce a signal
exactly when both inputs match.

**The P5 haircut is checked on hand-computable cases**: total 1900 with a best day of 1000 gives
excess 430 and recognised 1470; an even series is untouched; it bites exactly at the 30%
threshold (31/23/23/23 bites, 29/24/24/23 does not); a **losing** series is never haircut; it can
only reduce profit; and **D496's flat 30% is proven to be an upper bound on the real bite.**

`net = gross − cost × trips` is asserted exactly, with the trip count identical either way, which
is what makes the gross/net decomposition trustworthy. All six micro costs are asserted present,
and **6E is asserted to use the Globex $6.25 tick rather than ClearPort's $1.25**, with its
venue-split warning still in place.

**Profiled before launch:** 146 ms per draw → 4.9 min.

## 8. What this does not do

- **It admits nothing** ([R15](../RULES.md#r15)). Nothing enters `COMPONENTS_PROP.md`, the vault
  or either book.
- **Execution is open-of-next-segment at the measured half-spread** — no queue, no partial fills,
  no slippage on a flip. Fills need `mbp-10` (D471 §1). **Every figure is an upper bound.**
- **The volume-clock exit (D472, +10.4%) is still not applied**, so the net figures understate by
  roughly that much.
- **Nothing is elevated** into `FINDINGS.md` or `RULES.md`.
