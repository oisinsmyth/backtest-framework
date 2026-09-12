# D463 RESULT — market intraday momentum is a third of its published size on ES 2016–2023 and not distinguishable from zero; hurdle P, computed for the first time, fails on size at every f

**NOT A CANDIDATE: F1 fails, F3 fails, no f on the grid clears hurdle P.** Spec `dd5801c` and its
ADDENDUM predate the runner's run (R8). **In-sample on the usable window 2016-01-04 to 2023-12-29
(D462); the 2024–2026 slice was not read; RTY was not run (its fixture failed D462's G4).**
0.1 min. **The first forward-return look at a prop candidate on the futures themselves, and the
first time P3, P4 and P5 have been computed on anything (D375 §5).**

```
[G] the D462 gates passed on ES, NQ, YM;  [F] every bar inside the usable window and none after END;  30 bars in every trade window; same-contract days only
selftest: Newey-West slope on synthetic; the rotation null at offset 0 equals the real mean; the sized-days rule (whole contracts, 21-trade sigma, cap, flat days zero); provider start rolls
disclosed: the runner's first pass printed the slope dimensionless and crashed on an empty era cell before writing the artefact; both fixed, re-run, numbers unchanged
```

---

## 1. The effect, per instrument (sign of rROD, 15:30 open → 16:00 print)

```
                 trades   mean bp   +- SE   median   sd     hit    $/ct    cost bp   net bp   always-long   N1 rotation p95 (exact)   N2 signs p95   beta x100 (NW t)   post-2018 beta (t)
ES   primary      1,894    +1.18    0.86    +0.00   32.1   49.3%   +20.1    1.11     +0.07      -0.52          +1.10 (p99 +1.66)         +1.22           +1.82 (+1.1)        +2.13 (+1.2)
NQ                1,907    +1.51    0.90    +0.66   35.1   51.0%   +29.5    0.59     +0.92      -0.24          +1.26                     +1.31           +1.83 (+1.7)        +2.08 (+1.8)
YM                1,900    +0.22    0.80    -0.48   28.5   48.3%    +1.8    0.73     -0.51      -0.70          +0.99                     +1.08           +1.29 (+1.1)        +1.53 (+1.2)
ES by era:  2015-19 (from 2016)  -0.13 bp, hit 47%, beta +1.0    |   2020-23  +2.47 bp, hit 52%, beta +2.0
Gao's first-half-hour predictor on ES: beta x100 -10.7 (t -1.1) -- the wrong sign, insignificant
```

**F1 fails on the primary:** +1.18 bp per trade is 1.4 SE from zero, above the exact rotation p95
by 0.08 bp and below the sign-randomisation p95. **F3 fails:** the slope is **+1.8 (×100)**
against Baltussen's published **6.18** on 1974–2020 — **a third of the published size**, with
t = 1.1 on 1,894 days; post-2018 it is +2.1 (t 1.2), under the 3.0 floor the lane set as the
McLean–Pontiff haircut arriving. NQ is the same size at t 1.7; YM smaller. The hit rate is 49–51%
on every instrument: the sign of the day's return does not tilt the last half-hour's sign. **The
last half-hour itself drifted *negative* over 2016–2023** (always-long −0.5 bp on ES), against
X-b's +0.5 to +1.5.

**Read honestly:** the point estimate has the published sign on all three instruments and the
2020–2023 sub-period is +2.5 bp at 52% — but that is a post-hoc cell on four years, and the
pre-registered tests on the declared window and instrument do not pass. On eight years of one
instrument a 1–2 bp effect with a 32 bp per-trade σ cannot be resolved at 2 SE, and the
literature's number was measured on 46 years and 17 markets.

---

## 2. The path inside the window — the quantity nobody publishes (F2)

```
MAE per contract inside 30 minutes, ES:   p50 $175   p90 $675   p99 $1,641   worst $4,000 (2020-02-28)     P(MAE > $1,000) 4.38%    P(MAE > $2,000) 0.63%
                                  NQ:   p50 $230   p90 $945   p99 $2,312   worst $5,205 (2022-01-24)     8.86%                    1.63%
                                  YM:   p50 $140   p90 $550   p99 $1,220   worst $3,445 (2020-03-25)     1.84%                    0.26%
in return terms, ES:  MAE p50 11.7 bp   p99 91 bp   worst 310 bp
```

One ES contract held for the last thirty minutes goes more than $1,000 against you on **one day in
23** and more than $2,000 on one in 160 — X-c said 2–6% and 0.3–1.5%, and both landed. That is the
lane's "1.58σ" arithmetic made concrete, and it is what hurdle P is about.

---

## 3. Hurdle P, computed for the first time (ES, MFFU Rapid EOD 50K, 600-day horizon)

```
sizing                       contracts   zero-size days   P3 worst day   days < -2%   P4 funded life   alive at 600 d   pass eval   V per eval     P5 years > 40%   ann. return
f = 0.2%                       0.00        2,062             --              0          --  (never funded)   --             0%        -209 +- 0        --              0.0%
f = 0.4%                       0.27        1,504           -1.96%            0          0.48 yr             42%            4%        -209 +- 0       3 / 3           -3.0%
f = 0.7%                       0.69        1,128           -4.06%           13          0.20 yr              0%           17%        -209 +- 0       3 / 3           -7.7%
f = 1.1%                       1.45          585           -7.84%           81          0.14 yr              0%           18%        -122 +- 12      4 / 4          -12.1%
1 contract fixed (beyond grid) 0.92          168           -8.03%           87          0.07 yr              0%           19%        -159 +- 7       1 / 3           +1.5%
```

**The size scissors, measured.** On a $50,000 account one ES contract's 30-minute σ is about
$650, so the C4 rule at f = 0.2% or 0.4% sizes **below one whole contract on most days** — the
account cannot express the trade at the size the drawdown allows — and at the sizes that do trade
(f ≥ 0.7%, or a fixed contract) **the worst day breaches P3's 2% on 13 to 87 days**, **the funded
account lives 0.07 to 0.20 years against P4's three**, and **V is negative at every f**. P5 fails
in every year that has any profit. The candidate would fail hurdle P *even if F1 and F3 had
passed*: the shape X-e predicted, and the number the ledger's screen 4 could only estimate.

---

## 4. Predictions — two of six

| | prediction | outcome |
|---|---|---|
| X-a | ES β +2.5..+6.0 (t 2–5), post-2018 +0.5..+3.5; NQ ≥ ES; YM same sign | **+1.8 (t 1.1)**; post +2.1 ✓; NQ +1.8 (= ES); YM +1.3 ✓ sign |
| X-b | mean +1.5..+4.0 bp, hit 52–55%, always-long +0.5..+1.5, N1 p95 +1.2..+2.0, N2 p95 +1.0..+1.6 | **+1.18**, **49.3%**, **−0.52**, N1 1.10 (just under), N2 1.22 ✓ |
| X-c | sd 18–28 bp; MAE p50 6–10, p99 50–90, worst > 200; P(> $1k) 2–6%, P(> $2k) 0.3–1.5% | sd **32**; p50 **11.7**, p99 91 ✓, worst 310 ✓; 4.4% ✓, 0.6% ✓ |
| X-d | cost 0.4–0.6 bp, net > 0 | cost **1.11** (ES traded ~$150k notional on average over the window, not today's $225k); net +0.07 |
| X-e | f 0.2% sizes zero; P3 breaches at f ≥ 0.7%; P4 < 1 yr at every f | ✓ ✓ ✓ |
| X-f | same sign on all three; strongest early, weakest 2020–23 | same sign ✓; **strongest 2020–23** |

---

## 5. What this leaves — the principal's call

1. **The candidate is closed on this window as pre-registered**: the effect is a third of its
   published size, not distinguishable from zero on eight years, and it fails every hurdle-P leg
   at every size the account can express. The literature's SR 1.08–1.73 was 46 years and a
   17-market portfolio the instrument cannot hold; on the one instrument and the years we own,
   it is 1–2 bp a day at a hit rate of 50%.
2. **What the record establishes beyond the candidate:** the P3/P4/P5 machinery now runs on a
   measured intraday path (D440's provider with a whole-contract sizing rule), and the answer
   for *any* single-contract ES construction with a 30-minute σ of $650 on a $50k account is
   the same arithmetic — the floor is 3σ away per trade and the trailing drawdown compounds the
   bad days. **A prop candidate on ES at this account size needs a per-trade σ well under $300
   or a different account size**, which is a statement about the instrument, not the signal.
3. **The 2024–2026 slice stays unread**; the fixtures are committed and gated; NQ (net +0.92 bp
   at 1.7 SE on the slope) is the only instrument whose numbers a later record might reasonably
   look at again, and it is reported here so that a later look is not called a prediction.

**Disposition is the principal's.**

---

## 6. R13

Fiftieth look by object; look #1 of the prop track on the instrument itself; the 2024–2026 slice
unread; no holdout. **Evidence:** `data/d463_intraday_momentum.json`, `data/d463_trades.csv.gz`
(5,701 trades with their within-window paths). Runner `scripts/run_d463_intraday_momentum.py`.
