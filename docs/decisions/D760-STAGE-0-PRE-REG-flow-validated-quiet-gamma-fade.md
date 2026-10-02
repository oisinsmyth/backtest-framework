# D760 STAGE 0 PRE-REGISTRATION — the absorbed fade on quiet long-gamma days: arm the fade on strong long-gamma days without a 10:30 impulse, and enter only when aggressive flow in the morning's direction fails to move the price (ES, NQ, YM; one micro)

*2026-10-02. Prop book.*
- *The principal: "Arm a reversal style trade for Quiet long-gamma days then Require a Volume spike to validate the
  reversal. Or a order flow?". They then chose order flow, with YM's flow built too.*
- *Numbered D760, claimed with the documentation-review session.*
- ***Committed alone, before the YM fixture's builder and the runner exist.** In-sample only (≤ 2023-12-29).*

## 0. What is seen, what this record spends, and why

**Seen.**
- **D757 (post hoc):** strong long-gamma days without a 10:30 impulse (G ∧ ¬I) revert more often than the base: 0.375
  on ES, 0.378 on NQ and 0.404 on YM, against 0.333.
- **D759: NO ROOM.** The unconditional 10:30 fade on non-impulse days needs a precision of 0.451.
- **D715 / D717 (the nearest flow evidence):**
  - On ES, a morning move made with less aggressive flow than its size predicts reversed by the close, and one made
    with more continued (Spearman −0.061, inverted against D715's mechanism).
  - On NQ, the same residual ranked nothing (−0.007). D717 judged ES's result most likely noise.
- **Volume** has been a size detector, not a direction one, in every test on file (D720, D724, D725, D730, D434). It
  is not tested here.

**What this record spends: the fade's net on G ∧ ¬I days in-sample.** D759 deliberately left it uncomputed, for a
held-slice read. **That read has no power.** The held slice (2024-01 → 2025-02) holds about 225 G ∧ ¬I days across
ES, YM and RTY. Any triggered subset is about 100 trades, at a per-trade sd near $90, so the standard error is about
$9. An edge would have to be about +$17 a trade to show, on days whose reverting outcome pays about +$24.

**The in-sample G ∧ ¬I days (about 1,560 on ES, NQ and YM) are therefore the test set.** Their P&L is unseen, and the
trigger below is fixed before any of it is read. A PASS here is not admission: confirmation could come only from
the forward recorder (ES, NQ and YM bars since 2026-09-21), over months.

## 1. The mechanism, and the sign it commits to

**The story.**
- On a strong long-gamma day, dealers hedge against the move: they sell rallies and buy dips, mostly passively.
- A push in the morning's direction then meets resting liquidity. **Takers lift offers (or hit bids) hard and the
  price does not progress. That is absorption.**
- Absorption at a time when the market is already leaning toward reversion (G ∧ ¬I) is the validation. The trade
  fades the morning.

**The sign is fixed now.** The trigger is aggressive flow **in the morning's direction** with no price progress. The
opposite reading, flow turning in the fade's direction, is not tested; under this story it is the dealers' hedge,
which is passive, and it would not show as aggressive flow.

**What it predicts that chance does not:**
- the fade entered on an absorption window earns, net;
- it earns more than the same days' fade entered on a window chosen by flow from another day (the rotation);
- it earns more than arming alone (the 10:30 fade on the same days).

## 2. Data

| input | file | columns |
|---|---|---|
| bars | `fut_{ES,NQ,YM}_rth_1m.csv.gz` (D462), through D727's `load_root` and D756's `load_root_panel` | day, hhmm, contract, open, high, low, close |
| flow, ES and NQ | `fut_ES_signed_1m.csv.gz` (D695), `fut_NQ_signed_1m.csv.gz` (D717) | day, hhmm, contract, volume, buy, sell |
| flow, YM (new) | `fut_YM_signed_1m.csv.gz`, built for this record (§2a) | the same |
| G, I | D757's `gamma_cells` (GEX at the prior close, walk-forward top tercile) and I = \|z₁₀:₃₀\| ≥ 1.5 | read-only |
| costs | `data/futures_costs.json`, each micro's `default_line` (MES $4.418, MNQ $4.067, MYM $3.797) | |
| ledger | `data/d748_component_books.csv` (F2, C1, D737) | for ρ only |

**Every read is cut at day < 2024-01-01, and the cut is asserted.** SqueezeMetrics' GEX is read as D756 reads it
(the last date strictly before t), and is never tracked.

### 2a. The YM fixture (validation declared now, before the builder exists)

- **Builder:** `scripts/build_fut_ym_signed_1m.py`. It reuses D695's record layout, session slice, minute convention
  and cutoff unchanged. The one difference is the file suffix: Sierra holds YM as `YM{H,M,U,Z}{16..24}-CBOT.scid`.
- **Source:** each session's front contract from `fut_index_sessions` (root YM), 09:30–16:00 ET only, sessions
  2016-01-04 → 2023-12-29.
- **Validation** against `fut_YM_rth_1m`, per minute:
  - V1: the median volume ratio lies in [0.98, 1.02];
  - V2: the volume correlation is ≥ 0.98;
  - V3: the signed share is ≥ 0.99;
  - V4: the last trade equals the bar's close on ≥ 95% of minutes (one YM tick is 1.0 point).
- **If YM fails any gate,** YM is dropped and the record runs on ES and NQ, saying so. No gate is relaxed.

## 3. The construction (fixed now)

**Armed days, per root (ES, NQ, YM):**
- D757's G = 1 and ¬I;
- P₁₀:₃₀ ≠ O. The morning direction is d = sign(P₁₀:₃₀ − O), and the fade side is s = −d. P₁₀:₃₀ and O are D756's:
  the close of the 10:29 bar and the session open.

**Windows.** Seven 30-minute windows close at t ∈ {11:00, 11:30, 12:00, 12:30, 13:00, 13:30, 14:00}. Window w covers
the bars starting t−30 … t−1.
- **The flow imbalance:** f_w = (Σbuy − Σsell) / Σvolume over the window's signed minutes.
- **Coverage:** a window is usable only if at least 25 of its 30 minutes have flow rows for the same contract as the
  bars. An unusable window cannot fire.
- **The price move:** Δ_w = P_t − P_{t−30}, with P_t the close of the bar starting t−1 (D727's convention).

**The threshold.** θ_r,t is the 67th percentile of \|f\| over every usable window (all seven clocks) of **every**
session of root r (not only armed days) among the previous 250 sessions, strictly prior.
- Until 250 prior sessions exist, nothing trades (the burn-in).

**The absorption trigger.** Window w fires on an armed day when both hold:
- **A1 aggressive in the morning's direction:** d · f_w ≥ θ;
- **A2 no progress:** d · Δ_w ≤ 0.

The **first** firing window sets the entry.

**The trade:**
- side s;
- entry at P_t of the first firing window, i.e. the close of the bar starting t−1 (D756's decision-price convention,
  kept for comparability with D759);
- exit at the close of the 15:59 bar;
- one micro; gross = s × (exit − entry) × $ per point, net = gross − the default-line cost;
- no stop, no target;
- a day with no firing window does not trade.

**The books (pooled over ES, NQ and YM, one micro each; NQ is a decision root here because it has flow):**

| book | takes |
|---|---|
| **V, the primary** | armed days with an absorption window, entered at the first one |
| A0, arming alone | every armed day, the 10:30 fade (D759's trade, on G ∧ ¬I days) |
| P0, price only | armed days, entered at the first window with d · Δ_w ≤ 0 (A2 without A1) |

## 4. The gates (fixed now)

| gate | what | passes when |
|---|---|---|
| **T** trades | V | at least 150 trades pooled, otherwise the reading is NO TEST |
| **G1 edge** | V | the mean net > 0 with a day-clustered t ≥ 2.0 (one row per session, summing the roots), AND the median net ≥ 0 |
| **G2 the flow carries it** | V | V's efficiency Σgross / Σ\|gross\| is above the p95 of the **exact enumerated rotation** of the flow (each root's window-flow panel f, with its coverage, shifted by a shared offset k = 1 … n_min − 1 across that root's armed days, mod each root's count; prices, d, Δ and θ fixed) |
| **G3 more than arming** | V against A0 | V's mean net > A0's mean net (point estimates) |
| **G4 not one episode** | V | net > 0 without 2020 and without 2022; no calendar year carries > 50% of the dollar net; net > 0 in at least half the years with ≥ 10 trades |
| **G5 across roots** | V | mean net > 0 on at least 2 of the 3 roots |

**Readings:**

| reading | when | what follows |
|---|---|---|
| **PASS** | T, G1–G5 | forward recording only, on the principal's word. No held-slice read (§0) and no ledger admission |
| **FLOW ONLY** | G2 holds, G1 fails | absorption carries information but not the micro fee |
| **NOTHING** | G2 fails | the flow trigger adds nothing over its own rotation |
| **FAIL** | otherwise | |

**On any reading but PASS, I will recommend closing the reverting-day line (D756, D757, D759, D760).** That is the
principal's call.

**Reported, never gating:**
- the four groups for V, A0 and P0 at one micro: Sharpe and Sortino, net and gross, break-even cost, trade
  distribution with the symmetric trims, by year, top trades named;
- the rotation's p50 and p95 (exact, SE 0);
- per root;
- the entry-clock distribution;
- P(RD | V's days) beside q (does validation lift the reverting rate?);
- long against short;
- the next-bar-open entry as a sensitivity;
- **the component line:** daily net Sharpe and Sortino at one micro, hit rate, skew, and ρ with F2, C1 and D737
  from `data/d748_component_books.csv`.

## 5. Size the prize and the power (stated now)

- **The prize.** D759's fade earns +$23.68 on a reverting non-impulse day and loses $19.48 on the others. Entries
  after 10:30 leave less of the day to collect.
- **Trades.** A1 and A2 pull against each other (aggressive flow usually moves the price), so I expect a window to
  fire on 3–6% of usable windows. Over seven windows, that is roughly 20–35% of armed days. After the burn-in, about
  1,300 armed days remain, giving **about 250–450 V trades.**
- **Power.** With a per-trade sd near $80, the standard error is about $4–5. G1 detects a mean net of about +$9–10 a
  trade, roughly 40% of the reverting-day prize.
- **G2** ranks efficiency against about 450 exact offsets. It is decisive only if the flow moves V's efficiency by
  several points.

## 6. The runner's assertions (each proved to raise in `--selftest`)

1. **The known answer:** D757's G ∧ ¬I counts per root (ES 542, NQ 508, YM 510) and its RD rates, reproduced exactly.
2. **Lag audit, a second implementation:** for 40 sampled armed days, a plain loop over the raw fixture rows
   re-derives f_w, Δ_w, θ (strictly prior), the first firing window and the entry price, never calling the vectorised
   code. **Break:** a θ that includes the current session must raise.
3. **Sign audit in money:** a favourable move pays long and short positively; net = gross − cost.
4. **Right quantity:**
   - every entry is at or after 11:00, and every window lies wholly after 10:29;
   - the flow window's contract equals the bars' contract;
   - the rotation's offset 0 equals the observed statistic;
   - A0 on D756's panel reproduces D756's fade exactly on the armed days.
5. **The seal:** a 2024-dated row injected into any input raises.
6. **A synthetic check:** a planted absorption-then-reversal effect passes G1 and G2, and pure noise fails G2 about
   95% of the time.

**Speed.** The work is small: three roots, about 1,560 armed days, and seven windows. The rotation is about 450
offsets of a vectorised trigger. The projected wall time is under 2 minutes, so it runs as written.

**Output:** `data/stage0_d760_absorbed_fade.json`. The YM fixture goes to the data root's fixtures (gitignored,
hashed in its meta).

## 7. Predictions (Opus)

- **P1: NOTHING** (P 0.6). Aggressive flow on index futures has carried no direction on any clock tested (D695, D715,
  D717). I do not expect long gamma to change that.
- **P2: A0** (the 10:30 fade on the armed days, now read in-sample) **nets between −$8 and +$2 a trade** (P 0.7).
  q = 0.39 sits below D759's p* = 0.45, but p* on G days may be lower than on all non-impulse days.
- **P3:** V has between 250 and 450 trades (P 0.6).
- **P(PASS) ≈ 0.07.**
