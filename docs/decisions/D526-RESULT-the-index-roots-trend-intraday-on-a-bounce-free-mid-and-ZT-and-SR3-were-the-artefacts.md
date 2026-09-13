# D526 RESULT — **the index roots DO trend intraday, and it is not bounce.** ZT and SR3 were the artefacts; the rates complex mean-reverts for real

**Runner `scripts/d526_mid_vs_trade_scaling.py`** (`--self-test` passes, 18 checks; decode 24.4 min,
build 1 min, run 2 min). Artefact
[`data/d526_mid_vs_trade.json`](../../data/d526_mid_vs_trade.json), fixture
`data/fixtures/fut_day5m_mid.parquet`.
**26 roots, 2025-09-11 → 2026-09-09, ~245 sessions a root. No return is read as P&L, no cost, no
position. Nothing admitted (R15).**

**This record is a MEASUREMENT ON THE INSTRUMENT, not a pre-registered study.** It exists because
D523's label was voided and D525 retired, both because the statistic ran on **trade closes** which
carry bid-ask bounce. The principal's instruction was to measure on the bounce-free mid first.

## 0. The design — paired, which is the whole point

Same sessions, same roots, same statistic, **two price series**: the **trade close** from
`fut_day5m` (carries bounce) and the **quoted mid** `(bid+ask)/2` from `bbo-1m` (nobody trades at
it, so it carries none). **The bounce contribution is therefore a within-session difference**, far
more precise than any comparison across periods or roots.

Statistic: `log Σ|r_k|` regressed on `log k`, `k ∈ {3,4,6,8,9,12,18,24}`, `N = 72` returns,
vol-standardised. **Slope = Hu − 1.** Simulated benchmark (fGn at Hu = 0.50, seed 526, same window
and scales) = **−0.5521**, i.e. an implied Hu of 0.4479; the closed form would say −0.5000, so the
finite-window bias is **−0.0468** and the benchmark is simulated rather than assumed. **A POSITIVE
deviation means MORE persistent than a random walk measured identically.**

## 1. The instrument works — the check this record rests on

Bid-ask bounce is an MA(−1) in the trade price, so it shows in the lag-1 autocorrelation and
nowhere else so cleanly. **The mid roughly halves it on the rates complex and finds nothing to
remove on the index roots:**

| | ZB | ZN | ZT | UB | SR3 | | ES | NQ | RTY |
|---|---:|---:|---:|---:|---:|---|---:|---:|---:|
| lag-1, trade | −0.1128 | −0.1231 | −0.1122 | −0.0959 | −0.2350 | | −0.0290 | −0.0304 | −0.0060 |
| lag-1, mid | −0.0608 | −0.0609 | −0.0577 | −0.0620 | −0.1545 | | −0.0270 | −0.0286 | −0.0154 |

**The bounce was concentrated exactly where the tick is coarse relative to the move, and the index
roots never had any to lose.**

## 2. THE HEADLINE — the index roots are persistent, and the mid CONFIRMS it

| root | sessions | mid deviation | SE | t | implied Hu | bias-corrected Hu | share of the deviation that was bounce |
|---|---:|---:|---:|---:|---:|---:|---:|
| **ES** | 244 | **+0.0463** | 0.0122 | **+3.78** | 0.494 | **0.539** | −13% |
| **NQ** | 245 | **+0.0354** | 0.0118 | **+2.99** | 0.483 | **0.528** | +4% |
| **RTY** | 247 | +0.0266 | 0.0136 | +1.96 | 0.475 | 0.520 | +18% |
| HO | 238 | +0.0244 | 0.0130 | +1.88 | 0.472 | 0.517 | +16% |
| **YM** | 247 | +0.0177 | 0.0129 | +1.37 | 0.466 | 0.511 | +24% |
| … | | | | | | | |
| ZF | 244 | −0.0201 | 0.0141 | −1.42 | 0.428 | 0.473 | +10% |
| UB | 242 | −0.0267 | 0.0143 | −1.87 | 0.421 | 0.466 | −2% |
| TN | 242 | −0.0327 | 0.0147 | −2.22 | 0.415 | 0.460 | −29% |
| **ZB** | 243 | **−0.0362** | 0.0154 | **−2.35** | 0.412 | 0.457 | −6% |

**Pooled over the four index roots: +0.0315, and WITH the measured cross-root clustering
(ρ = 0.510, so `n_eff` = 387 of 980 root-sessions) that is t = +3.10.** The index-vs-non-index
contrast is **+0.0373 at t = +5.35**.

**The bias correction** adds ~0.045 to every implied Hu, because the estimator reads 0.4479 on a
simulated random walk at this window. The *deviation* column needs no correction and is the primary
quantity.

## 3. And it replicates across eras AND price series — 10 of 10 signs agree

The same estimator on the **already-spent** 2011–2023 trade closes, against the 2025–26 mid:

| root | 2011–2023 (trade) | 2025–26 (mid) | agree |
|---|---:|---:|---|
| ES | +0.0075 (+2.0 SE) | +0.0463 | ✔ |
| NQ | +0.0088 (+2.3 SE) | +0.0354 | ✔ |
| YM | +0.0057 (+1.5 SE) | +0.0177 | ✔ |
| RTY | +0.0142 (+2.9 SE) | +0.0266 | ✔ |
| HO | +0.0023 (+0.5 SE) | +0.0244 | ✔ |
| GC | −0.0217 (−6.2 SE) | −0.0195 | ✔ |
| ZB | −0.0051 (−1.5 SE) | −0.0362 | ✔ |
| ZN | −0.0128 (−3.6 SE) | −0.0175 | ✔ |
| ZT | −0.0163 (−4.0 SE) | −0.0028 | ✔ |
| 6E | −0.0216 (−6.1 SE) | −0.0163 | ✔ |

**Ten of ten, across a 12-year gap and two different price series.** But **the MAGNITUDES differ by
about 4× on the index roots** (ES +0.0075 → +0.0463). That is either a regime or one year of noise,
and one year cannot settle it. **The sign is the finding; the size is not.**

## 4. ZT and SR3 were artefacts, exactly as the D523 amendment predicted — and the rest were not

The discriminating group is the coarse-tick rates, where both hypotheses predict a negative sign, so
**only the bounce share separates them**:

| root | trade dev | mid dev | bounce share |
|---|---:|---:|---:|
| **SR3** | −0.0523 | **+0.0155** | **+130% — SIGN FLIPS** |
| **ZT** | −0.0239 | **−0.0028** | **+88% — now at the benchmark** |
| ZN | −0.0297 | −0.0175 | +41% |
| ZF | −0.0222 | −0.0201 | +10% |
| UB | −0.0261 | −0.0267 | −2% |
| ZB | −0.0341 | −0.0362 | −6% |
| TN | −0.0255 | −0.0327 | −29% |

**5 of 7 keep a deviation below −0.015 on the mid.** So the rates complex genuinely mean-reverts
intraday; **only ZT and SR3 — the two I named in D523 §7.3 — were bounce.** That amendment's
mechanism is confirmed on the two cases it identified and refuted as a general explanation.

## 5. What is NOT settled: tick fineness and asset class are collinear

**H-TICK is wounded but not dead.** The Spearman of deviation against `log(median 5-minute move in
ticks)` across 26 roots:

    on the TRADE close  +0.7025
    on the QUOTED MID   +0.5935

**It falls, but only from 0.70 to 0.59.** Tick fineness still orders the cross-section on a
bounce-free price — and **the four index roots ARE the four finest-tick roots**, so with 26 roots
the two explanations cannot be separated. What the mid establishes is that the *ordering is not
manufactured by bounce*; what it does not establish is *why* index roots sit at the persistent end.

**So the honest split:**

- **CONFIRMED.** Index equity futures show intraday path persistence on a bounce-free mid, at
  t = +3.10 pooled with clustering, replicating in sign over a 12-year gap. **The principal's
  assertion that trending markets exist is upheld, and my voided D523 headline was wrong.**
- **CONFIRMED.** The rates complex is genuinely anti-persistent intraday, ZT and SR3 excepted.
- **OPEN.** Whether the cross-section is asset class or tick fineness. It needs roots that break the
  collinearity — a fine-tick non-index root or a coarse-tick index root with real participation, and
  NKD does not qualify (3,301 contracts a session against ES's 1,205,239).
- **OPEN AND MORE IMPORTANT.** Nothing here is a per-session state. A bias-corrected Hu of 0.539 on
  ES is a *population* parameter over 244 sessions; D525 §11.4 measured the one-session `t` at
  **+0.24**. **A tradeable construction needs a per-session read this statistic cannot give.**

## 6. Defects found in this record's own instruments

1. **I claimed the path-length estimator was selection-free. The self-test refuted it.** `Σ|r_k|`
   is zero if every `k`-block sums to zero, as a perfectly alternating path does at `k = 2`.
   Fixed by dropping the affected **scale** rather than the session, with the masked OLS asserted
   equal to a plain OLS to **9.55e-15** where nothing is missing, and a session lost only if fewer
   than 3 scales survive. The docstring now says *rarer by orders of magnitude*, not *never*.
2. **A self-test assertion of mine was too strong** — I claimed the closed-form bias exceeds the
   whole 0.50→0.55 effect; measured, it is −0.0400 against +0.0426, so *comparable to*, not larger.
   Restated as "at least half the effect, so it is unusable".
3. **A check that could not fail**: I had compared `path_slope` to itself. Replaced with a plain-OLS
   reference.
4. **The bounce-share column is meaningless where the trade deviation is near zero** — it printed
   −2332% for 6A. Suppressed below |trade dev| = 0.010 rather than published.

## 7. The holdout accounting, stated plainly

`bbo-1m` exists **only** for 2025-09-11 → 2026-09-11, which is inside the slice D525 §6 reserved,
and **this record spends it.** Accepted because §6 itself measured that slice at **48% power** for
the close-price confirmation it was held for, because this is a **validity check on the instrument**
rather than a test of an edge, and because the quoted data exists nowhere else. The 2011–2023 closes
used in §3 were already spent by D525's design check and are re-read only as an era comparison, not
as confirmation.

**No slice remains unread for this line.** Any future confirmation needs new data — which arrives
with time — or a construction pre-registered against a forward window.

Nothing enters `FINDINGS.md`, `RULES.md`, `COMPONENTS_PROP.md` or either book on this record
(R8, R15).
