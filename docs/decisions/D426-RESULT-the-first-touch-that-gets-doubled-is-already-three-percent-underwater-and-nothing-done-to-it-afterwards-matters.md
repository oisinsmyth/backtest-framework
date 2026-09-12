# D426 RESULT — the first touch that gets doubled is already three percent underwater, and nothing done to it afterwards matters

**FAILS THE BAR on T1, T2 and T3.** Pre-registration `49997c9` predates the runner and this file
(R8). **The ledger does not move. Nothing was admitted. No holdout of any kind was read.** Daily bars.

Cost: 556 s (15 books in 4 s; the control was slow because each worker rebuilt the zone table —
D423's cached-input worker is the right pattern and this one should not be reused as is).

```
[SIGN]   restart delta == unit 1's move from its old exit to the joint exit, long and short LOG mirror;
         a close through FAR on bar 0 exits both units; the check fires when broken
[STAGE0] 180,050 / 9,411 / 7,974 / adds A 1,022 / B 1,249 reproduce
[X]      undoubled episodes return r_base exactly
[P2]     sim3 (over the panel, two-slot names) == D422's ANY-REQ book with adds off and no levels, and
         == D425's sim2 with ZTP+FAR levels -- both bit-identical
[RECON]  all 15 books;  [CHUNK] worker draw 0 == in-process
```

---

## 1. The bar — version A

```
T1  DD − BASE on the 887 doubled episodes     +0.63 ± 17.15 bp      +0.0 SE     FAIL
T2  DD-A net − ANY-REQ net                    −2.077 ± 0.977 bp/bar −2.1 SE     FAIL
T3  DD-A net vs random cell-2 pools (17,385)  −0.840  vs  p50 −1.150  p95 −0.153 (±0.064)   −10.8 SE   FAIL
```

---

## 2. THE FACT THE PRE-REGISTRATION DID NOT HAVE — a first touch that is doubled is a −327 bp trade

```
rung 1 & cell 2 (7,974)                          n      mean       median    win
a same-side second zone follows within 5      887   −326.73     −278.28   22.7%
no second zone follows within 5             7,087    +74.50      +55.13   56.3%
```

**The subset that gets doubled is not "rung 1, which pays +30". It is the 11% of first touches
the market went straight through.** A second same-side zone forming within five sessions sits
*below* the first (for a long): the price has fallen through the first zone, departed from a lower
base, and come back to touch that. At the moment of the add, unit 1 is underwater by the distance
between the two zones — about 3% — and that is a fact about the *structure* that defines the add,
not about the outcome. (The +74.50 on the complement is look-ahead: it conditions on no second
zone arriving. It says what the −327 says from the other side and is not a trade.)

**Everything in the pre-registration's arithmetic was downstream of "rung 1 pays +30", and every
prediction was wrong.** The doubled episodes' BASE is −307 per episode; the restart, the stops and
the double-down move that by +4.6, −2.0 and +0.6 with SEs of 9–17. **On a trade that has already
lost 3%, what is done in the next five sessions is noise.**

```
doubled A (887)     BASE −307.41   RESTART −302.77 (+4.64 ± 11.87)   STOPS −309.42 (−2.01 ± 8.95)   DD −306.78 (+0.63 ± 17.15)
   unit 1 alone     BASE −326.73  →  DD −324.09          unit 2 alone     BASE +19.32  →  DD +17.31      levels fire on 40.9%
doubled B (1,086)   BASE −259.12   RESTART −256.82 (+2.31)           STOPS −257.28 (+1.85)           DD −253.12 (+6.00 ± 15.27)
all rung-1 (7,974)  BASE  +32.02   DD +32.09 (+0.07 ± 1.91)
```

**And the second unit is not the +45 rung 2 either: it pays +19.** The rung-2 premium is not
uniform in the gap to its prior touch:

```
rung 2 & cell 2 by gap    all              same-side prior        opposite-side prior
gap 1–2                  +28.77 ± 14.2     +29.98 ± 14.5  (1,438)   +13.95 ± 61  (117)
gap 3–5                  +56.66 ± 18.2     +43.79 ± 17.6  (1,193)  +110.19 ± 59  (287)
gap 6–10                 +61.02 ± 13.8     +35.96 ± 15.4  (1,460)  +118.72 ± 28  (634)
gap 11–20                +38.68 ±  9.4     +45.61 ± 13.0  (2,280)   +30.79 ± 14  (2,002)
the prior's own 5-day return, same-side priors in cell 2:
gap 1–2  −276   gap 3–5  −467   gap 6–10  −94   gap 11–20  +174
```

The second zone that arrives one or two sessions after the first pays the least (+30), and its
prior is a −276 trade; at gap 3–5 the prior is −467. **The "second zone pays double" of D421/D422
is the second zone that arrives after the first trade has *resolved* — gap 6–20 — not the one
that arrives while it is being run over.** And the one lead this table holds, reported with its
noise: **a second zone whose prior touch was the opposite side, 3–10 sessions earlier — the swing
inside a range — pays +110 to +119** (n 287 and 634, SE 59 and 28, +1.9 and +4.2 SE). D422 found
the opposite-side prior helps; this says where.

---

## 3. THE BOOK — adding first touches turns the best book into a random one

```
cell 2, 10 slots       gross     net     cost    util   trades   run   early   per trade   adds  blocked   net by seed
ANY-REQ               +4.889  +0.993   3.896   68.2%   5,615   5.00    0.0%    +35.85       0       0    +0.99 +1.51 +1.20
UNION-1PN             +4.179  −0.786   4.965   85.0%   7,003   5.00    0.0%    +24.57       0       0    −0.79 −0.42 −0.89
UNION-STOPS           +3.686  −1.748   5.434   83.2%   7,628   4.49   19.4%    +19.90       0       0    −1.75 −0.76 −0.65
DD-A                  +4.130  −1.343   5.472   84.0%   7,674   4.51   20.8%    +22.16     215     235    −1.34 −0.42 −0.76
DD-B                  +4.077  −1.388   5.464   84.1%   7,681   4.51   20.9%    +21.86     241     296    −1.39 −0.47 −0.83

vs ANY-REQ            gross Δ    NET Δ
UNION-1PN             −0.862   −1.933 ± 0.817   −2.4 SE
UNION-STOPS           −0.765   −2.289 ± 0.939   −2.4 SE
DD-A                  −0.524   −2.077 ± 0.977   −2.1 SE
DD-B                  −0.586   −2.130 ± 0.984   −2.2 SE
random cell-2 pools of the union's count (17,385), one per name, no stops:  p50 −1.150  p95 −0.153  util 86.4%
```

**Every union book is net-negative on every seed, two basis points a bar below the incumbent, and
statistically indistinguishable from a random cell-2 pool of the same size** (DD-A −0.84 sits
between the random p50 and p95). Adding rung 1 fills the idle third of the book — utilisation 68%
→ 85% — with +25 trades against a 29 bp round trip, and the cost line rises 1.5 bp/bar. The adds
themselves were few (215 taken, 235 blocked for want of a slot) and, per §2, were adds to −3%
positions. The stops on standalone rung 2 cost −6.80 per trade (D423's FAR again, ZTP not
enough to offset).

**The book says what D422 said from the other direction: the second-zone rung is the selection,
and diluting it with first touches gives back the whole premium.**

---

## 4. Predictions — none of six

| | prediction | outcome |
|---|---|---|
| X-a | RESTART −5..−15 | +4.64 ± 11.87 — noise on a −307 base |
| X-b | STOPS −3..−10 | −2.01 ± 8.95 — noise |
| **X-c** | DD −15..−30, < −2 SE | **+0.63 ± 17.15 — nothing; the premise was wrong** |
| X-d | UNION-1PN below by 0.3–1.0 | −1.93 — worse |
| X-e | DD-A +0.2..+0.9, T3 pass | −0.84; random pools beat it |
| X-f | BASE > STOPS > RESTART > DD | RESTART > DD > BASE > STOPS, all within noise |

**Where the miss came from.** The add is defined by a later event — a second same-side zone
within five sessions — and I priced the trade it adds to at the unconditional rung-1 mean. The
event that defines the add *implies the price path since entry*: a second demand zone below the
first means the first was breached by about the gap between the zones. That was computable from
the two zones' bands at stage 0, with no outcome bar, and would have put BASE at −300 before the
pre-registration was written. **When a flag is defined by a later event, derive what that event
says about the path from entry, from structure, before predicting.** Memory updated.

---

## 5. What this leaves

1. **Not a clear. Doubling into the second zone does nothing to a trade that is already 3% gone;
   adding first touches to the second-zone book makes it a random book.**
2. **The second zone that pays is the one that arrives after the first trade has resolved** (gap
   6–20: +39 to +61), not the one that forms while it is being run over (gap 1–2: +30, on a −276
   prior). The rung is real; its timing structure was not in D422 and is now.
3. **The opposite-side prior at gap 3–10 pays +110–119 with SEs of 28–59** — reported, not a
   claim, and the only lead in this record.
4. The rung-2 standalone with ZTP+FAR is −6.80: the FAR stop's forfeit (D423) is not offset by
   ZTP (D425) here either.
5. The entry rung is untouched; D422 §7 item 2 stands, now with a gap structure to declare.

**Disposition is the principal's.**

---

## 6. R13

Twenty-sixth look by object on price levels. No new data spent.

**Evidence:** `data/d426_double_down.json` (episodes, 15 books, deltas, control) and
`data/d426_gap_split.json` (the gap table, run after the primary). Runners
`scripts/run_d426_double_down.py`, `scripts/run_d426_gap_split.py`; flags
`scripts/d426_rung_flags.py`, committed with the pre-registration.
