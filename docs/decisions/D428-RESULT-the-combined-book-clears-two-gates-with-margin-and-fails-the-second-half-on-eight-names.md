# D428 RESULT — the combined book clears two gates with margin, and fails the second-half gate on eight names

**FAILS THE CANDIDATE CONDITION: T1 PASSES, T2 PASSES, T3 FAILS.** Pre-registration `99b2b8d`
predates the runner and this file (R8). **The ledger does not move. Nothing was admitted. No holdout
of any kind was read — the condition that would have made this a candidate was not met.** Daily bars.

Cost: 344 s (90 books in 11 s; one worker measured at 972 MB before eight were launched; 200
control books).

```
[STAGE0] 2,649 / 303 / 1,416 reproduce
[P2]     sim4 on this pool == D421's simulate, with and without the priority -- gross AND cost series bit-identical
[COST]   the borrow term is zero on every long and positive on every short; the LONG book is identical with and without it
[RECON]  90 books;  [CHUNK] worker draw 0 == in-process
```

---

## 1. The bar — N = 4, priority, 1% borrow

```
T1  net bp/bar, mean over seeds        +5.651 ± 2.130      +2.7 SE     PASS
T2  vs random cell-2 pools of 2,649    p50 −0.497  p95 +1.516 (±0.127)   +32.5 SE   PASS
T3  2021–2026 net                      +8.362 ± 4.782      +1.7 SE     FAIL
```

**This is the first pre-registered book in the line to clear its own net gate and its random-pool
control with margin, on every seed (+5.41 / +5.77 / +5.78).** It fails the third gate — the window
that excludes 2020 — not because that window is worse (its mean is *higher*, +8.4) but because it
is 951 trades over six years with a bootstrap SE of 4.8, **and eight names carry half its P&L.**
That is the honest shape of the second half: the highest mean and the thinnest evidence.

---

## 2. Per trade — the pool of 2,649

```
                       n     gross   median   cost    NET    win   payoff   trim    ex-top   ex-bot
pool                2,649   +84.48   +63.3   34.5   +49.9  54.8%   1.20   +75.9   +54.0   +107.2
  2018+             1,410  +109.06   +89.4   35.3   +73.8  55.6%   1.22   +97.6   +72.3   +134.9
  2021–2026           951  +117.12   +91.5   36.5   +80.7  56.2%   1.19  +110.6   +74.5   +147.0
pool long           1,416   +79.93   +99.0   35.1   +44.9  58.6%   1.00   +76.8
pool short          1,233   +89.71   +12.2   34.0   +55.8  50.4%   1.46   +75.9   (2018+ median −10.7)
priority sub-cell     303  +140.83   +76.3   34.3  +106.5  56.1%   1.51  +131.6
|r| ≤ 50% variant   2,647   +79.86   +62.9   34.5   +45.3                          (two trades = −4.6)

concentration      names   to half   top1   top5   top10   years+   top name    top year
pool                 406      18      5.8%  20.1%  33.2%   16/17     RVMD       2026  19.0%
pool 2021–2026       227       8     11.7%  38.6%  61.8%    6/6      RVMD       2026  38.2%
pool long            336      11      9.7%  29.6%  48.3%   12/17     U          2026  19.8%
```

The top trade is named and its bars were read: **RVMD, short at 34.12 on 2023-10-16** after a
three-session +40% run on 10.6M and 8.4M shares, covered at 18.36 after a gap to 18.91 on 19.3M
shares — a real event, 2.8% of P&L, not the fixture. **The cheap tercile's mean survives the trim
(+75.9), the top-1% removal (+54.0) and the |r| ≤ 50% cut (+79.9).**

**The gap filter did not add on cheap names.** D427's cheap tercile alone was +86.48; cheap ∧
gap ≥ 3 is +84.48. X-a predicted +88–96 by adding D427's two effects; they do not add.

**The short half is the same object it was in D422:** a mean of +90 on a median of +12 (−11 in the
second half), payoff 1.46, carried by its right tail. The long half is the ordinary distribution
(median +99, win 58.6%). **At 10% borrow the short half costs the N=4 book 0.93 bp/bar** — three
times X-e's guess, because shorts are 47% of the trades and 20 bp a trade at this turnover is not
small.

---

## 3. The slot sweep — the pool fills three, and the book peaks at three

```
N   arm       gross     net    cost   util   trades  per trade   net by seed              mean ± SE      2021–26 ± SE
2   PRIO    +10.311  +5.549   4.762  67.9%   1,118    +75.96    +5.55 +6.33 +5.73    +5.87 ± 2.88    +8.63 ± 6.66
3   PRIO    +10.757  +6.562   4.195  60.9%   1,505    +88.30    +6.56 +7.07 +6.93    +6.85 ± 2.47   +10.23 ± 5.60
4   PRIO     +9.086  +5.407   3.679  53.7%   1,769    +84.61    +5.41 +5.77 +5.78    +5.65 ± 2.13    +8.36 ± 4.78
5   PRIO     +7.671  +4.449   3.222  47.2%   1,944    +81.25    +4.45 +4.61 +4.42    +4.49 ± 1.79    +6.44 ± 4.03
7   PRIO     +5.902  +3.408   2.494  36.6%   2,111    +80.59    +3.41 +3.51 +3.52    +3.48 ± 1.30    +5.30 ± 2.89
10  PRIO     +4.292  +2.490   1.802  26.5%   2,186    +80.85    +2.49 +2.56 +2.48    +2.51 ± 0.94    +3.83 ± 2.05

4   LONG     +5.001  +2.953   2.048  30.0%     988    +83.38    +2.95 +3.15 +3.16    +3.09 ± 1.65    +5.40 ± 3.77
4   PRIO-b10 +9.086  +4.480   4.606  53.7%   1,769    +84.61    +4.48 +4.84 +4.85    +4.72 ± 2.13    +7.40 ± 4.77

priority delta (PRIO − NOPRIO):  N2 +0.33 ± 0.47   N3 +0.22 ± 0.30   N4 +0.14 ± 0.19   N5 +0.02   N7 +0.00   N10 0
random-priority control at N4:   delta +0.138 vs random-priority p50 −0.231  p95 +0.164   inside the null
```

**Net per bar rises as slots fall — to a peak at N = 3, not monotonically to N = 2.** X-b
predicted monotone; at two slots the book turns away enough trades on cluster days that the
ones it keeps are worse (per trade +76 against +88 at three), and net falls back. **Utilisation
at N = 4 is 54%, not the 79% the occupancy arithmetic gave**, because the pool's events cluster
— 1,564 event days of 4,187, a p95 of four events on an event day — so a four-slot book is
empty most days and full on the days that matter. Capacity here is not a mean; it is a queue.

**The priority is worth nothing that a random priority isn't.** +0.14 at N = 4, inside the
random-priority null; its per-trade +141 is the days it lands on (D427 §1), and on a book that
is half empty a priority rarely decides anything.

**Every book at every N is net-positive on every seed**, at 1% and at 10% borrow, long-only or
not. The ten-slot book here (+2.51) is below D427's cheap-alone ten-slot book (+3.12) for the
same reason the per-trade table gave: the gap filter removed trades that were paying on cheap
names.

---

## 4. Predictions — three of seven

| | prediction | outcome |
|---|---|---|
| X-a | pool +88..+96 gross, net +52..+62 | **+84.5 / +49.9 — the layers did not add** |
| X-b | monotone in N; N10 +2.7..+3.4, N4 +5..+7, N2 +6..+9 | **peak at N3 (+6.85)**; N4 +5.65 ✓; N10 +2.51, N2 +5.87 both below |
| X-c | priority +0.2..+0.8 at N4, ≤ 0.1 at N10, inside its null | +0.14, 0.00, inside — the null part held |
| X-d | N4 beats random pools by > 2 SE | ✓ +32.5 |
| X-e | 10% borrow costs 0.3..0.7; LONG N4 +3..+5 at ~40% | **borrow 0.93**; LONG +3.09 at 30% ✓ |
| X-f | \|r\| > 50% moves the mean < 5 bp | ✓ −4.6 |
| X-g | T1, T2, T3 all hold | **T3 fails** |

Two lessons the misses share: **layers seen separately do not add** (cheap +86 and gap +3 gave
+84 together), and **a pool's capacity is its clustering, not its mean rate.**

---

## 5. What this leaves

1. **Not a candidate.** The declared condition was all three gates; the second-half gate is at
   +1.7 SE on 951 trades with eight names to half the P&L. **The holdout stays shut.**
2. **The first book in the line that clears its net gate and its control with margin** — +5.65
   ± 2.13 at four slots, positive on every seed and at every slot count, robust to the trim, the
   top 1%, the corporate-action cut and a 10% borrow. That sentence and the previous one are both
   true, and the second does not override the first.
3. **The construction's capacity is three positions**, not ten, and a book sized to it earns
   +6.9 bp/bar on the spent data. Everything above three slots dilutes; below it, cluster days
   are turned away.
4. **The second half is where the mean is highest and the evidence thinnest:** +117 gross per
   trade in 2021–2026, on 227 names, eight of which are half of it, and 2026 — a partial year —
   is 38%. Any reading of this book that does not carry that sentence is wrong.
5. **The short half is still a lottery at a positive mean, and borrow is not small on it.** A
   long-only book at four slots is +3.09 with no borrow exposure at all; that is the trade-off
   the principal would be choosing between, and this record does not choose.

**Disposition is the principal's.**

---

## 6. R13

Twenty-eighth look by object on price levels. No new data spent.

**Evidence:** `data/d428_combined_book.json` (the trade tables, 90 books, the sweep, both
controls). Runner `scripts/run_d428_combined_book.py`; pool `scripts/d428_pool.py`, committed
with the pre-registration.
