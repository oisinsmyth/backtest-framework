# D434 RESULT — volume is the narrowest axis in the atlas, and its one base rate is a short-side drift after a volume shock

**A MEASUREMENT (R15): admits nothing.** Spec `d830c47` and ADDENDUM `62c1a68` predate the run
that produced these numbers. **The first run (two halves, ~55 min) was one bar ahead of the
kernel's fill and is quarantined in `temp/d434_atlas_volume_{a,b}_LOOKAHEAD.json`; every number
here is from the shifted re-run.** 132 cells, 200 draws each, D392's kernel, seed and draw.

```
[K]  score_once == run_d359's own path on a 2,000-event probe
[T]  every tercile triple partitions every defined bar        [C]  no pool at t reads the fill bar or later
[F]  every pool is the t-1 feature placed at t                [X]  a next-bar dependence and the first run's unshifted pools are both caught
[E]  every draw on the eligible mask   [SE] every p95 with its bootstrap SE   [P] persisted per cell
pools: terciles ~950k cells each; rv_x3 43,077; cx_dn 11,535 (EMPTY at 30,000); cx_up 9,466 (EMPTY at 10,000 and 30,000)
```

---

## 1. The spreads — top tercile minus bottom, random long, p50 at n = 30,000, cap 20

```
axis                                   spread    hi p50   lo p50        D392 for scale
rv    relative volume                   +1.5     +1.7     +0.2          price     36.8
ef    effort per unit result            +4.1     +2.7     -1.4          momentum  32.2
vt    participation trend               -0.3     -0.0     +0.3          volatility 12.2
uv    up-volume share (20d)             -8.5     -3.4     +5.1
dv    dollar volume                     +4.0     +6.1     +2.0   (mid -4.1: not monotone)
divergence quadrants (ret20 sign x volume trend):  dn_fall +10.2  dn_rise +7.2  up_rise -6.7  up_fall -6.5   span 16.9
unconditional n=30,000 cap 20:  long +1.6   short -1.6
```

**Volume alone carries almost no base rate on this universe.** The widest volume spread (up-volume
share, 8.5 bp) is narrower than the narrowest of D392's axes (volatility, 12.2), a quarter of
price and momentum. Relative volume, effort-versus-result and the participation trend are flat to
within their own noise — a random trade after a high-volume, low-range bar earns what a random
trade earns. The divergence quadrants' 17 bp span is the **20-day return sign** — price down
→ +7 to +10, price up → −7 — which is short-horizon reversal, an axis the atlas already had in
another coat; the volume trend moves the quadrants by ~3 bp inside each sign.

**Up-volume share is contrarian, not momentum.** X-e predicted +10 to +25 (momentum measured by
volume); it is −8.5: a name whose last twenty days' volume came on up days earns *less* for a
random long. Volume-weighted recent direction reverts where price-weighted 12-1 momentum
continues.

---

## 2. The one volume-specific base rate: after a volume shock, the drift is down

```
pool                          n         long p50    long p95 (± SE)    short p50    trades
rv_x3   VOL >= 3x ADV       3,000       -5.9        +24.6 ± 2.3          +4.8       2,919
                           10,000       -5.6         +7.3 ± 0.8          +7.3       9,235
                           30,000       -7.0         -2.1 ± ---          +7.0      ~27,000
cx_dn   down climax         3,000       -6.2        +18.5 ± 1.4          +5.0       2,925
                           10,000      -12.8         -6.2 ± 0.6         +11.6       9,341
cx_up   up climax           3,000       -2.8        +26.7 ± 2.7          +5.2       2,918
```

**A random long placed the day after a 3×-volume bar loses 7 bp over twenty bars at the median,
and its p95 is below zero at n = 30,000; after a down climax it loses 13 at n = 10,000, p95 −6.**
The short side mirrors: +7 and +12. This is the opposite of X-b (a reversal premium after the
down climax, +20 to +50 long) and the opposite of the high-volume return premium X-a expected:
on this dead-inclusive universe, **a volume shock is followed by continuation, and the up
climax by nothing.** It is real at the atlas's standard — a p95 below zero on 9,000–27,000
trades — and it is 7 to 12 bp gross on the short side, where the round trip is 24–34 plus
borrow.

For comparison, the first (look-ahead) run had `cx_dn` at −405 and `cx_up` at +471: those were
the climax days themselves. The shift removed them and left a drift a thirtieth their size.

---

## 3. Predictions — one of seven

| | prediction | outcome |
|---|---|---|
| X-a | `rv` spread +8..+20; `rv_x3` above `rv_hi` | **+1.5**; `rv_x3` *below* (−7 vs +1.7) |
| X-b | `cx_dn` long +20..+50; `cx_up` long −10..−30 | **−13 (p95 < 0)**; −3 |
| **X-c** | `ef` inside ±10 | **+4.1 ✓** |
| X-d | `vt` +5..+15 | −0.3 |
| X-e | `uv` +10..+25 (momentum by volume) | **−8.5 — contrarian** |
| X-f | `dv_lo` ≈ `price_lo` (+15..+25); `dv_hi` ≈ 0 | +2.0; +6.1 — not the price axis |
| X-g | quadrant span 20..40, `up_rise` best | 16.9; **`dn_fall` best — reversal, not volume** |

Every directional prediction about volume was wrong, most in sign. The one that held said
"nothing here" about the one feature (effort vs result) the literature is most confident about.
The lesson is the same as D432's: I predicted the stories volume is supposed to tell; the
universe's own base rates were computable and would have said otherwise.

---

## 4. What this leaves for a price-and-volume supply/demand indicator

1. **Volume does not carry a base rate to build on** — nothing in relative volume, effort-vs-
   result, participation trend or dollar volume moves a random trade by more than a few basis
   points over twenty bars. Any volume construction's in-sample number will therefore be almost
   entirely its own selection, which is exactly the condition under which the second-zone line's
   layers did not transfer.
2. **The one volume-specific fact is a short-side drift of 7–12 bp after a volume shock or a
   down climax**, with the p95 below zero. As a base rate it is a prior for any "capitulation"
   or "exhaustion" construction: **the exhaustion long is fighting a −7 to −13 bp drift, not
   riding a bounce.** Absorption bars (`ef_hi`) have no base rate either way.
3. **The direction axes are the ones the atlas already had:** 20-day reversal (±7–10), 12-1
   momentum (32), price (37). Up-volume share is a noisier reversal proxy.
4. The atlas now has five volume axes and 22 pools for future constructions to be read against;
   `lookup` needs a `pool` from this file and D392's alike.

**Disposition — which construction, if any — is the principal's.**

---

## 5. R13

A measurement. Thirty-fourth look by object on this universe. No holdout read; the atlas is
mining-fixture only.

**Evidence:** `data/d434_atlas_volume_a.json`, `data/d434_atlas_volume_b.json` (132 cells);
`temp/d434_atlas_volume_{a,b}_LOOKAHEAD.json` (the first run, wrong by one bar, kept as evidence).
Runner `scripts/run_d434_atlas_volume.py`.
