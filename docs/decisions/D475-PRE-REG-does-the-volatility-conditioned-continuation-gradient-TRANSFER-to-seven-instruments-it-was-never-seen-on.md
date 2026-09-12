# D475 — PRE-REG: does the volatility-conditioned continuation gradient TRANSFER to seven instruments it was never seen on?

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Follow-up to [D474 RESULT](D474-RESULT-the-pre-registered-bar-was-not-met-but-four-of-five-predictions-broke-toward-the-hypothesis-and-the-test-was-underpowered-where-it-mattered.md),
which left the principal's hypothesis — **volatility for timing, continuation for direction** —
UNRESOLVED with four of five predictions broken *toward* it.

---

## 0. The problem this design exists to solve, and it is not power

D474 found a monotone gradient on ES: hit rate rising 49.93% → 55.53% across horizons in the
top volatility quintile. **I had predicted the opposite sign.** So that gradient was found *post
hoc*, on ES, in-sample.

**ES 2016–2023 is therefore spent for this pattern.** Re-testing it there — even with a better
statistic and better power — would test **selection, not transfer**, which is the standing
lesson of D430: *"+80/trade in-sample became −29 on 803 unseen names; in-sample nulls test
selection, not transfer."*

So the primary test is **transfer to instruments this pattern has never been looked at on**, and
ES is demoted to a descriptive discovery set that carries no evidential weight.

D474's *other* two flaws are fixed as a consequence: the new fixture supplies ~22 hourly pairs
per session instead of 1–2, and the statistic is a **trend** rather than a family maximum.

## 1. Data, fixed now

| | |
|---|---|
| fixture | `data/fixtures/fut_sessions_hourly.csv.gz` + `.meta.json` (built 2026-09-12, spec `59a151d`) |
| structure | full Globex session **18:00 → 16:59 ET** as 23 hourly OHLCV segments `h18…h16` |
| **primary roots (7, unseen)** | **NQ, YM, ZN, ZB, GC, CL, 6E** — equity index, rates, metals, energy, FX |
| **discovery root (not evidence)** | **ES** |
| excluded | **RTY**, which fails gate **G2** (one reverting roll, 2020-06-14 RTYU0→RTYM0) and whose `usable_start` is 2017-07-10. Excluded on a stated gate, not on convenience. |
| window | **2016-01-04 → 2023-12-29**, honouring each root's own `usable_start`. **2024+ is sealed and not read**; a gate raises if any row past 2023 is reached. |
| rolls | **`same_front` rows only** (96.0–98.9% of sessions by root) — no window may straddle a contract change |
| gates | every primary root's own G1–G5 results are **read and required to pass** before it is used |

## 2. The construction, fixed now

Within a session, hourly segment returns `r_i = (h{i}_c − h{i}_o)` in **ticks** (the root's own
tick from `data/futures_contract_specs.json`; roots absent from that file are measured in
**price σ units** instead and flagged as such).

- **Horizon h ∈ {1, 2, 3, 4, 5} hours**, formed as consecutive non-overlapping runs of h
  segments within one session. D473 §3 puts the cost-optimal band at **60–325 minutes**; this
  grid covers it exactly, which D474's did not.
- **Signal (continuation):** the sign of the h-hour window's return; the trade is that sign,
  held for the **next** h-hour window, entered at its open and exited at its close.
- **Conditioner (volatility timing):** realised volatility over the **3 hourly segments
  strictly before the signal window** — D474's V2, the variant independent of the signal's own
  magnitude. Quintiles are formed **within each root × horizon**.
- D474's V1 (bucketing on the signal's own magnitude) is **not** the primary here: it conflates
  conditioner with signal. It is reported as a secondary.

## 3. The primary statistic — a trend, fixed now

D474's error was a family-maximum |t| over 40 cells: an instrument built to find one
exceptional cell, applied to a hypothesis that predicts a **monotone gradient**.

For each root × horizon, regress the per-observation **same-sign indicator** on the **quintile
rank (1…5)** by OLS. The slope is in **percentage points of hit rate per quintile**.

    slope[root, h]  =  d(hit rate) / d(quintile rank),  in pp

**PRIMARY STATISTIC `S` = the mean of `slope[root, h]` over the 7 unseen roots and 5 horizons
(35 cells).** One number, one test, no multiplicity correction needed. Per-root and per-horizon
breakdowns are reported but are not the test.

**Secondary, reported always:** hit rate and gross edge per cell, implied skill `a = hit − ½`
for comparison with D473 §3's table, and the net edge in ticks where a micro contract exists.

## 4. Two nulls, because the hypothesis has two ingredients

A control must break the claimed ingredient (standing error: D411's VOL-SHUF preserved the sign
it meant to test). This claim has two, so it gets two controls:

- **N1 — sign randomisation.** Within each root × horizon × quintile cell, independently
  randomise the sign of the signal, leaving the forward returns and bucket membership
  untouched. **Breaks the directional link**; tests whether any gradient exists at all.
- **N2 — quintile shuffle.** Randomly reassign quintile labels within each root × horizon,
  leaving signals and forward returns intact. **Breaks the volatility conditioner while keeping
  the directional outcomes**; tests whether the gradient is specifically about volatility rather
  than an artefact of bucketing.

**2,000 draws each.** Report each null's **p50 and p95**, and carry the **bootstrap SE of the
p95**. Per D373's rule, an observed `S` within **2 SE** of a null p95 is recorded **UNRESOLVED**,
not a pass. One-sided: the hypothesis predicts `S > 0`.

## 5. The bar, fixed now

| verdict | requires |
|---|---|
| **TRANSFER CONFIRMED** | `S > 0`, exceeding **both** N1's and N2's p95 by more than **2 SE**, **and** `slope` positive in **at least 5 of the 7** roots individually — a mean driven by one root is not transfer |
| **PARTIAL** | clears N1 but not N2 → there is directional predictability but it is not the volatility conditioner doing the work; the conditioner claim fails |
| **TRADEABLE** | additionally, on **ES/NQ/YM only** (micros exist and specs are committed), the top-quintile **net** edge > 0 ticks at micro cost, at ≥ 2 of the 5 horizons |
| **COMPONENT** | none of the above suffices: `COMPONENTS_PROP.md` C-a–C-e on a daily P&L series at minimum size, its own runner and its own record |

**Nothing enters `COMPONENTS_PROP.md` or either book off this runner**, and **2024+ stays
sealed** regardless of outcome. A pass licenses writing a component study; that is all.

## 6. Predictions, and a disclosure attached to them

**DISCLOSURE: I now predict a POSITIVE gradient, and that prediction is informed by having
seen it on ES.** That is precisely why ES is excluded from the primary — a positive result there
would be worthless. These predictions are about the seven roots I have not looked at.

- **Y-a.** `S > 0` and clears **N1**'s p95 by more than 2 SE. *Reason: the ES gradient was
  monotone across five horizons and scale-free in hit-rate terms, which is hard to produce by
  chance in one instrument.*
- **Y-b.** `S` **fails** to clear **N2**'s p95 by 2 SE — i.e. the gradient survives sign
  randomisation but not quintile shuffling, meaning something predicts direction but the
  volatility bucket is not what selects it. *This is my genuine expectation and it is the
  prediction most likely to embarrass me.*
- **Y-c.** The gradient is **positive in the three equity-index roots** (NQ, YM plus ES
  descriptively) and **weaker or absent in ZN, ZB, GC, CL, 6E** — i.e. it is an equity-index
  phenomenon, not a futures-wide one.
- **Y-d.** **No root × horizon cell is TRADEABLE** at micro cost on 2 or more horizons.
- **Y-e.** Implied skill in the best cell stays **below 5%**, beneath D473's threshold for
  reaching C-a's Sharpe 0.5.

**If Y-a holds and Y-b breaks** — the gradient clears both nulls — that is the strongest result
available from this design and the point at which a component study is warranted.
**If Y-c holds**, the honest reading is narrower than the hypothesis: volatility-conditioned
continuation in equity index futures specifically, which is a different and smaller claim.

## 7. What would make me wrong

`S` clearing both nulls by more than 2 SE with at least 5 of 7 roots individually positive. I
expect N2 to be the one that kills it.

## 8. Stated limitations, before any number exists

1. **Hourly resolution.** A window boundary lands on an hour edge; sub-hour structure is
   invisible, and the volume-clock exit (D472, +1.18 pp) is **not** applied, so every net figure
   will understate by roughly that much.
2. **Cost is measured for ES only.** D465's 1.009-tick crossing is an ES measurement; NQ, YM and
   the non-equity roots are assumed one tick wide in the tradeability stage and that assumption
   is not verified here. `tbbo` covers 2025-09→2026-09 for all roots and could settle it later.
3. **Five asset classes is not five independent draws.** ZN and ZB are both US rates and are
   strongly correlated; NQ and YM are both equity index. Effective breadth is nearer 4–5 than 7,
   and the 5-of-7 consistency requirement does not fix that.
4. **In-sample only.** Even a pass is an in-sample pass on unseen *instruments*, not an
   out-of-sample pass in time. 2024+ remains the confirmation slice for whatever follows.
5. **No exit engineering.** Fixed hold to the window close; no stop, no target. D471 §5's
   `adverse/|move| ≈ 0.50` says a stop would bind, and its effect is not modelled.
