# D338 RESULT — `retrace_leg` beats all 200 rotations on every statistic, and its book is five names; the top trade is a $0.18 stock that quadrupled overnight

**Status:** RESULT. Pre-registered at `bc2d27c`, runner at `add0fe3` — both before this file
existed (R8). D333-bounded panel, D334-rebuilt cache, F0 deal filter, PUB primary.
**Date:** 2026-09-05
**Area:** Strategy research · **personal track**

**No holdout testing. Holdout reads spent: 0. Programme total: 0.**
**`retrace_leg` is NOT declared a candidate. Book: empty.**

---

## 1. The top trade, named — the rule FINDINGS §18 wrote after PNK, applied

**VSA, long, entered 2025-01-31, held one bar, +33,035 bp = 15.9% of the ledger's P&L.**

| date | open | high | low | close | volume (adj.) | r1 | raw close move | dividend |
|---|--:|--:|--:|--:|--:|--:|--:|---|
| 2025-01-30 | 111.000 | 111.000 | 87.501 | 90.550 | **2,738** | — | −14.2% | — |
| 2025-01-31 | 195.050 | 670.000 | 190.000 | 389.200 | 1,453,986 | **+329.8%** | +329.8% | — |

It is a real move on the tape: no dividend on either bar, and the panel's return equals
the raw close-to-close move to the last digit. **D333's bound has nothing to do with
this one.** Two reverse splits on file after the trade (1-for-50 on 2025-12-22, 1-for-10
on 2026-05-26) mean the adjusted $90.55 close was a **raw price of about $0.18**, and the
2,738 adjusted shares are the day's whole volume in a name whose trailing 63-day dollar
volume at entry was **$539k — the 4th percentile of the live cross-section.** The book
bought a quarter of its notional in it at the close and sold at the next close for +330%.

The top five, with the biggest day in each hold and the entry-day liquidity (diagnostic,
post hoc, labelled):

| trade | side | entry | hold | P&L bp | share | biggest day | raw close there | DV63 at entry | DV pct | raw price at entry |
|---|---|---|--:|--:|--:|---|--:|--:|--:|--:|
| **VSA** | long | 2025-01-31 | 1 | +33,035 | 15.9% | +329.8% | $389.20 adj. | $0.54M | **4.2%** | ~$0.18 |
| **RXT** | long | 2026-02-05 | 9 | +21,395 | 10.3% | +227.0% | $1.37 | $1.30M | **7.2%** | $0.48 |
| **NKA** | long | 2015-06-03 | 8 | +18,904 | 9.1% | +203.1% | $3.97 | $0.37M | **1.3%** | $1.51 |
| **FGP** | long | 2018-12-06 | 1 | +6,866 | 3.3% | +68.4% | $1.28 | $0.83M | **3.7%** | $0.76 |
| CHK | short | 2020-06-09 | 1 | +6,361 | 3.1% | −66.0% | $23.75 | $64.5M | 68.5% | $69.92 |

None is in an F0 window; none has a dividend on its big day; every one is a genuine
price move. **Four of the five are sub-$2 stocks in the bottom 7% of the universe by
dollar volume, and all four fall below dv28's 28th-percentile cut** (the cut sat at
$6.8M–$10.2M on those days). Three of the five are one-bar holds: the signal is computed
at a close, the book is filled at that same close, and the position is out at the next.
That convention is the whole D300 family's and is a fiction on a 2,738-share day.

The largest name by contribution is VSA at **20.1%** of P&L. **Five names of 673 are
half the P&L.** D322's incumbent was six names of 718 — and one of those was PNK.

## 2. The four groups

### Group 1 — performance, the same ledger costed under both conventions

| N=2 symmetric, k=20, F0 | PB | **PUB** |
|---|--:|--:|
| gross bp/bar | +32.37 | +32.37 |
| cost bp/bar | 8.94 | 13.45 |
| **net bp/bar** | +23.43 | **+18.93** |
| vol bp/bar | 549.9 | 549.9 |
| gross / net Sharpe | +0.935 / +0.676 | +0.935 / **+0.546** |
| gross t | +3.32 | +3.32 |
| maxDD bp | 13,829 | 13,829 |
| **exposure (bars with a live book)** | **76.1%** | 76.1% |
| fill of 4 slots / names held per bar | 100% / 4.00 | 100% / 4.00 |
| turnover per bar (names held) | 0.0988 | 0.0988 |
| held half-spread bp/side | 21.04 | 32.44 |
| held median price / dollar volume | $31.81 / $20.5M | $31.81 / $20.5M |
| 2c = round trip / 2 | 45.23 | 68.03 |
| mean move per trade / over 2c | +165.1 / 3.65× | +165.1 / 2.43× |
| **breakeven half-spread per side** | 80.3 = 3.82× | **80.3 = 2.48×** |
| GC+HTB borrow → net | 0.329 → +23.11 | 0.329 → **+18.60** |
| house 300 borrow → net | 1.184 → +22.25 | 1.184 → +17.74 |
| HTB share of short position-bars | 7.4% | 7.4% |

Reproduces D335's cells to 0.0. Gross Sharpe 0.94 on a **550 bp/bar** book: annualised
vol of 87%, a drawdown of 138 notional-percent. **Q9 falsified**: the book is live on
76% of bars, none before 2013 — the structure score needs two confirmed pivots inside a
year and the cache's warm mask, and the pre-registration assumed a book live from 2010.
The "17 calendar years" in Q4 was the same mistake; there are 14.

### Group 2 — the trade distribution, both tails trimmed (variant ledger, 1,256 trades)

| | |
|---|--:|
| mean / **median** bp | +165.1 / **+233.9** — mean below median |
| win rate / payoff | 72.6% / 0.60 |
| mean win / mean loss | +620 / −1,042 |
| holding run mean / median / max | 10.1 / 7 / 20 bars |
| skew / kurtosis | +8.8 / 165 |
| trimmed 12 each side: ex-top / ex-bottom / **both** | +70.3 / +221.1 / **+125.9** |
| top 1% share / bottom 1% share of P&L | **+58%** / −33% |
| top 1% mean / bottom 1% mean | +9,989 / −5,641 |

**Q2 falsified, and in the direction that matters.** The mean is below the median, as
predicted, but the *right* tail is the larger one — +58% against −33% — and the
symmetric trim moves the mean by −39 bp, not under 15. **The ex-top-1% mean is +70.3 bp
against a PUB round trip of 68.0: remove the twelve best trades and the book is at
breakeven.** The symmetric trim is the honest central estimate (reporting rule 2) and it
is +125.9, 1.85× the PUB cost — the core pays, the tails decide by how much, and the
right tail is four penny stocks.

Invariant lens, PUB, per trade: long +46.2 net on +110.0 gross (t 3.36, 2,213 trades);
short −29.0 on +31.7 (t 1.21, 2,053). Unchanged from D335.

### Group 3 — what the winners depend on (PUB, each cut charged its own 2c)

| | |
|---|--:|
| names traded / **names to half the P&L** | 673 / **5** |
| top 1 / 5 / 10 name share | 20.1% / 51.5% / 65.8% |
| calendar years (2013–2026) | 14 |
| years gross-positive / **net-positive PUB** / net-positive PB | 11 / **8** / 10 |

| cut | P&L share | trades | mean bp | own 2c | ×2c | net per trade |
|---|--:|--:|--:|--:|--:|--:|
| dead (26% of trades) | 16.4% | 326 | +110.3 | 79.5 | 1.39× | +30.8 |
| alive | 83.6% | 930 | +184.3 | 63.8 | 2.89× | +120.5 |
| era, first half | 23.9% | 631 | +81.7 | 62.2 | 1.31× | +19.4 |
| **era, second half** | **76.1%** | 625 | +249.2 | 75.5 | 3.30× | +173.7 |
| price low (≤ $19.15) | 46.2% | 419 | +213.7 | 108.5 | 1.97× | +105.1 |
| price mid | 20.6% | 418 | +104.8 | 62.5 | 1.68× | +42.3 |
| price high (> $51.35) | 33.2% | 419 | +176.5 | 55.3 | 3.19× | +121.2 |

PUB net by year: 2013 +71.5 · 2014 −0.3 · 2015 +46.4 · **2016 −49.0** · 2017 −16.3 ·
2018 −4.2 · 2019 −10.6 · 2020 +65.4 · 2021 +34.2 · 2022 +19.7 · 2023 +31.5 · **2024 −26.4**
· 2025 +83.7 · 2026 +99.4.

**Q3 and Q4 falsified; Q5 confirmed.** The cheapest tercile is 46% of P&L and pays its
own cost (+105 net a trade on a 108 bp `2c`); dead names are 16%; both eras are
net-positive. But the second half of the sample is three-quarters of the P&L, and
**2025–2026 alone carry VSA and RXT.** Eight of fourteen years are net-positive under PUB;
four of the six losing years are consecutive (2016–2019). The dead-vs-alive split is
clean — this is not a dead-name book — and the price split is not the incumbent's
(46% against 57%). The concentration is in *liquidity*, which group 3 does not cut on.

### Group 4 — the null, p50 and p95

Rank rotation inside the 25-name gate, 200 of 200 draws valid, one simulation per draw
costed under both conventions:

| statistic | score | null p50 | null p95 | null max | p |
|---|--:|--:|--:|--:|--:|
| gross bp/bar | **+32.37** | +5.71 | +12.21 | +15.16 | 0.0050 |
| gross Sharpe | **+0.935** | +0.288 | +0.590 | +0.647 | 0.0050 |
| net Sharpe, PB | **+0.676** | −0.051 | +0.243 | +0.327 | 0.0050 |
| net Sharpe, PUB | **+0.546** | −0.345 | **−0.067** | +0.052 | 0.0050 |

**The score is above the maximum of 200 draws on every statistic.** The gross null has
teeth — a random 4-name book inside the gate makes +5.7 bp/bar at the median and +12.2
at the 95th — and the signal's ordering within the gate is worth +20 bp/bar over it.
**But the net-Sharpe null under PUB has p95 = −0.067, and Q6's teeth clause fails as
written.** The pre-registered stop condition for that case reads: *untrustworthy whatever
the percentile; the null is redesigned before anything is read.* It fires.

What the negative p95 means, stated and not argued away: each draw is costed on the
names it actually holds, so this is a *matched-cost* null, and under the published
convention a random 4-name book inside the gate does not pay its 13 bp/bar. The
percentile on net Sharpe is then partly "the signal beats a control that loses money" —
R7's pathology — and the *gross* null is where the signal is tested. The record put the
teeth clause on net under both conventions; that was the wrong statistic to put it on,
and the correction is a pre-registration, not a footnote here.

## 3. Predictions

| | | outcome |
|---|---|---|
| **Q1** | top trade a price move, no dividend, **< 5%** of the ledger | **FALSIFIED** — VSA is a real move (dividend 0, r1 = raw) at **15.9%** |
| **Q2** | mean below median, left tail larger, trim < 15 bp | **FALSIFIED** — mean below median, but the right tail is +58% against −33%; trim −39 |
| **Q3** | names to half ≥ 40, top-10 < 25% | **FALSIFIED** — **5**, 65.8% |
| **Q4** | PUB net-positive ≥ 11 of 17 years, gross ≥ 13 | **FALSIFIED** — 8 / 11 of **14** |
| **Q5** | *(against)* cheap tercile < 50% and net > 0; dead < 30%; both eras net > 0 | **CONFIRMED** — 46.2% (+105); 16.4%; +19.4 / +173.7 |
| **Q6** | *(load-bearing)* above own null p95 on net Sharpe, both conventions, **p95 > 0** | **FALSIFIED** — above p95 and above the max on both, but PUB p95 = −0.067 |
| **Q7** | HTB < 10%, GC+HTB < 0.5 bp/bar, PUB net after borrow > 15 | **CONFIRMED** — 7.4%, 0.329, +18.60 / +17.74 |
| **Q8** | breakeven ≥ 2.0× held PUB half-spread | **CONFIRMED** — 80.3 bp = 2.48× |
| **Q9** | live > 95% of bars, fill > 99% | **FALSIFIED** — 76.1%, 100% |
| *check* | reproduces D335's F0 cells | 0.0 |

Three of nine.

## 4. Stop conditions, executed

- **Q1's** stop as written presumed a fabricated event and prescribes a data fix. The
  event clause *passed*; the share clause failed. There is nothing to fix in the panel,
  and the failure routes to the concentration branch below.
- **Q2 / Q3 fail** → the book carries a **concentration flag**: five names, one 15.9%
  trade, top 1% of trades = 58%, ex-top-1% at breakeven.
- **Q6's teeth clause fails under PUB** → **the R7 flag is recorded and the result is
  not read as a candidate's**, per the record. The gross null is reported beside it and
  is decisive on the signal; which statistic carries the teeth requirement is fixed in
  the next pre-registration, not here.
- **`retrace_leg` is not declared a candidate.** The "everything holds" branch did not
  fire; the concentration and R7 branches did.

## 5. What this establishes

1. **`retrace_leg` orders the gate.** +32.4 bp/bar gross against a rotation null whose
   maximum in 200 draws is +15.2; gross Sharpe 0.94 against a max of 0.65. That part is
   not in doubt and has now been measured on its own null under F0.
2. **What it orders the gate toward is the illiquid tail.** Four of its five largest
   trades are sub-$2 stocks at the 1st–7th percentile of dollar volume, bought at the
   close on the day before a +68% to +330% gap, three of them held one bar. The held
   *median* dollar volume is $20.5M and says nothing about this; the *top trades* say all
   of it. **D323's finding that `retrace_leg` peaks with dv28 OFF is explained**: its
   P&L lives below the cut.
3. **The core pays, and the tails decide by how much.** Symmetric trim +125.9 a trade
   against a 68 bp round trip; ex-top-1% +70.3, at breakeven. A book whose central
   estimate clears cost by 1.85× and whose headline needs its twelve best trades.
4. **A null's teeth clause belongs on the statistic that tests the signal.** Under a
   heavy cost convention a matched-cost net null goes negative because the *cost* is
   large, not because the null is broken; putting the teeth requirement on it made a
   correct null fail a correct test. Gross for the signal, matched-cost net for the cost.
5. **FINDINGS §18's rule worked exactly once and found a different disease.** Naming
   the top trade after PNK found a fabricated dividend; naming it here found a real move
   the book could not have taken. The rule is extended: **print the entry-day dollar
   volume percentile of the top trades beside their bars.**

## 6. Owed, as pre-registrations

1. **The cell under dv28**, D321's declared variant at its fixed threshold, reported with
   and without as the rule requires — predicted in advance from this record: the top four
   trades leave, net falls materially, concentration falls, and whether what remains
   clears the gross null is the question. Not run here; the diagnostic in §1 is the
   reason to run it, not a result.
2. **The null specification**: teeth on the gross null; the matched-cost net null
   reported beside it as the cost test; the R7 flag defined on the gross null's p95.
3. **A one-bar execution lag** for the whole D300 family: signal at close t−1, fill at
   the open or close of t. Three of the five top trades here are one-bar holds under a
   same-close fill. This is a family-wide convention question and a separate study.

## 7. Assertions

| | |
|---|---|
| **[K]** | cache key matches `cache_key()` with `ragged_panel.py` in the tuple; npz newer than the builder |
| **[F]** | F0 mask: 1,719 filings applied, 2.54% of live name-bars |
| **[1]** | D335's F0 `retrace_leg` cells reproduced to **0.0** — variant net and Sharpe, invariant per trade, both legs, PB and PUB |
| **[A]** | lag audit: the long-leg gate rebuilt from the raw F0 score at t−1 by a direct stable argsort equals the gate on all 200 sampled bars; the rebuild from the score at t differs on 200 of 200 |
| **[S]** | every real trade equals `sgn·Σ(v − mt)` from the ledger to 2.2e-16; a favourable excess path pays positively on every long and every short |
| **[RQ]** | same 1,256 entries/exits under compound accumulation, 1,112 P&Ls differ (+165.1 vs +154.0); group 1 scores the summed ledger |
| **[2]** | 1,256 trades reconstruct gross to −0.15 bp; 4 positions open at T, none before bar 4,171 of 4,187; trade P&L = 2.00× contribution; rejects a ledger missing a trade |
| **[3]** | symmetric trim at k=12; rejects one deeper on the bottom |
| **[N]** | rotating the rank array by 501 bars moves gross +32.37 → −2.99; 200 of 200 draws valid |
| **[B]** | borrow per bar × `cnt1` == per trade to 7.3e-12; house == 300/252 to 0.0 on covered bars |
| **[U]** | score in [−19.17, +24.75]; scale-free on a synthetic path |
| **[6]** | raises on +5 bp handed on 200 masked bars |

**Speed:** 62 s; the null 21 s for 200 draws. Self-test 42 s.

## 8. Files

`data/d338_retrace_leg_candidate.json` · `scripts/run_d338_retrace_leg_candidate.py` ·
the liquidity diagnostic is a scratchpad script whose numbers are quoted in §1 and not
otherwise stored; it reads `X.roll_mean_T(CLOSE × VOL)` at the entry bar, the same array
dv28 cuts on.
