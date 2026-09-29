# Better predictors for the opening break: five analyst lanes, 2026-09-29

*Commissioned by the principal after D668's development run and its oracle.*

> "spin off multiple fable 5.1 agents 4-5, have them look at the opening range variable we have examined before, then
> have them reason and use the results that have already been tested. To recommend some better predictors. Keep in
> mind that some variable/confluences, may be size up or down vs a yes/no filter ... the reasoning has to be from the
> frame of a opening range break out"

**Two instructions were added mid-run:**
- *"a filter/confluence does not need to be directional, it can predict big moves, and our direction is from the
  break out"*;
- *"if a variables sign points in the opposite direction and it is a real contraindication I think its ok"*. The
  conditions put to the analysts: a mechanism, a sign declared per root before confirmation, and stability.

**Constraints:**
- The five analysts (Fable 5.1) were read-only and computed nothing on prices.
- Every seal was stated in their briefs: the vault from 2025-03-01, CL/NG post-vault until 2026-10-10, SqueezeMetrics
  raw data, Sierra files and `data/raw/`.
- Their numbers cite committed records and JSON only.
- **This note is research input. It is not a pre-registration, and nothing in it has been tested.**

**The lanes:**
- **A:** dealer positioning and options;
- **B:** order flow at the open;
- **C:** price structure and the volatility state;
- **D:** cross-market and root context;
- **E:** sizing, exits and the design of the expected-profit model.

## 1. Synthesis

### 1.1 Where all five converge: the direction comes from the break; predict the SIZE of the day

The trailing-stop break (E4) behaves like a long straddle on the day's range, with the break choosing the leg:
- the loss is capped near the initial stop (NQ's stop exits average −4.0 bp; a failed break costs about −19 bp);
- the gain grows with the day (the 194 close exits average +57.5 bp; the top 1% of trades make 123% of NQ's net).

So **an unsigned predictor of a big day** raises expected gross at an unchanged P(hold). Unlike a directional filter
at AUC 0.53, a size filter keeps the trend days rather than dropping them at random.

**The structural proposal (lane E, with the inputs from A–D):** a walk-forward model of ln(RTH range / ATR20) fitted
on **every session**, not only the break trades. That is about 2,300 sessions per root, pooled across the roots with
root intercepts.
- The target is far less noisy than trade P&L: information that reads t ≈ 1.7 in the trade regression reads t ≈ 11
  here, which is D665's gamma t of 8–12.
- **Validation, before any P&L is read:**
  1. an out-of-sample rank correlation against a time-rotation null;
  2. calibration;
  3. a clock-only arm that must fail;
  4. **P(hold) must be flat across forecast deciles.** A rising hold rate means direction has leaked in.
- Only after that is E4 gross read by decile.
- The form is frozen on ES/NQ, then run blind on YM/RTY.

**The candidate size inputs, all known before the entry:**

| input | lane | sign | data |
|---|---|---|---|
| the options market's implied move: the nearest-expiry ATM straddle at the prior close, one day, in ATR units | D | + all roots (YM borrows ES's; RTY a weaker blend) | ES/NQ options books on disk; before 2022 the weeklies |
| continuous dealer gamma −GEX/V20, SPX GEX on every root (own book beside it on ES/NQ) | A | + all roots | on disk (licensed; prior row) |
| relative volume, 09:30 → the bar before entry, against the same clock window's 20-session mean | B | + all roots | the D462 one-minute fixtures, all four roots |
| the overnight two-way range (Globex range − \|gap\|)/ATR20 | C | + (RTY weaker) | ES/NQ on disk; YM/RTY need a Globex build |
| macro-release days: CPI and NFP size up; FOMC size down or skip (its move comes at 14:00) | D, C | as stated | `cme_session_calendar` flags from 2016 |
| \|TICK z\|, \|A7\| (participation, either side) | B, A | + (low weight) | on disk (A7 for YM/RTY being built) |
| \|gap\|/ATR | C vs E | **disputed** (see 1.4) | on disk |

### 1.2 Contraindications: a small fixed-sign layer, never fitted

Lane E's form:
- a score S = Σ s_j·x_j over alignment dummies, with s_j = ±1 declared from mechanism before YM/RTY and the ES/NQ
  numbers disclosed as "seen";
- **veto when S ≤ −1**, or when the projected value falls below 1 × cost;
- a term whose walk-forward sign stability is below 0.8 is REMOVED, never re-signed;
- a random-sign arm must fail.

| term | sign | mechanism (the ORB frame) | lane | status |
|---|---|---|---|---|
| overnight probe of the level: Globex traded beyond L (strong form: beyond the stop) and is back inside by 09:30 | **−** all roots | the stops were run overnight, so the RTH break is a *second* break; D666/D681 found second breaks are a coin flip | C | new; ES/NQ on disk |
| aligned aggressor flow (D × A7), or better, B's **absorption ratio** (net aggression ÷ travel) | **−** | the flow that caused the break is spent; heavy aggression to reach L means resting supply absorbed it | B, A, D, E | the conditional sign is negative on both roots, but ES's raw split goes the other way; stability 0.82 NQ, 0.66 ES |
| an aligned gap in its trailing top quintile of \|gap\|/ATR | **−** | the gap spent the day's range budget; the break is late | C, E | coefficient stable (1.00 ES, 0.83 NQ) |
| monthly opex Friday | **−** (skip) | expiry gamma pins and compresses the day (Golez & Jackwerth, JFE 2012; D409) | A, D | report by era (D614) |
| FOMC day | **−** (skip, or hold the initial stop to 14:00) | the expansion arrives at 14:00; a 09:46 entry is trailed out in the lull | D | |
| gap aligned with the break | + | the auction has accepted the overnight move | E | NQ +5.31 vs +1.82; ES +2.12 vs −1.13 |
| constituent TICK aligned | + (NQ-like roots) | a futures break without cash breadth is futures-led and fails | E, B | weak on ES (TICK-SP is arbitrage-linked) |
| cross-index confirmation (the other roots are beyond their own yesterday's level) | + ES/YM/RTY, ~0 NQ | a complex-wide break is a re-pricing; a lone break is a rotation (YM: one name can break it) | D | on disk, all four roots |
| short side on ES/YM | veto | the drift; ES shorts are absorbed by dip-buying | D | cost avoidance, not edge (N1 absorbs it) |

### 1.3 What to drop or re-role

- The **linear clock** (stability 0.57/0.50). Replace it with a clock-normalised excess (0.25A over the typical
  |move| at that clock; C), or a fixed √(time left) prior (E).
- The **short-gamma dummy**. Use continuous gamma from one measure (A, D).
- **Charm/vanna and the gamma-flip distance**: vendor lore, and the flows are too small (A).
- **Weekday**: one cell in a chance-level scan (C, D).
- **VIX**: not on disk, and the vol-tercile evidence has the wrong sign for a "high VIX" prior (D).
- **Directional OLS on E4 gross, the 2 × cost filter and the 1/2/3-micro ladder** (E). At AUC 0.53 a hard filter drops
  trend days at random: D668's filter cut NQ's dollars 62% and Sharpe from 0.60 to 0.51. The replacement:
  - veto at 1 × cost;
  - one micro;
  - size ACROSS TIME by the drawdown cushion (Grossman & Zhou 1993), not across trades. One MNQ at today's price is
    already about full Kelly on a prop cushion.
- **Exits:** keep E4. One pre-declared variant, reported and never gated: a wider trail (0.375A) on predicted
  big-size days.

### 1.4 Disagreements to settle before a design

1. **\|gap\| as a size input.**
   - E enters it as + (a big gap marks a big day).
   - C decomposes D681's classes and finds that the gap *spends* the range budget: NQ's gain-if-hold falls 35 → 24 →
     20 bp across the open classes, while the loss is fixed. So C makes it a contraindication (size-down).
   - The data C cites favours C. Declare it **−**, or leave it out.
2. **A7.**
   - A and D: a genuine contraindication, negative on both roots.
   - E: its sign is not stable across roots in the raw splits.
   - B: on NQ, "large-lot" is a 1-lot cut from 2019, so it is plain aggressor imbalance. Re-role it as the denominator
     of an **absorption ratio**.
   - Prefer B's ratio, with E's stability gate.
3. **Gamma measure.** A and D: unify on SPX GEX on every root, because the ES/NQ asymmetry is mostly measurement
   (short on 11% vs 39% of days). E: a fixed κ from D665. They are compatible: continuous SPX GEX, its slope fixed
   from D665 or fitted in the size model.

### 1.5 Ceilings and warnings, all lanes

- **No lane expects more than about +0.01–0.04 AUC from any single variable.** Lane E:
  - AUC 0.60 on *direction* needs 3.4× the separation any known variable shows;
  - the size route is the one that does not need it.
- **The E4 size oracle has never been computed:** E4 gross by the ex-post RTH range/ATR quintile, with P(hold) beside
  it (C).
  - D661's 60-minute-hold ceiling (34% vault power even with perfect size foresight) does not transfer to a trailing
    exit.
  - It is the cheap first step: it sizes the prize of the whole size-model route.
- **The component line** (E): 2024 is 66% of NQ's dollar P&L. On the ledger's 2016–2023 window the break nets about
  $407 a year (Sharpe about 0.3), which fails the component standard, and the 2024+ NQ day session is spent (D503).
- **Multiplicity:**
  - every ES/NQ number is development;
  - the confluence splits were read in a 472-subset scan at chance level;
  - YM/RTY (and the vault) are the only clean evidence;
  - any change to D668's nine features before the YM/RTY run would need a committed amendment. **None is proposed:**
    D668 runs as registered, and these ideas go to a successor design.

## 2. The reports, verbatim

The reports follow as delivered, lightly condensed where a list was flattened (each lane's main report, then its addenda). The full text is in the session record.

### Lane A — dealer positioning and options mechanics

#### Report

In-sample 2016-01-04 → 2025-02-28 throughout; nothing computed, nothing sealed opened.

**0. The frame this lane fits.** E4's economics (≈ 44·P(hold) − 19; stopped trades −4.0 bp, the 194 NQ close-exits +57.5 bp, `diag_d666.json` A4) make the trailing stop a **size-capture device**: the break supplies direction, and any variable that predicts a large |move| raises the expected value of the winners without touching P(hold). D665 is the template — gamma predicts |F| at t 8–12 beyond σ20 and predicts carry not at all (D663). So every item below is scored as a **non-directional size predictor first**, and the roles are: floor filter (skip quiet days), exit modulator (trail width), and only lastly direction. One correction for lane E: if mean ≈ a·s − c and sd ≈ b·s (s = expected day size, c = the fixed stop-loss-plus-cost), edge per unit risk rises with s but the Kelly size falls ∝ (a·s − c)/s². Size predictors justify a **floor and constant-dollar risk**, not D668's 1/2/3-micro escalator.

**1. Ranked predictors.**

1. **Continuous dealer short gamma, g = −GEX_prior / V20 (D663's definition), unsigned by D.** Prior-row SPX GEX (SqueezeMetrics, licensed) for all four roots as the market-wide measure; the own carried book (`fut_es_options_eod`, `fut_nq_options_eod`, D581's Black-76 convention) beside it for ES/NQ. Mechanism: short-gamma dealers hedge with the move, so the day travels further either way; the break picks the side. Role: **floor filter + trail-width exit modulator**. Sign per root: positive for size on all four (YM/RTY through SPX GEX; D665's |F| gradient is 13.6→36.9 bp ES, 21.0→49.6 NQ by quintile, t 5.9/4.8 beyond σ20). Evidence for: D681 NQ short-gamma +6.37 vs +2.98 (t ≈ 1.3); D668 NQ +2.0 standardised, same sign in 100% of refits; ES oracle gamma-met +2.83 vs +0.99 gross. Against: five carry nulls (D581, H-O6, S-H, D662, D663); NQ own-book H1 slope −1.54 on the 60-min no-stop F. That contrast is the point — size pays only under E4. Estimated gain: the dummy already buys ~3.4 bp on NQ; a continuous, σ20-controlled g might add 1–2 bp on the kept half and ≤ +0.02 AUC. Collinearity: replaces f4; correlates with σ20 and with 2020/2022, which must be controlled.
2. **Unsigned re-roles of D668's signed features as size-of-day predictors:** |gap|/A, |TICK z|, |A7|, and the 09:30→entry range/A. D668's signed gap coefficient is −2.1 while the gap-class dummies are +1.4/+1.9: the gap's *size* predicts day size and its *sign* adds exhaustion — the unsigned form separates the two. A7-aligned is worse (D681 +2.78 vs +5.18): large-lot flow reads as participation, not direction, so |A7| is the honest form. Role: size/floor; expected sign positive on every root. Cheap: same columns.
3. **Monthly opex day and the post-opex session** (third Friday; `cme_session_calendar` has `quad_witching`). Mechanism: ATM gamma scales 1/√T, so expiry-day hedging pins and compresses the day (Golez & Jackwerth, JFE 2012: ≥ 11 bp pull on ES option expiry, half in the last 30 min); the Monday after, the unwound book leaves the tape unpinned. In-house: D409 measured |move|/σ√h compression into the monthly expiry on optioned stocks (Q1–Q5 −13.5%), size not direction. Against: D614 found no pinning on the 0DTE ladder. Role: **filter** (skip opex Friday), same sign all roots. ~12 sessions/yr, so ≤ 0.5 bp per trade overall; no AUC. Stivers & Sun (JBF 2013) OE-week returns are directional and single-stock — do not import as a direction.
4. **Same-day-expiry presence (the 0DTE natural experiment).** Peer-reviewed/WP evidence says same-day dealer gamma is net positive and damps (Adams et al.; Dim–Eraker–Vilkov), but is weakest in the first hour (1/√T), which is when this trade enters — an argument for item 1. In-house: D681 NQ post-0DTE +5.56 vs +3.72; D581's residue sat on sessions without a same-day expiry. Contradictory → **reported era/day split, not a feature.**
5. **VIX term structure and overnight VIX change.** Not on disk. Cboe's free daily history would supply prior-close backwardation and the 09:31 VIX open — usable for post-09:32 entries, not for the 29% open fills. Role: size modulator. Risk: one year's fit — 2022 was also backwardated and was NQ's second-best year (+7.37). Rank mid-low, new data.
6. **Distance of the break level to the zero-gamma crossing and to the largest-OI strikes** (carried book, ES/NQ only). Role: veto/exit. Against: the carried book sees ≤ 8.5% of same-day gamma (D581), calls short 42% of days vs SPX's 11% (D665 A1), and D618 showed any band centred on the price is a grid artefact. ≤ 0.5 bp.
7. **Single-name dealer gamma in NQ's mega-caps** (needs OPRA statistics for the top-7 names). A root-asymmetry explainer, not yet a predictor.
8. **Charm/vanna into the open — DROP.** Vendor lore only; directional; D661 sizes gamma flows at $0.5–2 bn/day, failing the bar at its best case.

**2. Why short gamma helps NQ and not ES; YM/RTY.** (a) Not the same instrument: ES's f4 is SPX GEX < 0 on 12% of trades, concentrated in 2020/2022 crisis tape; NQ's is a thin own book's naive sign, short 39%; the two ES measures agree on sign 69%. The like-for-like ES carried book did order F monotonically (D662 post hoc +0.48, t 2.30). (b) Crisis composition: ES's short-gamma trades coincide with breadth-aligned panic opens (gamma+tick −6.2, gap+gamma+tick −10.1 gross); the overnight move already carried the hedge, the open gaps through the stop, and the break is exhaustion. (c) Size convexity: E4's loss is ~fixed; NQ's gradient is wider and its cost lower. (d) Constituent hedging: SPX dealers are net long gamma on 90% of days and damp; NQ's mega-caps carry retail-driven single-name books where dealers are short calls (Ni–Pearson–Poteshman–White, RFS 2021; Barbon–Buraschi). **YM/RTY:** the SPX-GEX size effect should transfer; the NQ-specific tilt should not. Prediction: SPX-GEX f4 positive, t < 2 on both.

**3. Drop or re-role.** Drop the short-gamma dummy; carry continuous g from one measure (SPX GEX) on every root, own-book beside for ES/NQ. Re-role gap, A7 and TICK to unsigned size terms (keep the gap-class dummies). Add no gamma × shock interactions. Drop charm/vanna and the gamma-flip distance.

**4. The pre-registrable test.** H: E4 gross rises with unsigned g through the winners' size, not through P(hold). (i) HAC slope of E4 gross on g with σ20 and ATR20/price as controls; (ii) decomposition — slope of 1[hold] on g (≈ 0) and of the close-exit trades' gross on g (> 0); (iii) the book above vs below g's trailing 250-session median against the same split on σ20 — gamma must beat the vol split by > 2 bootstrap SE. Null: enumerated rotation of g purged ±10 sessions; N1 within the high-g sessions. Falsified if rank < 0.95, if σ20 absorbs the slope, if P(hold) carries it, or if the g-split book does not beat the σ20-split book. Trail-width variant reported, not gated.

**5. Risks.** Multiplicity (the NQ gamma split was one of 472 cells); look-ahead (GEX row dating; VIX open unknown for open fills; same-day 0DTE positions in no OI print); five carry nulls; D661's 34% ceiling must be re-derived on E4; licence: anything built on GEX informs the principal's own trading only.

#### Addendum: contraindications

| variable | ES | NQ | YM | RTY | mechanism | declared sign | stability |
|---|---|---|---|---|---|---|---|
| continuous unsigned g, size | C | C | C | C | short gamma widens the day either way | + all roots | D665 t 5–12, monotone quintiles |
| SPX GEX < 0 × gap-through open | X | none | X | X (weak) | the hedge is spent by the open; the break is exhaustion (ES n 61/36) | veto/size-down on ES/YM at open fills | UNRESOLVED (ES f4 stability 0.42; post hoc) — declare, gate nothing |
| opex Friday | X | X | X | X | expiry gamma pins the day | skip/size-down all roots | D409 36/36; report by era (D614) |
| post-opex Monday | C | C | C | C | unpinned book | + size | unmeasured; report only |
| same-day-expiry presence | — | — | — | — | damping | cannot be declared | fails (3) |
| VIX backwardation | — | — | — | — | stress tape | cannot be declared (2020 lost, 2022 won) | fails (3) |
| break into a large-OI strike | X | X | none | none | long-gamma dealers sell into the move | ES/NQ veto candidate | unknown; D618 artefact risk |
| charm/vanna | drop | drop | drop | drop | — | — | — |

A7-aligned is a genuine contraindication by these criteria (spent flow; negative on both roots, stability 0.66/0.82) and is a different variable from unsigned |A7| (participation → size); both admissible. The ES/NQ gamma asymmetry is mostly measurement, which is not a licence for root-specific signs: declare one sign per measure across roots.

### Lane B — order flow and participants at the open

#### Report

**Why aligned A7 is negative (ORB frame).**
1. **A7 is not "large-lot" on NQ.** The rolling 90th-percentile cut fell to 1 lot from 2019 (D658; the 2026-09 flag check shows NQ `net_large == net_all`). NQ's A7 is the plain aggressor imbalance; ES's cut fell to 2–3 lots from 2022. It measures urgency, not information (Barclay–Warner, JFE 1993).
2. **It is measured 09:30 → a checkpoint ≤ entry, i.e. the flow that CAUSED the break**, already in the price (D661 §6). Chordia–Roll–Subrahmanyam (JFE 2002), Chordia–Subrahmanyam (JFE 2004): lagged imbalance predicts reversal once the current imbalance is controlled.
3. **Absorption.** A break reached on heavy aggression met resting supply at yesterday's high; one that repriced on little aggression shows latent demand. D668 already encodes it: NQ travel +1.9 (stable 100%) and a7 −3.0 (82%) — "much travel, little flow" is the good break.
4. **Forced flow completes.** Stops sit just beyond yesterday's extremes (Osler, JIMF 2005); a gap-through open fires them plus MOO/index-arb and dealer gap hedges. ES shows it hardest (A7 −4.9).

A7 and TICK are structurally zero on the 29% open fills and A7 is zero before 09:45 — about half the trades; the features cannot see the class ES earns in.

**Ranked predictors.**
1. **Absorption ratio (flow per unit of travel)**: D × net aggressive volume / total volume, 09:30 → bar BEFORE entry, divided by travel; for open fills the overnight twin (Globex signed volume over |gap|/A). High = absorbed → fails. Negative on all roots, strongest ES, weakest RTY. Role: size modulator with a top-decile veto. Data: ES/NQ Sierra ticks on disk; YM/RTY after the D668 downloads. Estimate +0.02–0.04 AUC. Replaces f5 and f7.
2. **Signed-flow persistence** (share of minute bars with net aggression in D): a trend day is a metaorder executing (Lillo–Mike–Farmer 2005; Tóth et al. 2011). Positive all roots. Filter. +0.01–0.02.
3. **Relative volume at the break** (log volume 09:30→t−1 minus the same window's 20-session mean; D462 fixtures, all four roots). Positive everywhere. Size only. D647 vol_z; D531 P-B; Gao et al. (JFE 2018). +0.01–0.02 on gross.
4. **Cash breadth state and trend** (ADV/(ADV+DECL) or UVOL/(UVOL+DVOL) at t−1; ΔTICKz). RTY strongest (breadth ≈ the index); NQ sign uncertain. Direction veto plus size. +0.01–0.02.
5. **Trade-count intensity and mean trade size** (Jones–Kaul–Lipson 1994). Size. ≤ +0.01.
6. **Opening-auction proxy for open fills** (SPY/QQQ 09:30-bar volume vs its mean). Filter on open fills only. Small; new data for true imbalance.

Not recommended: small- vs large-lot divergence (NQ's cut is 1 lot) and retail proxies (micros are not a retail identifier, D485; Boehmer et al., JF 2021).

**Drop or re-role.** Drop A7 as an aligned confluence; re-role it as the denominator of #1 at 1-minute resolution. Fold f5 and f7 into #1; keep TICK as state + trend. Report the open-fill class separately. Say whether "large lot" is a rolling percentile (era-varying) or a fixed band.

**Test (#1).** P(hold) and E4 gross fall with the absorption ratio, on YM/RTY (ES/NQ development): walk-forward AUC of hold on ABS and the OOS slope of E4 gross on ABS's within-year rank, Holm across the evidence roots. Nulls: N2 permutation; a within-session time rotation of the minute flow; unsigned relative volume as the ingredient-breaking control that ABS must beat. Canaries: the flow window ends at t−1; the overnight twin at 09:29. Falsified if AUC < 0.55 with CI touching 0.5 on both roots, or if the unsigned control matches it.

**Risks.** The ES/NQ in-sample is spent for A7-sign hypotheses; Sierra's aggressor flag is validated only on five 2026-09 sessions; flow at the open has failed four times here (D658, H-O6, D485, D661, D494). Honest ceiling for the lane: AUC ~0.56–0.57. ABS is a realised Kyle-λ and interacts with short gamma — pre-register the interaction or omit it.

#### Addendum: non-directional predictors

E4 is option-like (stop exits −4.0 bp, close exits +57.5), so an unsigned |move| predictor raises expected gross at unchanged P(hold). D661 §2's floor: on a 60-minute hold, perfect foresight of the top-20% expansion days turns −3.15 into +4.65 net; E4 is more convex.

Ranked unsigned predictors: (1) **relative volume at the break** — hard filter below about p20 and size above; positive on every root; the net clears only where cost is small relative to range; no new data; ranked first in the lane, above the signed absorption ratio. (2) Trade-count intensity (size). (3) |A7|, the magnitude of the imbalance (size, not filter; UNMEASURED). (4) |TICK z| and the cash volume state (size; RTY strongest, YM weakest). (5) Overnight activity for the open-fill class (filter on the 29% open fills).

Which signed features work better unsigned: A7 — test D×A7 and |A7| side by side with RV present (D681's "not aligned" pools the half with A7 = 0 before 09:45, a three-way object read as two); expect D×A7 negative and |A7| positive but weaker than RV — one more in-sample look, to be recorded. TICK — yes, |TICK z| is the trend-day variable; keep signed TICK only as a veto. Gap — mixed: NQ's gap-through class is its weakest, so keep the dummies and do not add |gap|. Travel, gamma, side: already appropriate.

Risk: every size predictor is collinear with the others and with gamma; pre-register ONE composite (RV primary, the rest diagnostics), score it on |E4 gross| and through the size ladder, null it with the within-session flow rotation, confirm on YM/RTY.

### Lane C — price structure and the volatility state of the open

#### Report

**0. The three explanations, in the ORB frame.** E4 gross = P(hold)·G − (1−P)·L; from `diag_d666_gap.json` (E4, by open class):

| | NQ P(hold) / G / L | ES P(hold) / G / L |
|---|---|---|
| no gap | 0.54 / +24.3 / −17.9 | 0.52 / +16.2 / −15.6 |
| gap inside | 0.45 / **+35.1** / −19.4 | 0.45 / +18.8 / −18.8 |
| gap through | **0.58** / +19.8 / −20.2 | **0.60** / +18.3 / −15.8 |

**Signed gap −2.1 beside positive class dummies.** The dummies carry P(hold): an open beyond yesterday's extreme means Globex already accepted prices outside the range, so the break returns less often. The signed size carries G: a gap spends the day's range budget before the trade exists (the gap-through fill is 13.7 bp past the stop). On NQ G falls 35 → 24 → 20 across the classes while L is fixed. The gap is a **size-of-day contraindication**, stable on both roots (0.83 NQ, 1.00 ES). **Travel +1.9** is already unsigned — the RTH range realised from the open to the level, a within-day volatility read (D471 ρ +0.31); D668's only big-day predictor; unstable on ES (0.40). **ES's gap-through class** (+4.55 vs NQ +2.80) is ~0.6 SE, noise; the real contrast is gap-inside (ES −2.05 vs NQ +4.93, ~2.3 SE, uncorrected). On ES the classes differ in P(hold) with G flat; on NQ in G. Declare no gap-inside sign for ES/YM, positive for NQ/RTY.

**1. Ranked predictors** (C = confluence, X = contraindication):
1. **Overnight probe of the level** — Globex 18:00→09:29 traded beyond L on the break side and is back inside by 09:30 (strong form: beyond the stop). The stops were run overnight; the RTH break is a second break (D681: second break +1.17 vs +4.29; D666: re-break < plain in 8/8). X on all roots (RTY weaker). Veto (strong form), size-down. ES/NQ on disk (`fut_opening_globex_1m`); YM/RTY need a build. If ~25% flagged behave like second breaks, traded mean +1.1 bp, AUC +0.01–0.02.
2. **Overnight two-way range** (Globex range − |gap|)/ATR20 — non-directional big day. C on all roots (RTY weaker). Size-up. D647's unsigned vol_z; against: the ATR tercile is flat (E4 is ATR-normalised, so only surprises matter). +1–1.5 bp top half.
3. **|gap|/ATR unsigned + aligned dummy** (replaces signed gap): |gap| X on all roots; aligned C. Size-down. Makes the contraindication testable on YM/RTY.
4. **Range-so-far/ATR** and a **clock-normalised excess** (0.25A over the typical |move| for that clock, Zarattini–Aziz–Barbon's noise area). Size. Replaces the unstable linear clock. +0.5–1 bp.
5. **Room to the 5-day extreme.** C for clearing the 5-day extreme; no sign at 20 days (D487). Size. +0.5–1 bp.
6. **Compression** (yesterday's range/ATR20, NR4/NR7, inside day) — mild X (declared against Crabel: vol clustering says a narrow range forecasts a smaller day). Size-down, never a filter.
7. **Vol regime** (ATR20 level) — none declared; E4 normalises it away. Dollar sizing / trail width only.

Cross-lane flags: scheduled-release flags are the cleanest non-directional big-day variable on disk, and the worst break hour (10:xx) is the release hour; opening relative volume ("stocks in play") is the one conditioner the ORB literature finds robust (lane B); gamma belongs in the same size term (lane A).

**2. Drop or re-role.** Linear clock → #4's excess; signed gap → #3; travel → range-so-far (never travel/range: efficiency is inverted on ES, D471); keep the class dummies; do not add weekday, the ATR level or path efficiency.

**3. Test (#1, with #2 as the decomposition guard).** Flag Q (probe beyond L, back inside by 09:30) and Q⁺ (beyond the stop). Stage 0: P(hold | Q) − P(hold | ¬Q) within the no-gap and gap-inside classes. Primary: E4 gross (¬Q − Q), HAC t, ES/NQ development and YM/RTY evidence after the Globex build, sign declared negative on all four. Null: the flag rotated across sessions within year, 1,000 draws. Guard: the off-side probe must not lower the hold rate equally (else it is #2). Falsified if the difference is under 3 bp, within 2 SE of the null p95, or matched by the placebo. Power: ~350 flagged trades, SE ≈ 2.8 bp — only ≥ 6 bp resolves.

**4. Risks.** Multiplicity (the 472-subset scan; any change to D668 before YM/RTY must be an amendment); look-ahead (range-so-far ends at the prior bar; Globex features end at 09:29; RTY's sparse overnight bars); **the E4 size oracle has never been computed — do it first**; structure features have a losing record here (momentum, path efficiency, daily VR < 1); power (a 3 bp half-split is 1.3 SE in-sample).

Sources cited by the lane: Zarattini, Aziz & Barbon 2024 (SSRN 4824172); Zarattini & Aziz 2023 (SSRN 4416622); Zarattini, Barbon & Aziz 2024 (SSRN 4729284); Gao, Han, Li & Zhou (JFE 2018); replication repositories (QQQ ORB: 76% of P&L is 2022). Crabel's NR and Market-Profile IB claims: practitioner only, not peer-reviewed.

### Lane D — cross-market and root-specific context

#### Report

**0. The ES/NQ asymmetry.** Sized correctly: the "aligned = exhaustion on ES" cells are tiny (gap+gamma+TICK n=36, −10.1 gross, t −1.8; gap+gamma+A7 n=21, t −2.7), ES's gamma is short on 11.7% of trades. Like for like without gamma, **gap+TICK: ES +2.39 gross (n=285) vs NQ +11.7 (n=228, t 2.7)**: alignment adds ~+6 bp on NQ and ~0 on ES, not "ES exhausts". The structural asymmetry is the open class: ES's edge sits in gap-through opens (+4.55), NQ's in no-gap breaks from inside the range (+4.86, 52% of P&L). **ES is priced overnight** (the global macro instrument; an intraday break from inside the range re-prices a market that already priced its news; the edge is long-side). **NQ is priced at the cash open** (mega-caps, retail, TQQQ/SQQQ arrive at 09:30; a break from inside the range is new information; two-sided edge). TICK-NQ aligned says the leaders are moving; TICK-SP aligned says little (arb). Vol scale and cost do not explain it (per-trade SD ratio 1.31, gross ratio 3.6). "Passive ES breaks" (beta echoes of NQ) are plausible and untested.

**1. Ranked predictors.**
1. **Cross-index confirmation**: for each other index root, D × (close[t−1] − its own yesterday level on the side)/ATR; n_conf (0–3) and c_min. A complex-wide break is a re-pricing; a lone break a rotation. + on ES/YM/RTY, ~0 on NQ (it leads). Size, with n_conf = 0 a veto candidate on YM. On disk. +0.01–0.03 AUC on ES/YM/RTY. Must add within the no-gap class.
2. **Open class as the root's regime**: ES-like roots (YM) earn in gap-through, NQ-like (RTY) in no-gap. Filter by root, declared before the run.
3. **Short-side veto on ES/YM** (excess over null +0.85 short vs +3.2 long). Direction veto; cost avoidance, not edge.
4. **Weekday**: fold into open class (Monday = weekend gap); diagnostic only.
5. **Macro-calendar flags** (fomc/cpi/empsit, quad witching, month/quarter-end on disk): FOMC −, CPI/NFP ambiguous; filter or widen the trail on event days. ~8 FOMC breaks/yr: trims variance, cannot move AUC.
6. **Overnight rates move × stock-bond regime** (ZN 18:00→09:00 signed, × the 60-day ES–ZN correlation). Low rank: D494 (cross-asset → ES worth one tick).
7. **Regime dummies** (0DTE era; stock-bond correlation sign): size only.

Not available: VIX (not on disk; D487 says the quiet tercile trends most, so "high VIX = trend" is the wrong prior); mega-cap earnings dates (EDGAR, ~28 sessions/yr); Nasdaq-100 rebalances (close flow, not open).

**2. Drop or re-role.** Gamma → size/exit, one measure (SPX GEX on all four, NQ's own secondary); A7 → keep as a veto on crowded breaks (ES −4.9, NQ −3.0; stability 0.66/0.82); clock → drop (late NQ breaks pay, late ES breaks lose); TICK-SP on ES weak by construction; travel root-specific.

**3. YM and RTY.** YM: ES-like, gross ≈ +1, edge (if any) in gap-through and longs, TICK-NYSE uninformative, confirmation matters most, net negative at MYM cost. RTY: NQ-like in class (small caps re-price at the cash open), two-sided plausible, rates-sensitive (ZN), gross +2 to +4, but the trail stops more in a thinner book and M2K costs 4.3–6.1 bp → Gate 1 borderline, Gate 2 fail.

**4. Test (#1).** Breaks confirmed by ≥ 2 of the 3 other roots beyond their own yesterday level at t−1 have higher E4 gross, also within the no-gap class; confirmed − unconfirmed, HAC t, YM/RTY evidence (Holm), ES/NQ development; plus the change in β_disc t with n_conf as f10. Nulls: permutation within root × year; a placebo confirmation against the day-before-yesterday levels. Falsified if inside the permutation p95 on both evidence roots, or if it vanishes within the no-gap class.

**5. Risks.** Multiplicity (only YM/RTY are clean; RTY MDE 3.6 bp); roots are not independent (ρ 0.52); look-ahead (other roots' t−1 close; hourly h08 not h09; March-2020 opens); the drift (items 3–5 reshape drift exposure); against the lane: D494, the Reddit negative catalogue, Rapach–Strauss–Zhou. Nothing here plausibly delivers more than +0.02–0.03; lane D trims losers and sizes, it does not turn ES into NQ.

#### Addendum: non-directional big-day predictors

E4 is a long option on the day's range with a near-fixed premium; an unsigned expansion predictor is a legitimate filter/size term on every root **provided P(hold) does not fall with size** — every such variable must report P(hold) by its own quintile. Trailing-vol LEVEL is not the variable (NQ E4 by vol tercile 3.26/5.08/4.53; D487: the quiet tercile trends most); predictors must be day-specific.

Ranked: **S1, the market's own implied move** (ES/NQ options books on disk: the nearest-expiry ATM straddle at the prior close, one day, in ATR units; implied/realised secondary) — size, the natural magnitude term; YM borrows ES's, RTY a blend; daily expiries only from 2022-05 (ES)/2022-10 (NQ), earlier the Friday weekly; the strongest single size variable available. **S2, macro-release days**: CPI/NFP size up (ES/YM/RTY more than NQ), FOMC size down/skip (or hold the initial stop to 14:00). **S3, |overnight macro move|** (|ZN|, |6E|, |6J|, |GC|, |CL| 18:00→08:59 in σ; unsigned untested; must add beyond own |gap|). **S4, mega-cap earnings** (NQ only; EDGAR dates). **S5, cross-root dispersion at the open** (factor/rotation days). **S6, other roots' realised expansion at entry.** **S7, opex/quad witching/month-end** (skip opex as a declared secondary). **S8, VIX** — last; S1 replaces it.

Re-role unsigned: TICK → |z| as size; A7 → |A7| as size, sign as veto; gap → keep signed and add |gap|/ATR (with the caveat that NQ's gap-through earns least — a big gap is partly a day already spent); S3/S5 unsigned only; gamma already unsigned (unify the measure); confirmation count is a count. Filters: FOMC and monthly/quad opex skips. The trap: size predictors also raise the failed-break count on hard-reversal days (2020), so the pre-registered statistic is E4 gross by size quintile with P(hold) beside it, not |move|.

### Lane E — sizing, exits and the expected-profit design

#### Report

**The decomposition.** NQ E4: P(hold) = 0.526; hold +25.2, return −18.9; gross ≈ 44·P(hold) − 19. The loss is set by exit geometry (a constant in ATR units); the gain is the trend day's size (close exits +57.5; top 1% = 123% of net), which gamma predicts (t 4.8–12 beyond σ20) with no direction. The hold indicator has sd 0.5 (≈ 22 bp in payoff units); E4 gross sd 45.5 with skew 1.5. D668 regressed the noisy composite; half the target's variance was payoff dispersion no hold predictor can explain.

**Ranked recommendations.**
1. **Two-part (hurdle) model, roles fixed by mechanism**: projected = π̂ × [P̂(hold)·Ĝ − (1 − P̂)·L]; hold part: signed gap/ATR, TICK z, open class; size part Ĝ = ATR20 × (1 + κ·short_gamma), κ fixed a priori from D665 (~1.4 on NQ SPX GEX), never refitted; loss part L = 0.25A + the root's mean gap-through overshoot. Short-gamma NQ E4 +6.37 vs +2.98, win 45% vs 40%, 9/10 years. A binary target roughly doubles the t per unit of information.
2. **Count score with mechanism signs, not fitted OLS**: hold part = count of {gap aligned, TICK aligned}; A7 excluded (sign not stable across roots in the raw splits). Fitted OOS AUC 0.529 vs 0.531 by counting; NQ's final coefficients are ~1 SE each, which is why π̂ settled at 0.48. The information is d ≈ 0.11 sd (AUC 0.53) and fitting cannot raise it.
3. **Veto, never filter, at this AUC**: take every break; veto only projected < 1 × cost (in practice count 0: NQ 39 trades −7.8 net, ES 52 trades −12.3 — post hoc). D668's filter kept 20% of trades, cut dollars 62% ($836 → $314/yr), Sharpe 0.60 → 0.51, and the top-1% share from 123% to 38%: at AUC 0.53 a hard filter drops trend days at random.
4. **Size across time by the drawdown cushion, not across trades by the forecast** (Grossman & Zhou 1993): f* ≈ 21 × cushion; with a $2,000 trailing floor that is ≈ 1.0 MNQ at NQ 20,000. D668's 2–3 micros are 2–3× Kelly, fired where the forecast is noisiest and in the high-price years — why sized Sharpe fell 0.48 → 0.40. Rule: trade 1 MNQ only when cushion ≥ 6 × the trade's $σ. Unfiltered maxDD $2,213 at 1 MNQ would have breached a $2,000 floor once in nine years.
5. **Exits: keep E4, fit nothing.** E3 −0.48 vs E4 +4.29: only holding captures the tail. One variant, reported never gated: trail 0.375A on short-gamma sessions. E4 was one of four exits: +4.29 carries ~0.5–1 bp best-of-four optimism.
6. **Gates: mechanism per root, predictor pooled.** At R² ≈ 0.003 and n ≈ 1,000, t ≈ 1.7 even if AUC 0.55 is real; pool YM+RTY (~2,600 trades, root fixed effect) for the predictor's slope; keep Gate 1 per root; never pool coefficients across roots.

**Drop or change in D668.** OLS on E4 gross → logistic/count on hold, size from ATR and gamma with fixed κ; the 2 × cost threshold → veto at 1 × cost; 1/2/3 sizing → drop; π̂ through the origin → keep as a diagnostic (0.48 = half the forecast is noise); nine features → two in the hold part, two in the size part. **Component line on the ledger window:** 2024 is $5,038 of NQ's $7,585 (66%); on 2016–2023 the break nets $407/yr, Sharpe ≈ 0.3, failing C-a; the 2024+ NQ day session is spent (D503).

**Test.** The hold rate rises monotonically with the mechanism-signed count (gap aligned, TICK aligned; weights 1) on YM and RTY: pooled slope of the hold indicator on the count, root fixed effect, one-sided HAC t ≥ 2; nulls: N2 permutation, N1, and a content-free arm with random fixed signs that must fail. Prediction: RTY shows it, YM does not.

**Risks.** Multiplicity already spent on NQ; AUC 0.60 is not reachable from known variables (0.60 needs d ≈ 0.36 sd, 3.4× the current separation) — lane E can stop the model destroying the edge, new information must come from lanes A–D; the size-only ceiling (D661 §2: 34% vault power); look-ahead (hold label on earlier sessions only; the cushion rule is path-dependent — declare a start date); the count is root-fragile (ES count-4 −9.75); NQ's own book and SPX GEX agree on the short regime 69%; one micro is now the prop barrier.

Sources cited: Grossman & Zhou 1993 (Mathematical Finance; Klass & Nowicki 2005 on discrete time); Zarattini, Aziz & Barbon 2024 (SSRN, not peer-reviewed); meta-labelling (Meyer, Barziy & Joubert, Journal of Financial Data Science; López de Prado 2018).

#### Addendum A: the unsigned size-of-day model (supersedes recommendation 1's emphasis on the hold part)

E4 is a long straddle on the day's size with the break choosing the leg: loss capped (≈ 19 bp on NQ), gain open. At P(hold) 0.526 break-even G = 17 bp; G ≈ 25 gives the observed +4.3; if G moves with predicted size as D665's quintiles suggest (21 → 50 bp), the bottom half of days sits near −1 gross and the top half near +9, with no directional information. A size filter is aligned with the tail: it keeps the trend days instead of dropping them at random.

**The model.** Target on every session (~2,300 per root): ln(R), R = RTH (high − low)/ATR20; secondary |close − open|/ATR20. Walk-forward OLS, 250-session burn-in, pooled across the four roots with root intercepts; coefficients sign-constrained to mechanism priors (all +): |gap|/ATR, continuous dealer gamma (−GEX/DV20), |TICK z| at 09:45, 5-day realised vol/ATR20, a scheduled-macro dummy (FOMC/CPI/NFP), and the clock as a FIXED √(minutes left) prior. Converting to the trade: G_i = g × R̂_i × A_i, g the through-origin slope of realised gain-if-hold on R̂·A over earlier break trades (the only place trade P&L enters). Projected = p_r·G − (1 − p_r)·L_r − cost. Veto below 1 × cost; 1 micro; on a multi-root day the contract goes to the root with the largest projected value; one reported trail variant (0.375A in R̂'s top tercile). Why estimable: ln(range/ATR) sd ≈ 0.4 on a mean near 1 vs E4 gross sd 45 on 4; a feature explaining 5% of ln-R variance gives t ≈ √(2,300 × 0.05) ≈ 11 — D665's t 8–12 — where the same information in the trade regression reads t ≈ 1.7.

**Validation independent of P&L, in order:** (i) OOS Spearman(R̂, R) against a time-rotation null (gamma alone ≈ 0.10–0.15); (ii) decile calibration; (iii) a clock-only arm that must fail; (iv) P(hold) by R̂ decile must be FLAT (a rising hold rate is a directional leak); (v) only then E4 gross by R̂ decile. Freeze the form on ES/NQ sessions, run YM/RTY blind.

**D668's features unsigned:** open class keep; gap → |gap|/ATR in the size model (signed only in the trade score); gamma continuous; A7 → |A7| z, low weight; TICK → |TICK z|; travel → the 09:30 → entry range/ATR; clock → the √(time-left) prior; side out of the size model.

**Revised top test:** R̂ (frozen on ES/NQ sessions) orders E4 gross on YM and RTY while leaving P(hold) flat: pooled HAC slope, root fixed effect, t ≥ 2 and above the rotation-null p95 by 2 SE; the hold-rate slope inside its null; the clock-only arm fails. Expected: top tercile ≈ +10 gross, bottom ≈ 0 on an NQ-like root.

#### Addendum B: contraindications

Two layers, roles apart. (1) In the unsigned size model a contraindication is the low end of a size variable (long gamma damps the day). (2) The trade-level score S = Σ s_j·x_j over alignment dummies, s_j ∈ {−1, +1} fixed a priori; veto when S ≤ −1 or projected < 1 × cost; otherwise 1 micro; no fitted weights. Declared vector, the same sign on all four roots (no mechanism below is root-specific): gap aligned +1 (NQ +5.31 vs +1.82, ES +2.12 vs −1.13); TICK aligned +1 (ES marginal contrary, disclosed); **A7 aligned −1** (spent flow; conditional coefficient negative on both roots, −4.90 ES, −2.97 NQ, but ES's raw split goes the other way; stability 0.82/0.66 — the least stable declared sign); **aligned gap in its trailing top quintile −1** (gap exhaustion; −1.91 ES, −2.10 NQ, stability 1.0/0.83). Not declared: travel, open class, clock, side.

Guards against post hoc sign choice: (1) signs written from mechanism before YM/RTY, with the ES/NQ numbers printed as "seen" and contradictions marked; (2) the 16-vector sign family reported with the declared vector's rank against the family-max null (own-null pass but family-max fail → PROVISIONAL); (3) a sign-randomised arm that must fail; (4) stability ≥ 0.8 as a gate — below it the term is removed, not re-signed; (5) an evidence root with the opposite sign at |t| > 1.5 removes the term; (6) one primary statistic on S (pooled slope of E4 gross on S), no per-term gates; (7) S scored beside the size model, never merged — if S adds nothing beyond R̂, the break plus a size-of-day model is the construction. Expected: the S ≤ −1 veto removes 5–10% of trades at a strongly negative mean on an NQ-like root; +0.3 to +0.8 bp; a protection layer, not the edge.
