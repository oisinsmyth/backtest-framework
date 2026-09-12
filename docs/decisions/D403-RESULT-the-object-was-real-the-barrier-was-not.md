# D403 RESULT — the object was real, the barrier reading was not, and it escapes TERRAIN's mechanism

**CLOSED BY THE PRINCIPAL, 2026-09-09** — *"this construction is dead, I don't think this
accurately captures supply and demand."* Pre-registration `7860c21`, amended `95dad11`, runner
`ed4df92`, all predating this file (R8).

**Only G1 was spent — 4 of 24 names. G2 (8) and G3 (12) were never run. No holdout was read.
Nothing was admitted to either book.**

---

## 1. What was built

The principal's construction: each daily candle contributes a **supply zone** `[max(O,C), H]` and a
**demand zone** `[L, min(O,C)]`. Stack both **additively** over 100 trailing daily bars, subtract
the valley floor between the two peaks, clamp at zero. Read at 15 minutes.

**§5.1 killed the first version before any statistic ran.** The bare wick stack is not a potential
— it is a **comb**:

```
modes of M_raw, p10/50/90     89 / 96 / 103
unimodal share                0.0
breakpoints                   ~385 of a possible 400
max level                     15-22 of a possible 200

BMY   2021-01-04  C_ref  62.00  p_l  61.94  p_u  62.01   tau 17 of max 22
ILMN  2021-01-04  C_ref 359.89  p_l 297.18  p_u 362.63   tau  1 of max 15
```

BMY's two "peaks" sit **seven cents apart**, straddling spot, because the densest teeth are always
the recent bars beside it. ILMN's well is 18% wide the same day. The peak anchoring was picking a
tooth, not a barrier.

**The principal's amendment (`95dad11`): clamp the wick at height one and let a distribution take
over from the edge.** Overlapping wicks then pool, and the wick's own span still sets the core.
It worked — the comb collapses on a genuine scale ladder:

```
kernel     c   h %px    modes p10/50/90   <=2 modes   tau/max
gauss   0.25   0.70%     [3,  5,   9]        0.097      0.297
gauss   0.50   1.40%     [1,  2,   4]        0.522      0.412    <- bimodal regime
gauss   1.00   2.79%     [1,  1,   3]        0.891      0.577
gauss   2.00   5.59%     [1,  1,   2]        0.994      0.726
```

At `c = 0.5` the median map has **exactly two modes** and 52% of name-days are bimodal-or-less —
the two-peak framing becomes well-posed exactly where the pre-registered primary already sat. Past
`c = 1` it over-smooths to one blob and the pedestal eats 58–73% of the peak, so the "well" becomes
a subtraction artefact. **A window, not a knob.** `exp` and `tri` show the same collapse at
different rates.

---

## 2. What the map does — and it is the inverse of the claim

Events against all bars on the **same** map (alignment held fixed), primary cell:

| vs ALL_BARS | BMY | ILMN | BMRN | NOW |
|---|---|---|---|---|
| move > 2.0σ | +0.04 | +0.16 | +0.61 | +0.68 |
| move > 2.5σ | **+0.28** | **+0.37** | **+0.81** | **+0.70** |
| reversal > 1.0σ | −0.29 | −0.26 | −0.31 | +0.38 |
| reversal > 1.5σ | −0.56 | −0.24 | −0.24 | +0.59 |

**Large moves sit at dense map — 8 of 8, monotone in the threshold. Reversals sit at thin map —
6 of 8.** Swing points sit indistinguishably at the average (±0.28, no sign pattern). **Price goes
through the zones, it does not turn at them.**

**Occupancy does not support the potential reading.** `monotone_decreasing` is **0 of 4 names in
every one of the eight cells**; the curve is hump-shaped — lowest at `M≈0`, peaking near `M≈0.15`,
then declining — so the negative `beta` (−0.28 to −0.91) is a straight line through a bend.
Top-to-bottom ratio 0.855–1.474, i.e. about 1.

**A construction consequence worth recording:** the pedestal zeroes the map exactly where price
lives, by design, so **60% of all visits fall in the bottom `M` bin.**

---

## 3. It escapes TERRAIN's mechanism — the one durable positive

TERRAIN closed 259 looks on a mechanism, not an absence: *inventory accumulates below price exactly
when price has been falling into it, so the map's local structure is reliably wrong.*

```
corr(M at price, trailing 20d return)   -0.009   -0.109   -0.097   +0.074
mean M after up-runs / down-runs        splits 2-2
```

**Small, sign-inconsistent, no pattern. This map is not a restatement of where price recently was**
— the first price-level object in six looks of which that is true. It is the finding most worth
carrying forward, and it is why D405 was worth attempting afterwards.

---

## 4. A′ was contaminated by the construction, so "0 of 32" is not a finding

Every cell reported the observed event mean below A′'s p95, 0 of 32, which looks like D388
repeating. **It is tautological.** `tau` is the *minimum* of the field between the two peaks and
`C_ref` lies between them, so the observed alignment **guarantees** price sits near the map's zero.
Rotating drops price at a random point on a foreign map, often on a slope. A′'s p95 sits at 13–16
against an observed 4.1–4.9 everywhere, and A′'s **median** does not even agree in sign across four
names (BMY +0.31, ILMN +1.24, **BMRN −2.47**, NOW +2.50).

**The fix, unrun:** rotate against `M_raw`, whose zero is not tied to price.

---

## 5. THREE ARMS WERE NOT REPORTABLE, AND THEIR CONTROLS WERE PRE-REGISTERED AND NOT BUILT

Stated plainly because the numbers are attractive and would be quoted otherwise.

- **`reject_share` 0.65–0.92.** Looks like a spectacular confirmation of supply and demand. Almost
  certainly **band-width arithmetic** — leaving a wide band the way you entered within 4 bars is
  the random-walk default. Needs the width-matched random band (`LVL`, §6) that was never built.
- **Breakout frequency 0.78 at 0.07σ → 0.00 at 50σ.** This is **D273's monotone 62.6% → 1.3%
  exactly**, which any random line reproduces. `by_barrier_height` (0.73 → 0.003) looks like the
  barrier prediction but height and distance are confounded: the tall part of the map is far from
  price *because* price sits in the valley.
- **Excursion +3.2 to +4.6σ** — meaningless without a matched random level.

`OCC` and `LVL` were both named in §6 of the pre-registration and neither was implemented. **That is
an incompleteness in the runner, not a finding about the map.**

---

## 6. Reliability — measured after the fact, and it is what closed the line

The G1 run measured `P(M | event)`. Reliability is `P(event | M)`, and a >2.5σ move fires on ~2.4%
of bars, so the two are very different questions. Measured (exploratory, G1, not evidence):

**AUC for predicting a >2σ move from `M_raw`:**

```
h=1 bar    0.520  0.497  0.510  0.506
h=4 bars   0.568  0.518  0.510  0.492
h=12 bars  0.563  0.583  0.550  0.484
```

Top-minus-bottom decile of forward |move|, **session-clustered** SE (iid would be fiction — 15m
bars are serially correlated):

```
h=4    BMY +0.064+-0.022   ILMN +0.011+-0.025   BMRN -0.003+-0.027   NOW +0.032+-0.022
h=12   BMY +0.060+-0.032   ILMN +0.080+-0.035   BMRN +0.021+-0.037   NOW +0.070+-0.033
```

**No lift curve is monotone**, and the top decile is usually not the maximum — BMY peaks at d8,
BMRN at d6, **NOW at d3**.

**The reconciliation matters:** "8 of 8 large moves at dense map" is a ~6% shift in a conditional
mean over a wide distribution — impressive-looking and nearly information-free. Inverted into
`P(move | M)` it is **AUC 0.52**.

### The regime question, and it is ruled out in both directions

Split on volatility, trend and time-of-session, `h = 4`, negative = the barrier reading holds:

```
vol    BMY  +0.072 +0.067 +0.141      NOW  +0.093 +0.065 -0.056
       ILMN -0.050 +0.022 +0.012      BMRN -0.008 +0.007 -0.064
```

**The sign flips by NAME, not by regime.** BMY is *most* positive in high volatility (+0.141,
3.7 SE); NOW turns negative in exactly that slice. And the dense-map condition is **not rare** —
13.6% / 15.4% / 19.4% / 14.2% of bars sit in the top decile of their own map's range, with the
median bar at ~45% of the map maximum. So "works in a corner that seldom happens" fails too.

---

## 7. `[ALIGN]` — the finding that outlives the study

**The 15m fixtures are fully corporate-action adjusted; `us_shorts_daily_raw.csv.gz` is not on the
same basis.**

```
NOW    15m / daily = 0.20000 flat 2018-2025, 1.0 in 2026     (a 5:1 split)
ILMN                = 0.97276 to 2024-06,   1.0 after        (the GRAIL spinoff)
BMY, BMRN           = 1.00000 throughout
```

**`raw_price_factor` cannot repair this** — it knows splits only, and a spinoff is not a split.
Unrepaired, ServiceNow's map sat at **five times its own prices for the entire scored window**:
every level unreachable, every breakout frequency zero, and it would have been reported as a fact
about supply and demand. Nothing else in the study would have flagged it.

The repair is a per-session basis factor `phi[u] = (15m last close) / (daily close)` applied to bar
`u`'s own OHLC — causal, units not information, measured per bar rather than smoothed. **Any
cross-timeframe study in this repo inherits this trap.**

Minor, also recorded: D388's `ew_sigma` floors variance at `1e-24`, so runs of identical 15m closes
drive `|r|/σ` into the hundreds of thousands. Under 0.1% of bars, masked not clamped, too small to
have moved the event thresholds — but it is a live edge in a shared estimator.

---

## 8. What survives

1. **The map is not a restatement of recent price** (§3). Unique among the price-level programmes.
2. **The amended construction is sound** — no bandwidth in the object at `c = 0.5`, `[GRID]` moves
   the statistics 0.0% between 601 and 1201 points, `[QTY]` matches a closed form to 0.0/5e-06/0.0
   across three kernels, `[PIVOT]` bit-identical to `terrain_swing` on a 4,616-tie probe.
3. **`[ALIGN]`** (§7), which is now a memory and bound D406's design.
4. **G2 and G3 are unspent** — 20 of 24 cohort4 names, and cohort3 was never touched.

## 9. R13

Sixth look at a price-level map. The ledger carried 259 terrain looks and 86 structure looks in;
D405 and D406 followed. **Seven programmes, none paid.**

**Evidence:** `data/d403_wick_potential.json` — eight cells, the object dump across the sweep, and
the per-name A′ enumeration. Runner `scripts/run_d403_wick_potential.py`.
