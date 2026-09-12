# D439 RESULT — a passive order at the open fills nine times in ten and recovers two-thirds of the modelled half-spread net of the chase; and the modelled half-spread on liquid names is ten times a quoted one

**A MEASUREMENT (R15): admits nothing.** Spec `7dceb57` and ADDENDUM `116d9e8` predate the corrected
run. **2024-01-01 onward on the 15m fixtures was not read (`[RESERVED]` asserted on 59,805
name-days).** No strategy scored. 56 s.

**Disclosed:** the first run had the half-spread in the wrong units (the atlas grid is already bp)
and measured the wrong term (the information in the fill, not the cost of not filling); both are
in the addendum, both fixed before this run, and the first run's numbers are not used.

```
[SIGN]     a gap-down day fills the buy and not the sell; a buy that fills into a fall reads as a cost; the check fires when flipped
[RESERVED] 40 names, 2018-01-02 .. 2023-12-29, every bar past 2023-12-31 cut
usable name-days 58,965;  volume-shock days (>= 3x trailing-20 volume) 704
PUB half-spread of these names (the number two_c charges): median 28.0 bp/side; terciles 22.7 / 35.0; wide tercile mean 55
```

---

## 1. The table — buy limit at the open, working 30 minutes, then cross at the 30-minute price

```
                        fill%    hs (bp/side)   gross capture   chase | unfilled   (1-fill) x chase   NET capture   net / hs
all, touch              100.0      33.5           33.5            0.0                 0.0              33.5         1.00   (degenerate: the open is inside the first bar)
all, through-5           92.2      33.5           30.9         +112.1                 8.7              22.2         0.66
all, through-10          88.6      33.5           29.7         +102.8                11.7              18.1         0.54
all, limit at prev close, through-5   71.1        33.5           23.8          +47.2                13.6              10.2         0.30

hs narrow  (<22.7)  through-5   91.4    17.1     15.7    +76.1     6.5      9.1     0.53
hs mid              through-5   92.2    28.2     26.0   +103.5     8.1     18.0     0.64
hs wide    (>35.0)  through-5   93.0    55.2     51.3   +166.0    11.6     39.7     0.72
shock days          through-5   95.2    36.5     34.8   +289.0    13.9     20.8     0.57
shock days, limit at prev close 59.7    36.5     21.8   +119.0    47.9    -26.2    -0.72
sells: mirror within 1 bp of the buys throughout
fill information (filled minus unfilled same-day return, the term the spec first named): +125 bp; rotation null p05..p95 -5 .. +5
```

**A limit at the open that needs the market to trade 5 bp through it fills 92% of the time.**
The first thirty minutes of these names trade through the open by 5 bp on nine days in ten (X-a
predicted 35–45%; the intraday range of even a large name dwarfs 5 bp). On the 8% of days it does
not fill, the price is **+112 bp** away at the half-hour — a strong opener that ran — so the chase
term is 8.7 bp per order. Net of that, the passive order recovers **22 bp of a modelled 33.5 bp
half-spread: 0.66**. Behind the queue by 10 bp: 0.54. A limit at the prior close is a different
instrument — it fills 71% and the chase is on gap-ups — and recovers 0.30.

**The fraction is largest where the spread is widest** (0.53 / 0.64 / 0.72 by tercile), as X-e
said, because the chase does not scale with the spread and the saving does. **On volume-shock
days it still fills 95%, the chase is +289 on the days it misses, and the net is 0.57** — a
passive order at the open on a shock day works; a limit at the *prior close* on a shock day is
the one rule that loses (−0.72: the open has gapped away from it).

**The fill information is +125 bp** — the days a buy fills are days that close 125 bp lower than
the days it doesn't — far outside its rotation null (±5). That is the size of the selection a
passive order lives with; it is not a cost relative to crossing, because the crosser holds the
same position on the same days (the addendum's point). It would matter to a strategy that could
choose *not* to trade on unfilled days, which none here can.

---

## 2. The number that bears on every cost line in the repo

**The modelled PUB half-spread on these 40 names is 17 to 55 bp a side, median 28.** These are
MSFT, JPM, CSCO, INTC, V, PG — names whose quoted half-spread is a basis point or two. The
Corwin–Schultz estimator reads the daily high–low and it reads intraday *range*, not the quote;
D285 found the same figure (33.8 bp/side on held names) and took it as the cost. D336's
quoted-spread pull never ran (TWS). **So "capture of the half-spread" here is in large part
capture of a number the market does not charge:** the passive fill saves the modelled 33 bp; a
crosser on MSFT pays 2. The **model-free** content of this study is the chase — 8.7 bp per order
under through-5 at the open, 11.7 under through-10, measured in prices only — and the fill rate.

What that implies is not that costs are lower everywhere. It is that **the cost models are range
models**, honest about small illiquid names where the range and the spread converge, and wrong by
an order of magnitude on liquid ones. B's wide third (D438: 42 bp/side modelled) sits inside this
fixture's range (17–55), so the 0.66–0.72 fraction is not an extrapolation for those names — but
whether *their* modelled 42 is a quote or a range is the unmeasured thing, and it is the thing.

---

## 3. Predictions — three of six, after the addendum

| | prediction | outcome |
|---|---|---|
| X-a | through-5 fills 35–45% | **92%** |
| X-b | hs median 3–12 bp/side | **28** — the model is a range, not a quote |
| X-c (addendum) | chase +15 to +40 | **+112**, on 8% of days |
| X-d (addendum) | net capture 0.5–0.8 of hs; lower on shock days | 0.66 ✓; shock 0.57 ✓ |
| X-e | largest fraction in the wide tercile | 0.72 ✓ |
| X-f | rotation null ±2 | ±5 — wider, still an order of magnitude below the +125 |

---

## 4. What this decides, per §5 of the spec

Net capture on liquid names is 0.66 of the modelled half-spread — above the 0.3 the spec set as
the threshold for "the cost models are conservative by that fraction on liquid names." **A stage
2 on B may declare a passive-fill cost line — the modelled half-spread × (1 − 0.66) per side plus
the measured chase of 9 bp per order — labelled as an assumption for the wide third**, beside the
incumbent crossed-spread line. On D438's B at cap 20 that assumption turns 2c from 52 to roughly
**27 bp plus borrow**, against +39 gross. It does not decide whether B's names' modelled spread is
a quote or a range; nothing on this data can, and TWS still can.

**Disposition is the principal's.**

---

## 5. R13

A measurement. Thirty-ninth look by object; no holdout; the reserved 15m window untouched.

**Evidence:** `data/d439_fill_capture.json`. Runner `scripts/run_d439_fill_capture.py`.
