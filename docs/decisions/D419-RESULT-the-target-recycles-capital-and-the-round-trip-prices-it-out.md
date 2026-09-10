# D419 RESULT — the target does recycle capital into better trades, and the round trip prices it out

**FAILS THE BAR in all three families, on both gates, on both books.** Pre-registration `346c671`
predates the runner and this file (R8). **The ledger does not move. Nothing was admitted. No
holdout was read (the principal's standing decision).**

Cost: 85 s for 60 books and the oracle; 351 s for 1,200 control books on 8 processes.

---

## 1. The book, and the assertions that make it one

```
[RECON] book == ledger to <1e-9 on FIXED, SL, TS, TP, SLTP and the oracle
[HOLD]  the no-exit book holds 4.999 bars (delistings are the 0.001)
[MECH]  the target's winners run 4.30 bars against losers 5.00
[SIGN]  the oracle earns +80.16 bp/bar against FIXED's +2.82
[CHUNK] worker draw 0 == in-process draw 0 to 1e-12
[NUISANCE] every control's mean run equals its rule's to two decimals, all six cells
```

D295's bar order, D295's reconciliation, D295's control. **The mechanism the principal pointed
at has its precondition:** utilisation on the 50-slot book is **99.5%** and **99.9% of early frees
found a fresh touch at that close** (X-a). A freed slot never idles. Whatever recycling can do,
this book lets it do.

---

## 2. THE BOOKS — 50 slots pooled, seed 419

```
         gross     net     cost   trades   run   early   turnover   per-trade
FIXED   +2.817   -3.616   6.434   40,977  5.00    0.0%   19.90%/d    +14.16 bp
SL      +2.663   -4.776   7.440   47,432  4.31   31.3%   23.04%/d    +11.56
TS      +2.609   -5.764   8.374   53,177  3.84   58.3%   25.83%/d    +10.10
TP      +3.161   -3.784   6.944   44,129  4.64   20.4%   21.43%/d    +14.75
SLTP    +3.150   -4.977   8.127   51,851  3.94   51.1%   25.18%/d    +12.51
```

**The first thing the book says is about the book, not the exits: it is net-negative at every
rule, including no rule at all.** A 20%-a-day turnover against a 27 bp median round trip costs
**6.4 bp/bar** and the fixed exit earns **2.8**. That is ADDENDUM 2's 0.41× coverage arriving
through the path-variant lens with the same answer. On the cell-2 book it is 5.3 against 4.6 —
closer, still under.

**The second thing is what the principal predicted and D417 could not see.** The target *raises*
gross — +0.34 bp/bar over FIXED at this seed — and its per-trade mean is *higher* than FIXED's
(+14.75 against +14.16) even though every one of its early exits forfeits the D417 remainder.
**Recycling the slot into a fresh, front-loaded entry more than pays for the forfeit, gross.** Then
its turnover rises from 19.9% to 21.4% a day, the extra round trips cost 0.51 bp/bar, and net it
is 0.17 *below* the fixed exit.

---

## 3. The bar

### T1 — family net minus FIXED net, mean over three seeds, monthly block-bootstrap SE

```
                     gross Δ      NET Δ            SE      seed spread
50-slot pooled  SL   -0.565     -1.568 ± 0.677   -2.3         0.98     FAIL
                TS   -0.593     -2.526 ± 0.630   -4.0         0.94     FAIL
                TP   +0.147     -0.352 ± 0.532   -0.7         0.54     FAIL
                SLTP -0.109     -1.790 ± 0.582   -3.1         0.66     FAIL
cell-2 10-slot  SL   -1.128     -1.921 ± 0.945   -2.0         0.90     FAIL
(secondary)     TS   -0.977     -2.409 ± 1.083   -2.2         1.49     FAIL
                TP   +0.732     +0.351 ± 0.804   +0.4         1.70     FAIL
                SLTP -0.432     -1.734 ± 0.995   -1.7         0.75     FAIL
```

**The stop and the trail lose in both lenses and on both books.** The target is the only family
with positive gross deltas everywhere; **on the cell-2 book it is net-positive against the fixed
exit, +0.35 bp/bar — at 0.4 SE, with a seed spread of 1.7 bp/bar, which is to say it is noise**
(X-d, exactly as stated).

### T2 — against turnover-matched random exits, 200 draws each

```
              observed net   ctrl p5    p50      p95     obs − p50    margin to p95
SL   N50        -4.776      -5.024   -4.548   -3.992     -0.228        -33.2 SE   FAIL
SL   C2N10      -3.111      -3.783   -2.628   -1.567     -0.483        -31.6 SE   FAIL
TS   N50        -5.764      -6.003   -5.342   -4.781     -0.423        -36.9 SE   FAIL
TS   C2N10      -3.909      -4.501   -3.435   -2.441     -0.474        -31.1 SE   FAIL
TP   N50        -3.784      -4.407   -4.003   -3.541     +0.220        -12.8 SE   FAIL
TP   C2N10      -1.206      -2.824   -1.990   -1.070     +0.784         -3.2 SE   FAIL
```

**This table separates information from turnover, and it separates the three families cleanly.**
Each rule is compared with a book that exits after random holds drawn from *that rule's own* run
distribution — same turnover, same cost, same refill frequency, no information.

- **The stop and the trail are WORSE than random exits with the same turnover**, below their
  controls' medians in all four cells. A stop does not merely cost its forfeit; it chooses *which*
  trades to forfeit, and it chooses badly — the ones about to recover.
- **The target is BETTER than random exits with the same turnover**, above its control's median in
  both cells, by +0.22 pooled and +0.78 on cell 2. **The target carries information: it exits
  after the move, and a random exit does not know when that was.** It does not reach the p95, and
  on the cell-2 book it misses by 3.2 SE.

X-f predicted this ordering and got the gate wrong: the target's advantage over random is real
and is not large enough to clear.

---

## 4. THE REPLACEMENT PREMIUM — the swap, priced

For every early exit, on the 50-slot book: what the arriving trade earned over its own life, minus
what the departing one would have earned from its fill to its scheduled exit. Three seeds:

```
                   n       premium         arriving     forfeited
TP   s419        8,997    +13.38 ± 8.23    +11.90        -1.48
TP   s4190       8,921     +8.00 ± 8.11     +7.73        -0.27
TP   s41900      8,831     +8.18 ± 8.23    +11.04        +2.86
SL   s419       14,857     +1.94 ± 5.85    +16.03       +14.09
SL   s4190      14,942     -9.94 ± 5.70     +8.21       +18.15
SL   s41900     14,800     +0.53 ± 5.81    +11.82       +11.29
```

**The target forfeits nothing** — the departing trade would have made −1.5, −0.3, +2.9 bp after
the target — **and the arriving trade earns +8 to +12.** A target swap is worth about **+10 bp
gross.** It pays a ~27 bp round trip. **Net, each swap is about −17 bp, and that is the whole
result in one line.**

**The stop forfeits +11 to +18 bp** — the trade it cut would have recovered that much — and the
arriving trade earns +8 to +16. A stop swap is roughly a wash gross, a loss of the round trip net,
and it moves 15,000 times.

Slots idled on 6 to 87 of those swaps. The mechanism had its bench.

---

## 5. THE SHAPE THAT SAYS WHAT THE MECHANISM IS — recycling scales with how binding the cap is

```
seed 419        FIXED gross    FIXED net    util     TP − FIXED gross    TP − FIXED net
N = 25            +3.013        -3.230      99.8%        +1.087             +0.655
N = 50            +2.817        -3.616      99.5%        +0.343             -0.167
N = 100           +2.441        -3.873      95.3%        -0.072             -0.516
```

**The target's advantage over the fixed exit is monotone in scarcity.** At 25 slots — a queue of
fresh cell-2 touches always waiting — the target is **+1.09 bp/bar gross and +0.66 net** over the
fixed exit at this seed. At 100 slots there is nothing better to recycle into and the target is
worse on both. **This is opportunity cost measured directly**, and it is exactly the mechanism the
principal's question pointed at: **the more capital-constrained the book, the more a freed slot is
worth, and at 25 slots it is worth more than the round trip.**

It is shape. `N = 25` was declared shape, it is one seed, and the pre-registration said the gate
was the 50-slot book. **It is recorded because it is the finding that would decide what a smaller
book does, and it is not promoted because it was not the declared test.**

---

## 6. Predictions

| | prediction | outcome |
|---|---|---|
| X-a | utilisation > 90%, same-day refill > 95% | correct — 99.5%, 99.9% |
| X-b | TP gross +0.2 to +0.6 over FIXED; SL, TS below | direction correct; **+0.147 over three seeds, under the floor** |
| X-c | net: every family fails T1 pooled | correct — the recycled trade earns +13 and costs 27 |
| X-d | cell-2 TP net-positive, inside 2 SE | correct — +0.351 at +0.4 SE |
| X-e | TP premium positive gross, near zero net; SL negative | **half** — TP +10 gross and about −17 net, not near zero; SL's gross premium averages −2.5 over seeds and is noise |
| **X-f** | **TP beats its turnover-matched control gross; SL, TS do not** | **ordering correct, gate wrong** — TP sits above its control's median in both cells and below p95; SL and TS below their medians |

Four of six on the letter, all six on the direction. **The two misses are both the target's
advantage being smaller than I predicted** — real, and not enough.

---

## 7. What this changes in the record, and what it does not

**It changes the explanation.** D417 said *no exit beats the time stop because the expected
remaining move is never negative.* That was true and it was the per-trade lens. **The book lens
says: the target does beat the time stop gross, by recycling into front-loaded entries; the stop
and the trail do not, because they choose the wrong trades to recycle. Neither clears net, because
the round trip is larger than any swap is worth.** The principal was right that the first lens
was missing something; what it was missing has now been measured, and it is +10 bp gross per swap.

**It does not change the disposition.** Every book is net-negative under this cost model, with or
without any exit. **The binding constraint is the round trip, and it binds the fixed exit and the
target alike.** The one place the target clears net against FIXED is a 25-slot book at one seed,
which is shape.

**And it sharpens the D413 cost finding into a design fact:** at ~20% daily turnover, any book on
this construction pays ~6 bp/bar in neutral cost against ~3 gross. **A book that traded a tenth
as often would pay 0.6.** Turnover, not exits, is where this line's cost lives — which is a
statement about the *entry* frequency and the hold, not about anything an exit rule can do.

**Disposition is the principal's.**

---

## 8. R13

Nineteenth look by object; sixth on execution; the first through the book. No new data spent.

**Evidence:** `data/d419_book.json` (60 books, the bar, the premium ledgers, the run
distributions) and `data/d419_book_controls.json` (1,200 control books, six cells). Runner
`scripts/run_d419_book.py`, one simulator serving the books, the oracle and the controls.
