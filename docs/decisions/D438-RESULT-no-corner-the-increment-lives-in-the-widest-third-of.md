# D438 RESULT — no corner: the shock's increment lives in the widest third of the spread, and only a sixty-bar hold nets positive, at 1.4 SE, on twenty names

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D438-RESULT-no-corner-the-increment-lives-in-the-widest-third-of-the-spread-and-only-a-sixty-bar-hold-nets-positive-at-1-4-se.md`. The H1 above is the full title.*

**A MEASUREMENT (R15): admits nothing. NO CORNER on the condition declared in `91ad967`** (net PUB
> 0 by 2 SE *and* increment above the state-matched p95). In-sample; no holdout. 7.5 min.

```
[K] kernel probe;  [F] the events are D436's (13,731 / 12,597);  [T] the spread terciles partition each component's events
[P2] cap 20 reproduces D437's per-trade gross for A and B to 1e-9
```

---

## 1. Axis 1 — the spread tercile of the names held (PUB half-spread at t−1; the control shares the tercile)

```
                     n      gross     2c PUB    2c PB    net PUB          net PB    state-matched p50   p95     increment
A narrow (<24.8)   3,683    +11.1      38.6     23.6    -27.6 (-2.4 SE)   -12.6        +21.8          +37.0     -10.8   <= p95
A mid              3,855     +0.9      62.3     47.3    -61.4 (-4.3 SE)   -46.4        +16.2          +38.4     -15.3   <= p95
A wide (>38.5)     3,472    +97.9     102.2     65.4     -4.3 (-0.2 SE)   +32.5        +51.5          +87.4     +46.5   > p95
B narrow (<21.3)   3,418     -1.8      33.2     25.6    -40.3 (-3.8 SE)   -32.8        -11.6           +3.5      +9.8   <= p95
B mid              3,590    +14.3      52.5     43.2    -43.0 (-3.4 SE)   -33.6         +1.6          +15.7     +12.8   <= p95
B wide (>32.4)     3,307   +106.5      83.8     48.8    +18.0 (+0.7 SE)   +52.9        +72.7          +97.9     +33.8   > p95
```

**The increment is where the spread is.** In the narrow and mid terciles the shock adds nothing
beyond its state (A −11 / −15; B +10 / +13, both inside their controls' p95) and the names cost
33–62 bp to trade; in the wide tercile the shock adds **+46 (A) and +34 (B) — the whole of
D437's +10 and +22 and more** — and the names cost 84–102. The wide tercile grosses +98 / +106
and nets **−4 (A) and +18 (B, +0.7 SE)** under PUB, +33 / +53 under PB. X-b predicted the
increment flat across terciles; it is entirely in the third the spread eats. **This is the zone
line's cheap-tercile finding in another coat: the information and the illiquidity are the same
names.**

---

## 2. Axis 2 — the cap (all events; the control state-matched at the same cap)

```
              n       gross    2c PUB   net PUB           net PB    ctrl p50   p95     increment        deployed gross / cost2 / net2 per bar    names to half   top-1% share   years+
A cap  5   11,717     +2.1     62.3    -60.1 (-10.3 SE)   -38.6      +6.8     +12.4    -4.6  <= p95     -0.85 / 12.49 / -13.34                       1           1289%       8/16
A cap 10   11,181    +12.4     62.0    -49.6 ( -6.3 SE)   -28.9     +10.0     +20.8    +2.4  <= p95     +0.82 /  6.23 /  -5.41                       4            293%      12/16
A cap 20   10,495    +36.8     61.6    -24.8 ( -2.2 SE)    -4.0     +26.7     +37.5   +10.1  <= p95     +1.50 /  3.11 /  -1.61                      11            139%      12/16
A cap 40    9,057    +47.5     61.0    -13.5 ( -0.8 SE)    +8.0     +47.1     +68.4    +0.5  <= p95     +1.12 /  1.55 /  -0.43                      11            139%      11/16
A cap 60    7,976    +90.7     60.5    +30.2 ( +1.4 SE)   +51.6     +74.9     +99.4   +15.8  <= p95     +1.38 /  1.03 /  +0.35                      16             91%      12/16
B cap  5   10,887    +15.3     52.6    -38.5 ( -7.4 SE)   -22.8      +2.3      +7.9   +13.0   > p95     +3.80 / 10.54 /  -6.75                       9            148%      13/17
B cap 10   10,444    +27.9     52.5    -27.1 ( -4.0 SE)   -11.7      +6.3     +15.8   +21.6   > p95     +2.65 /  5.27 /  -2.61                      14            108%      15/17
B cap 20    9,851    +38.8     52.2    -18.3 ( -1.8 SE)    -3.0     +17.4     +31.5   +21.3   > p95     +2.24 /  2.62 /  -0.38                      16            108%      15/17
B cap 40    8,394    +68.9     51.8     +7.3 ( +0.5 SE)   +22.6     +32.4     +50.4   +36.4   > p95     +1.86 /  1.31 /  +0.56                      18             85%      13/17
B cap 60    7,332    +93.9     51.5    +27.9 ( +1.4 SE)   +42.9     +57.4     +77.6   +36.5   > p95     +1.62 /  0.87 /  +0.75                      20             79%      14/17
```

**B carries information at every horizon and A does not.** B's increment over its state-matched
control clears the p95 at every cap and grows from +13 at five bars to +36 at forty and sixty; A's
increment is inside its control's p95 at every cap (−5, +2, +10, +0, +16) — D437's +10 for A at
cap 20 was the one horizon where it came closest, and the cap axis says it was not there. **The
top-momentum long after a volume shock is the state's own drift; the top-price short after a
volume shock is not.**

**The spread amortises with the hold, and by sixty bars both net positive — at 1.4 SE, on twenty
names.** 2c is fixed per trade; gross rises with cap as the atlas's floors do; net PUB crosses
zero between 40 and 60 for B (+7 → +28) and at 60 for A (+30). Neither reaches 2 SE. Deployed,
B nets +0.56 / +0.75 a bar at 40 / 60 and A +0.35 at 60. And the concentration at those holds is
the concentration of every tail-carried result in this repo: **the top 1% of trades is 79–91% of
the P&L, twenty names are half of it**, and thirteen to fourteen of seventeen years are positive.
X-e predicted B's cap-60 net at +5 to +25 above 2 SE; it is +28 at 1.4.

---

## 3. Predictions — two of six

| | prediction | outcome |
|---|---|---|
| X-a | 2c ~25–35 / 45–60 / 90–130; gross rises with spread | 2c 39 / 62 / 102 (A), 33 / 53 / 84 (B) ✓; gross +11 / +1 / +98, −2 / +14 / +106 ✓ |
| **X-b** | increment flat across terciles | **entirely in the wide tercile** |
| X-c | no spread corner | ✓ (narrow nets −28 / −40, worse than predicted) |
| **X-d** | increment accrues with cap, A and B | **B yes (+13 → +37); A no (never > p95)** |
| X-e | cap 60: B net PUB +5..+25 at > 2 SE | +28 at **1.4 SE**; A +30 at 1.4 |
| X-f | A's deployed net2 negative at every cap; B positive at 40–60 | A +0.35 at 60; B ✓ |

---

## 4. What this leaves

1. **No corner.** Nothing in the spread axis or the cap axis satisfies "net positive at 2 SE and
   informative beyond its state." The closest cells — B at cap 40–60 (net +7 / +28, +0.5 / +1.4
   SE, increment +36 above p95) — are a sixty-bar short book of high-priced names whose P&L is
   79% its top 1% of trades.
2. **The increment and the spread are the same names.** Both components' information sits in the
   widest third of their spread distribution, where a round trip is 84–102 bp. The narrow and mid
   thirds — the tradeable names — carry no shock information at all.
3. **A is closed by this measurement:** the momentum-long shock never clears its state-matched
   control on any horizon. **B is the object,** and it is the same object D434 found as "a
   short-side drift after a volume shock" and D435 located in `price_hi`: it exists at every
   horizon, it grows with the hold, and it nets positive only where the hold is long enough to
   amortise a spread the signal cannot avoid.
4. **The remaining lever is the one it has been since D433: execution.** A +34 increment in
   names with an 84 bp round trip is a trade if a passive fill recovers a third of the spread,
   and not otherwise. That is measurable on the 15m fixtures and it is not a signal study.

**Disposition is the principal's.**

---

## 5. R13

A measurement. Thirty-eighth look by object; no holdout.

**Evidence:** `data/d438_cost_axes.json`. Runner `scripts/run_d438_cost_axes.py`.
