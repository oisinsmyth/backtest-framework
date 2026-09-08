# D385 PRE-REGISTRATION — the event density over its time calibration, with a swept sharpening power

**R8: committed before the runner exists. Result separately.** Stage 0 again — a premise check. It
scores no cell, tests no signal, admits nothing, touches no multiplicity ledger (R13), and reads no
holdout.

**This is D384 rebuilt after its close was withdrawn** (`6e1e899`). D384 failed for two reasons, both
of which this record is designed around: it measured **one density at the final mining bar** instead
of §4's per-bar pooling, and it measured the **time density**, which is nearly a functional of the
return distribution — the very thing N2 preserves. The second is the principal's diagnosis and it is
the load-bearing correction here.

---

## 1. The construction

**The time density is the calibration, not the signal.** Measured on 60 ETFs, it is a leptokurtic
blob on zero (75.4% of bars inside 1 EW-sd at half-life 5, against a Gaussian's 68.3%) whose only
real feature is negative skew — a return-distribution fact. Testing it against a null that preserves
the return distribution was close to tautologically null.

**The signal is event mass relative to time spent.** Two densities on the same log-deviation
coordinate `x = log P − log EMA(P)`:

```
g_t   TIME density  — EVERY bar injects at its own x_t          (the calibration / denominator)
f_t   EVENT density — only a TRACKED EVENT injects at its x_t   (the numerator)

s_t   = normalise( (f_t / g_t)^p )   over the support where g_t > 0.05 · max g_t
```

Both are exponentially weighted, both built at bandwidth `h = h_eff · √p`, and `s` is the object
every verdict is read from.

**Own-time deviation, construction (A) — no frame shift.** Each bar contributes at *its own* `x`, so
the object is stationary and needs no moving origin. D384's amendment established (A) as the right
stage-0 object; the ratio additionally requires numerator and denominator to share a frame, which (A)
gives for free. `[FRAME]` is therefore not consumed here, and the record does not claim it.

---

## 2. Why the power goes on the RATIO, and why `h` moves with `p`

**The principal's proposal was `f_t = λ f_{t-1}² + (1−λ) A_t²` renormalised. That form degenerates**
— measured, `temp/d384_power_density.py`: effective width collapses from 0.0268 to 0.00125 (one grid
cell) inside **10 bars**, 99.9% of mass in a single bin, and it stays there permanently. Density
values are not bounded by 1, so iterated squaring is winner-take-all and renormalising only rescales.
**No renormalisation rescues it; the fault is the compounding, not the scale.**

**The accumulation therefore stays LINEAR and the power is applied at READ time.** This keeps the
recursion that `[REC]` proves exact, and translation commutes with pointwise power exactly
(0.000e+00), so nothing in the proved machinery is lost.

**The power applies to `f/g`, not to `f`.** With events drawn as a random subset of bars — so the true
excess is flat — the systematic tilt of `s` across 40 draws is:

| `p` | power on the ratio | power on `f` alone |
|---|---|---|
| 1 | 0.0070 | 0.0070 |
| 2 | 0.0152 | 0.4313 |
| 4 | 0.0235 | 0.8640 |
| 8 | 0.0518 | 1.1937 |

**Power on `f` alone manufactures excess where none exists**, because `f^p/g` is tilted toward wherever
`g` is large. Power on the ratio preserves "events distributed like time ⇒ flat" at every `p`.

**`h = h_eff · √p`, because otherwise `p` is bandwidth in disguise.** On an isolated event, `f^p`
normalised is *identical* to a kernel at `h/√p` (agreement 1.4e-14). Holding `h` fixed, an isolated
event's width collapses 0.0366 → 0.0129 across `p`; reparametrised it holds at 0.0366 → 0.0432.
**A residual +18% drift remains and is disclosed** — `g` also moves with `h` — so the de-confounding
is near-exact, not exact, and the result must not attribute an 18%-scale effect to `p`.

**`p` buys concentration and pays in variance.** Compared at equal `g` (pair at −5%, solo at +5%), the
pair/solo height ratio runs **1.60 → 2.87 → 9.63 → 120.76** across `p ∈ {1,2,4,8}`. The cost is noise:
within-draw CV rises 0.069 → 0.222. **The null absorbs this because it goes through the identical
pipeline**, but high `p` is expected to have a wider null and therefore a higher bar.

**`p` is a free parameter and is SWEPT, never picked** — R14's addition. `p = 1` is the linear
construction and anchors the sweep.

---

## 3. Memory, and the fork this record does NOT close

**The decay rule is the principal's parked fork and this record uses a scaffold, not a resolution.**
`f` advances only on event bars, so its half-life is measured in **events**. That is event-time decay,
which the principal correctly objected to on coherence grounds — the centring EMA still runs in
calendar time, so the two memories are not tied. **This record does not claim the fork is settled.**

The scaffold is chosen for one measurable reason: **it makes `n_eff` constant.** With the half-life in
events, `n_eff ≈ 1.44 × hl` for every name and every event type. That is the direct fix for what
killed D384, where `n_eff` was **14.5 bars** at half-life 5.

**`g`'s calendar half-life is TIED, not chosen:** `hl_bars = hl_events / (that name's event rate)`, so
numerator and denominator cover the same span. Data-set, per name and per type.

**Event rates, measured** (`temp/d384_event_rates.py`, 60 names): swing low **21.0** per 100 bars,
swing high **21.0**, lowest low in 20 **10.8**, highest high in 20 **~10.8**. The rare types —
reversals at 2.4, moves >2% at 4.0 — are **excluded**, because at those rates a calendar window holds
1–2 events and nothing can be resolved. **This is my choice, not the principal's, and it narrows his
family to its dense members. It is declared here so it can be objected to before the runner exists.**

---

## 4. The grid

| | |
|---|---|
| **event types** | swing low, swing high, lowest low in 20, highest high in 20 — 4, all ≥10.8 per 100 bars |
| **sharpening power `p`** | **1, 2, 4, 8** — swept, reported, never picked |
| **event half-life** | **20, 40, 80 events** — `n_eff` = 28.9 / 57.7 / 115.4, constant across names and types |
| **`h_eff`** | Silverman on the EW spread of `x`, floored at the bar's own resolution (D384's rule, unchanged) |
| **names / draws** | 60 / 25, matching D384 so the two are comparable |

**48 cells.** Under R13 no strategy ledger is touched — there is no strategy.

---

## 5. What is measured

**Primary: the TV distance between the observed `s_t` and the null's mean `s_t`, evaluated at every
20th bar after warm-up and POOLED per name by the median** — the per-bar sampling D384 declared and
did not do.

**The null reference is leave-one-out**, per D384 §7: each null draw's TV against the mean of the
*other* draws, which is the same statistic computed under the null. **D384's first run omitted this
and would have reported ~27 SE of structure that was pure artefact.**

**Reported beside it:**
1. **`n_eff` for every cell** — the number D384's failure turned on, never again absent from a table.
2. **Where the excess sits** — `s`'s peak location, and whether it is one-sided.
3. **Mode count** of `s`, observed against null.
4. **The support fraction** — how much of the grid survives the `g > 0.05·max g` floor, since a ratio
   is meaningless where its denominator is empty.

---

## 6. Decision rules

**P1 — is there excess structure a shuffle cannot produce?** Observed TV against **N2**'s leave-one-out
distribution. Cleared where observed exceeds N2's p95 **by more than 2 SE**.

**P2 — the shape in `p`.** Monotone rise, a hump, or flat. **A single clearing `p` with neighbours
inside the null is a knife-edge and is reported UNRESOLVED.** Because `p` costs variance (§2), a rise
that stops is the *expected* shape and a monotone rise to `p=8` should be treated as suspicious, not
as confirmation.

**P3 — the shape in event half-life.** Same reading, across 20/40/80.

**P4 — do the four event types agree?** Four types that disagree at random is noise; lows and highs
behaving *oppositely* is a directional claim and would be the interesting outcome.

**Nulls:** **N2** (iid bootstrap of standardised returns re-scaled by the observed volatility path) is
load-bearing — it regenerates the path, from which events, EMA, `x`, `f`, `g` and `s` are all
recomputed. **N1** (iid bootstrap of raw returns) is the loose bound and proves little by design.

---

## 7. Assertions

| tag | what it proves |
|---|---|
| **`[STAT]`** | **the runner computes the POOLED-OVER-BARS statistic §5 declares** — asserted by re-deriving one cell's TV from an independent per-bar loop that never calls the pooling function. **This is the D384 failure and it gets its own assertion** |
| **`[NEFF]`** | `n_eff` is constant across names and types at fixed event half-life, to a stated tolerance, and is present in every emitted row |
| **`[REC]`** | the fast (`lfilter`) EW recursion equals the explicit bar-by-bar loop **bit-identically**, probed on a tie-heavy input — CLAUDE.md's rule for any vectorisation of a float recursion |
| **`[FLAT]`** | with events drawn as a random subset of bars, the **mean** of `s` over draws is flat at every `p` to a stated tolerance — §2's C1, the property that rejects power-on-`f` |
| **`[DECONF]`** | an isolated event's effective width does not move with `p` beyond the disclosed 18%, and **does** move under fixed `h` — the check must fail the un-reparametrised form or it proves nothing |
| **`[CAUSAL]`** | `s_t` reads no bar after `t`, proved by setting a future bar to an extreme |
| **`[NULL]`** | N2 reproduces the observed volatility path and return distribution and destroys autocorrelation |
| **`[SPLIT]`** | mining only, reserved window default-deny, no override |
| **`[GATE]`** | an **explicit** `assert_gates_passed` call |
| **`[X]`** | every audit raises on a deliberately broken input. **Each break must move the exact scalar its assertion compares** — three duds this session (D376, D380, D384) all broke what the assertion was *named* for instead |

---

## 8. Fixture and split

**`data/fixtures/etf_wide_daily_raw.csv.gz`** — 551 names, 2,516 mined bars, gated `e22350a`.
**Split unchanged from D382/D384: mining → 2019-12-31, RESERVED 2020-01-01 onward, untouched.**
A third look at a window already mined; under the principal's ruling of 2026-09-07 the cost is the
**prior**, not validity, and it is disclosed.

---

## 9. Predictions

| | |
|---|---|
| **Q1** | **P1 clears somewhere.** Unlike D384 this is not testing the return distribution against a null built to preserve it — swing lows clustering at characteristic deviations is a real, separable claim. If it fails *here* the family is genuinely empty |
| **Q2** | **the clearing is stronger for the 20-bar extremes than for the 2-bar fractals**, because a fractal swing is a local wiggle and a 20-bar low is a level |
| **Q3** | **P2 humps and does not rise monotonically** — `p`'s variance cost should overtake its concentration benefit by `p = 8` |
| **Q4** | **lows and highs behave the SAME, not oppositely.** If they differ I will suspect a sign or masking error before I believe a directional claim |
| **Q5** | **the support fraction falls with `p`** — narrower effective structure means less of the grid carries mass |
| **Q6** | **AGAINST myself: `n_eff` will still be the binding constraint at event half-life 20** (`n_eff` 28.9), and the shortest half-life will look noisiest rather than sharpest |
| **Q7** | `[FLAT]` and `[DECONF]` both hold first time. **D384's Q7 made this same prediction about `[FRAME]`/`[REC]` and was falsified — it fired twice** |

---

## 10. What would make me abandon this

- **`[STAT]` fails** → the runner is not computing the declared statistic. This is D384's exact death
  and it is now an assertion. Stop, fix, publish nothing.
- **`[REC]`, `[CAUSAL]` or `[NULL]` fails** → the construction or the null is not what §1–§3 describe.
- **`[FLAT]` fails** → the ratio form does not have the no-excess-⇒-flat property, so any excess found
  could be manufactured. §2's entire argument collapses with it.
- **`[DECONF]` fails** → `p` is not separable from bandwidth and the sweep is unreadable.
- **P1 fails at every `p`, every half-life and every type, with `n_eff` reported adequate** → the
  family carries no excess structure a volatility-matched shuffle cannot produce. **Close it, and this
  time the close is on the declared statistic.** If `n_eff` is *not* adequate, the finding is
  "untestable at this resolution", which is not the same thing and must not be written as a close.

---

*Pre-registered 2026-09-08. Runner does not exist at the time of this commit (R8). Stage 0: scores no
cell, admits nothing. The decay-coherence fork of §3 is OPEN and is the principal's. The narrowing to
dense event types in §3 is mine and is flagged for objection.*
