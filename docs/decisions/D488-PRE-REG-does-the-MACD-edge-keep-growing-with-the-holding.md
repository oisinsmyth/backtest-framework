# D488 — PRE-REG: does the MACD edge keep growing with the holding period, and does it cross its cost?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D488-PRE-REG-does-the-MACD-edge-keep-growing-with-the-holding-period-and-does-it-cross-its-cost.md`. The H1 above is the full title.*

**2026-09-12, committed before the runner exists** (CLAUDE.md, [R8](../RULES.md#r8)).
Directed by the principal: extend the hold.

---

## 0. Why this is the right next lever, and what bounds it

[D484](D484-RESULT-the-log-MACD-is-a-real-signal-that-fails-only-on-cost.md)
found a real MACD edge that reaches only **55% of its cost** at H=5, and **its grid stopped at
H=5 while the edge was still rising** — a ceiling of my design, not of the effect.
[D486](D486-RESULT-cost-cutting-closes-70-percent-of-the-gap-and-stops-and.md)
then showed commission is **70–86% of cost** and is **fixed per round trip**.

**So the arithmetic favours a longer hold twice over, and one of the two needs no new edge at
all.** Cost is constant in H while σ grows as √H, so

    gross/cost  ∝  edge_sigma(H) × √H

**rises as √H even if `edge_sigma` is completely flat.** D484 measured it *rising*. That is the
hypothesis.

### Two constraints, both binding, both stated before the design

1. **P2 caps the hold at the venue's flatten time.** The fixture's session is 18:00 → 16:59 ET.
   The two venues that permit automation ([P6](../RULES.md#r11)) flatten at **4:10pm ET**, so the
   last usable exit is the **h15 segment (ends 4pm ET), index 21**. Maximum within-session hold
   from the 18:00 open is therefore **22 hours** — which is precisely C1's window.
2. **The principal's closure forecloses most of that on the index roots.** *"The index overnight
   leg at micro cost (any gate, window or size) is closed for the prop book"*
   (`COMPONENTS_PROP.md`, 2026-09-12). **Any ES/NQ/YM hold spanning the overnight is inside that
   closure and will not be run.** Only the **day session** remains open for those roots.

### And the consequence, computed now so it cannot be discovered late

If `edge_sigma` were flat, NQ's 0.55 at H=5 would need **√(H/5) ≥ 1/0.55**, i.e. **H ≈ 16.5
hours**, to reach gross/cost = 1. **That is inside the closed window.** Confined to the day
session (H ≤ 7) NQ reaches only ≈ 0.65.

**So this test cannot rescue the index roots, and I am saying so in advance.** Its value is
concentrated in the **non-index** roots, where no closure applies — and GC and CL were D484's two
largest cells (+0.0326 and +0.0337 σ).

## 1. Data, fixed now

| | |
|---|---|
| fixture | `data/fixtures/fut_sessions_hourly.csv.gz` (spec `59a151d`), 23 hourly segments h18…h16 |
| roots | **ES, NQ, YM, ZN, ZB, GC, CL, 6E**. RTY excluded, fails gate **G2**. Each root's own G1–G5 read and required to pass. |
| window | **2016-01-04 → 2023-12-29**, each root's own `usable_start` honoured. **2024+ sealed**, gate raises. |
| contract | `same_front` only; contract-pure over the trailing **78 bars** (3 × the slow EMA) |

## 2. The construction, fixed now — and NOTHING about the signal changes

**The signal is D484's, unaltered.** Same variants, same published parameters, **no re-tuning**:

- **B1 (primary)** — log **Impulse MACD**, ZLEMA/SMMA length **34**, signal **9**, with `md == 0`
  a **NO-TRADE** state;
- **B2 (secondary)** — plain log MACD histogram, **12/26/9**.

**Any parameter change would make this a search and a different, far more dangerous study.**

**Entry** at the open of hour t+1 after the signal at hour t; **exit** at the close of hour
t+H. Entries are formed at **every eligible hour**, so holds overlap heavily — which is why §4's
null is a rotation.

**Eligibility differs by root class, and that is the closure being honoured in code:**

| roots | holds H (hours) | entry restriction |
|---|---|---|
| **non-index**: ZN, ZB, GC, CL, 6E | **5, 8, 11, 16, 22** | exit index ≤ 21 (flat by 4pm ET) |
| **index**: ES, NQ, YM | **5, 7** | **entry index ≥ 15 (h09) and exit index ≤ 21** — the hold lies wholly inside the day session and never spans the overnight |

**H=5 is carried on every root as the replication anchor against D484.**

## 3. The statistics, fixed now

**S1 — scale-free, every root** (no contract specs needed, which is why it is primary):
per (root, variant, H), the edge in σ units `mean(signal · r_fwd) / σ(r_fwd)`.

**S2 — the growth exponent, which IS the hypothesis:** the OLS slope of
`log(edge_sigma × √H)` on `log H`, pooled across roots per variant. **A flat `edge_sigma` gives
slope 0.5; D484's rising edge predicts slope > 0.5.** Reported per root and pooled.

**S3 — tradeability, only where a verified micro spec exists:** `gross_ticks = edge_sigma ×
σ_ticks`, against that micro's cost (`$3.00 / tick_usd + 1.009` ticks), and the ratio
`gross/cost`.

> **S3 IS AVAILABLE ONLY FOR ES, NQ AND YM** (MES/MNQ/MYM are in
> `data/futures_contract_specs.json`), **and those are exactly the roots the closure confines to
> the day session.** **GC, CL, ZN, ZB and 6E cannot be costed here**: MGC, MCL and M6E are absent
> from the committed specs, and the specs file's own provenance records that CME returns 403 to
> plain HTTP so they were read through a browser. **Costing the non-index roots is therefore
> DEFERRED to a verified specs fetch and is not part of this record.** No micro tick value will
> be guessed — the specs file exists precisely because hardcoding them was refused once already.

## 4. The null, fixed now

**R1 (primary) — circular rotation of the SIGNAL series** against the returns, within each root.
Preserves the signal's autocorrelation (D484 measured lag-1 ρ = **+0.886** for the impulse
histogram), the returns' volatility clustering, and both marginals exactly; destroys only the
alignment. **Overlapping holds make any i.i.d. null and any naive t-statistic invalid**, and
D484 measured the gap: a sign shuffle's p95 was **1.7× too narrow**.

**R2 (secondary)** — per-observation sign randomisation, reported so the gap stays visible.

**2,000 draws each.** Report p50 and p95 and carry the **bootstrap SE of the p95**; an observed
value within **2 SE** of a p95 is **UNRESOLVED**, not a pass. One-sided.

## 5. The bars, fixed now

| verdict | requires |
|---|---|
| **EDGE GROWS** | S2's pooled slope **> 0.5** and exceeding R1's p95 by > 2 SE — the edge per σ rises with H, not merely the σ |
| **EDGE SURVIVES** | S1 > 0 at the longest H on each root, clearing R1's p95 by > 2 SE — a weaker claim: the edge does not decay away |
| **TRADEABLE** | S3's `gross/cost` > 1.0 at some H on a root where S3 is available — i.e. **on ES/NQ/YM inside the day session only.** §0 predicts this fails. |
| **COMPONENT** | none of the above suffices: `COMPONENTS_PROP.md` C-a, C-c, C-d, C-e on a daily P&L series at minimum size, plus C-b's routing, its own runner and its own record |

**Nothing enters the ledger, the vault or either book off this runner. 2024+ stays sealed.**

## 6. Predictions

- **W-a.** S2's pooled slope is **> 0.5** on B1 and clears R1 — the edge per σ keeps rising, so
  `gross/cost` grows **faster** than √H. *Reason: D484 measured edge_σ rising monotonically
  across H=1,2,3,5 on NQ (+0.0090 → +0.0177) and the grid ended while it rose.*
- **W-b.** The rise **decelerates**: the slope measured over H=5…22 is **below** the slope D484's
  H=1…5 implies. *A signal built on a 34-bar smoother should not keep improving indefinitely.*
- **W-c.** **No index root is TRADEABLE** inside the day session at any H — §0 puts NQ at ≈ 0.65.
- **W-d.** **GC and CL show the largest S1 at the longest H**, extending their D484 lead, and are
  the roots that would clear cost if costed. *This is the prediction that decides whether the
  specs fetch is worth doing.*
- **W-e.** R2's p95 is again **narrower** than R1's on every root and variant, as in D484.

## 7. What would make me wrong

S2's pooled slope clearing R1's p95 while also exceeding the H=1…5 slope — i.e. the edge
*accelerating* with the hold rather than decelerating, which would mean the signal's useful
horizon is well beyond anything tested and the grid should be extended again rather than costed.

## 8. Stated limitations, before any number exists

1. **The volume-clock exit (D472, +10.4%) is NOT applied**, so every figure understates by
   roughly that much.
2. **The 1.009-tick crossing is an ES measurement** assumed for other roots.
3. **Overlapping holds** mean the effective sample is far smaller than the row count; only the
   rotation null's distribution is used for inference.
4. **The longest holds have the fewest independent windows** — H=22 admits one entry per session,
   so ~2,000 genuinely independent observations per root, and heavy overlap elsewhere.
5. **This is in-sample.** 2024+ is the confirmation slice and is not read.
6. **Eight roots are not eight independent draws**: ZN/ZB are both US rates, ES/NQ/YM all equity
   index. Effective breadth is nearer 5.
7. **A 22-hour hold is C1's window**, and on the index roots that window is closed. The non-index
   roots have no such history — **but neither have they any prior evidence**, so a long-hold
   result there is a first look, not a confirmation.
