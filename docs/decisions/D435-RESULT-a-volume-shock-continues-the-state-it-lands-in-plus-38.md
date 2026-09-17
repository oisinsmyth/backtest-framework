# D435 RESULT — a volume shock continues the state it lands in: +38 for a random long in high-momentum names, −48 in high-priced ones, and the universe average of −7 hid both

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D435-RESULT-a-volume-shock-continues-the-state-it-lands-in-plus-38-in-high-momentum-names-and-minus-48-in-high-priced-ones-and-the-universe-average-hid-both.md`. The H1 above is the full title.*

**A MEASUREMENT (R15): admits nothing.** Spec `ff2a175` predates the runner `7008b65` and this
file. 192 cells, 200 draws each, D392's kernel, every pool shifted one bar and `[F]`-checked.
**The principal's objection to D434 — that averaging volume over the universe is unwise because
volume means different things in different states — is confirmed, and confirmed most strongly
exactly where D434 had found its only base rate.**

```
[K] kernel probe;  [T] volume terciles partition each state;  [F] every state x feature pool is the t-1 pool placed at t
[M] the three states of every conditioner decompose D434's marginal pool exactly;  [E] [SE] [P] as D392
EMPTY: cx_dn inside vol_lo (1,230 cells), vol_mid (2,892), ret20_mid (1,863), ret20_hi (739) at n=3,000
```

---

## 1. The shock pools by state — the sign flips

```
random trade the day after a 3x-volume bar (rv_x3), n=3,000, cap 20      | after a down climax (cx_dn)
state         long p05    p50     p95      sd   short p50   pool cells     | long p50   p95    short p50   pool
price_lo        -3.9   +32.4   +62.8    21.9     -32.5      16,182         |   +7.9   +30.6     -9.8      4,286
price_mid      -34.5    -9.2   +16.0    16.3     +11.0      14,298         |  -30.0   -17.4    +30.0      3,732
price_hi       -74.1   -48.2   -25.1    15.5     +50.3      12,597         |   -9.7    +0.0    +10.3      3,517
mom_lo         -52.0   -17.3    +8.6    18.5     +19.5      13,560         |   -6.0    +8.1     +6.5      3,693
mom_mid        -29.6    -7.1   +15.0    13.5      +5.6      11,789         |  -30.4   -23.2    +30.8      3,240
mom_hi         +10.4   +38.4   +63.8    17.9     -38.0      13,731         |  +32.4   +46.2    -33.4      3,755
vol_lo         -18.9    -5.8    +9.2     8.9      +4.2       8,273         |  EMPTY
vol_mid        -24.6    -5.0   +16.2    12.7      +6.1      11,934         |  EMPTY
vol_hi         -49.6    -9.4   +32.2    24.3      +8.2      22,870         |   +0.6   +28.6     +4.5      7,413
ret20_lo       -30.1    +2.6   +32.4    18.6      -2.2      17,758         |   +2.9   +28.5     -2.9      8,932
ret20_mid      -30.6    -9.6    +9.3    12.6     +12.9       9,595         |  EMPTY
ret20_hi       -49.5   -12.8   +18.8    20.8     +17.3      15,721         |  EMPTY
D434 marginal (all states):  rv_x3 long -7 / short +7;  cx_dn long -13 / short +12
```

**A volume shock does not have a direction of its own. It amplifies the direction of the state it
lands in.** In the top momentum tercile a random long the day after a 3× volume bar earns **+38
bp at the median with the 5th percentile of draws at +10** — every one of 200 draws was above
zero — against the state's own unconditional +23; after a *down* climax in those names, **+32**
(p05 +19). In the top price tercile the same shock is followed by **−48** (p95 −25) for a long,
+50 for a short, against the state's −17.5. In the bottom momentum tercile −17. **D434's
universe-average −7 is the sum of a +38 and a −48 that have nothing to do with each other.**

Two honest limits on the climax rows. `cx_dn` inside a state is 3,200–4,300 cells and n is
3,000, so each draw is nearly the whole pool: the cell's p50 is effectively the pool's own mean,
and its "p95" is a resample of the same cells, not a null — the sd of 4–9 says how little the
draws differ, not how certain the mean is. The `rv_x3` rows (12k–23k cells) are proper atlas
cells. And these are 20-bar gross means per trade with no cost: +38 on a 24–34 bp round trip is
the first number in this atlas that would survive one, and it is a *base rate*, not a signal —
it is what a random long earns in that state after that event.

---

## 2. The tercile features by state — conditional spreads (long, hi − lo, n = 10,000)

```
state         rv (marg +3.3)     uv (marg -7.2)     ef (marg +3.5)
price_lo        +3.7 ± 1.1         +6.1 ± 1.1         +0.7
price_mid       +3.1 ± 0.9        -17.3 ± 1.0         +4.9
price_hi        -1.5 ± 0.9         -6.8 ± 0.8         +5.3
mom_lo          -4.6 ± 1.0         -8.5 ± 1.1         +2.8
mom_mid         +2.7 ± 0.7         -7.1 ± 0.8         +3.6
mom_hi          +2.3 ± 1.0         -6.2 ± 1.0         +6.2
vol_lo          -0.3 ± 0.6         -6.9 ± 0.7         +0.9
vol_mid         -2.2 ± 0.8        -12.0 ± 0.9         +3.7
vol_hi          +9.9 ± 1.3         -5.2 ± 1.3         +2.6
ret20_lo       +14.0 ± 1.1         -4.0 ± 1.1         +8.9
ret20_mid       -3.2 ± 0.8         +3.1 ± 0.9         +2.7
ret20_hi        -6.7 ± 1.0         +6.6 ± 1.0         +3.2

heterogeneity (range across a conditioner's states):  rv x ret20 20.7   uv x price 23.4   rv x vol 12.1   uv x ret20 10.6   ef <= 6.2 everywhere
```

- **Relative volume means opposite things after a decline and after a rise.** In the bottom
  20-day-return tercile, a high-volume day is followed by **+14** more than a low-volume day —
  volume confirms the reversal in losers; in the top tercile, **−6.7** — volume on a rise is
  distribution. The marginal +3.3 was the two cancelling. It also matters in high-volatility
  names (+9.9) and nowhere else.
- **Up-volume share is contrarian in mid-priced names (−17.3) and *positive* in cheap ones
  (+6.1)**; inside the 20-day-return terciles it flips from −4 (losers) to +6.6 (winners), so
  X-a's "it is `ret20` in a volume coat" is half right: the marginal −7.2 shrinks inside
  `ret20`, and what remains changes sign with it.
- **Effort-versus-result carries nothing in any state.** The largest of its twelve conditional
  spreads is +8.9. Absorption, as a bar shape, has no base rate on this universe under any
  conditioner tried.

---

## 3. Predictions — one and three halves of five

| | prediction | outcome |
|---|---|---|
| X-a | `uv` inside `ret20` shrinks below 5 in every state | lo −4.0 ✓, mid +3.1 ✓, **hi +6.6 and sign-flipped** — half |
| X-b | `rv`, `ef` inside every state within ±8 | `ef` ✓; **`rv` +14.0 in `ret20_lo`, +9.9 in `vol_hi`** — wrong |
| **X-c** | shock drift state-dependent in *size*, not sign; largest short in `mom_lo`, smallest in `price_hi` | **sign flips; `mom_hi` is +38 LONG; `price_hi` is the largest short (+50)** — wrong in every part |
| X-d | at least one conditional tercile spread > 20 | max 17.3 (`uv`|`price_mid`); **the shock pools swing 80 bp across states** — half by the letter |
| X-e | `[M]` passes | ✓ (the marginal reconciliation to 3 bp was not computed) |

X-c was the principal's hypothesis versus mine, and the principal's was right: the state changes
the sign, and the universe average of a sign-changing quantity is the number that misleads.

---

## 4. What this gives a price-and-volume supply/demand search

1. **The object with a base rate is "volume shock × state", not volume.** A 3× volume day (or a
   down climax) in a top-momentum name is followed by +32 to +38 bp for a random long over 20
   bars, p05 above +10; in a top-price name by −48, p95 −25. These are the largest conditional
   base rates in the atlas after price and momentum themselves, and they *add* to the state's
   own (+23 → +38; −17.5 → −48). A construction that trades volume shocks *with* the state's
   momentum has ~+15 to +30 bp of incremental base rate to stand on; one that trades them
   against it (the "exhaustion" story) is fighting the same numbers.
2. **Relative volume after a 20-day decline (+14) is the second object**: volume confirms the
   bounce in losers. Smaller, but the sign is the intuitive one.
3. **Effort-versus-result (absorption) is dead in every state**, and so, as a standalone, is
   dollar volume, participation trend, and relative volume without a state.
4. Everything here is the mining fixture; both daily holdouts are spent for the zone line but
   unseen by any construction built from this atlas — per the principal's per-line ruling they
   are available to a new line, once, each.

**Disposition — which object, if any — is the principal's.**

---

## 5. R13

A measurement. Thirty-fifth look by object on this universe; no holdout read.

**Evidence:** `data/d435_atlas_cond_a.json`, `data/d435_atlas_cond_b.json` (192 cells). Runner
`scripts/run_d435_atlas_conditional.py`.
