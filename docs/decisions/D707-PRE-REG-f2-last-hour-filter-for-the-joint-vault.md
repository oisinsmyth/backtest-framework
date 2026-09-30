# D707 PRE-REGISTRATION — F2 for the joint vault run: the ES last-hour continuation, taken only when the prior hour's relative size and today's realised volatility rank in the top fifth together. The principal's candidate, with the construction recorded in full

*2026-09-30.*
- *The principal, after [D705](D705-RESULT-none-passes-f2-fails-only-on-2022-concentration.md): "The F2 construction
  is now a candidate, add it to the big vault run. Then summarise and record the construction in its entirety."*
- *Numbered D707: D706 is the highest on every branch and in every commit subject. The other session confirmed 707
  is free before this was written.*
- ***Committed alone, before its runner exists.** Nothing in this record reads a price dated 2024-01-01 or later.*

**What this record does.**
- It registers F2 as one family for the **joint vault run** (AITODO's programme rule, A10), scored on data F2 has
  never seen.
- It writes the construction down completely (§1), so the vault run and any later forward book trade exactly this
  object.
- The runner is built next. It reproduces D705's F2 in-sample exactly, computes the power, and freezes the rule
  (`scripts/freeze.py`'s hashes, as D680).

## 0. The principal's ruling, and what it overrides

**D705's verdict stands as written: DEVELOPMENT FAIL.** F2 passed gates (a), (b) and (c) and failed (d), because 2022
holds 59.9 % of its net against a 50 % bar.

**The principal has made F2 a candidate anyway.** That is an override of a pre-registered development gate. It is
recorded here as the principal's decision, not as a pass:
- **The (d) bar is not moved.** D705's verdict and its gate are unchanged.
- **What the override buys** is one look at unseen data, under D705 §3's confirmation rule, which was frozen before
  D705 ran.
- **Why that is not a loosened test:** the question (d) asked, whether the edge is one year, is exactly what unseen
  data answers. The unseen data contains no 2022.

**The selection path, disclosed in full,** because the confirmation look is priced against all of it:

| step | record | what was chosen |
|---|---|---|
| 1 | D618 | the last-hour continuation itself (ES, sign of 14:30 → 15:30 held to 16:00) |
| 2 | D702 | the hindsight oracle profile. The edge is big-move-shaped, and the relative size signal is the one that ranks |
| 3 | D703 | a dollar expected-profit filter; failed (a regime gate: 79 % of trades in 2022) |
| 4 | D705 | three relative filters, best-of-three null; F2 the strongest, failed (d) |
| 5 | this record | F2 carried to unseen data on the principal's word |

- **Only step 4's choice among three is priced by a null.** Steps 2, 3 and 5 are not.
- **So the in-sample +$13.21 is an upper estimate.** §5's power is stated at 100 %, 50 % and 25 % of it.

## 1. The construction, in its entirety

### 1.1 The instrument and the data

| item | value |
|---|---|
| instrument | **ES** (the E-mini S&P 500 future), traded as **one MES** (the micro, $5 a point) |
| price data | `data/fixtures/fut_ES_rth_1m.csv.gz`: one-minute RTH bars, `day`, `hhmm` (bar START, ET), `open`, `close`, `contract` |
| session | a trading day with **at least 380 one-minute bars** (D618's `MIN_BARS`). Half days fall out |
| the contract | each session's modal `contract` |
| roll session | a session whose contract differs from the previous session's. **Never traded** |
| price at hh:mm | the **close of the bar that STARTS one minute earlier** (D462's convention): P15:30 = close of the 15:29 bar |
| the open | P09:30 = the **open** of the 09:30 bar |

### 1.2 The signal and the trade

| item | definition |
|---|---|
| **F5**, the prior hour's move | F5 = 10⁴ · ln(P15:30 / P14:30), in bp |
| **direction** | d = sign(F5). **A session with F5 = 0 is not a candidate** (a zero signal pays no fee) |
| **entry** | at 15:30 ET, in direction d, at P15:30 |
| **exit** | at 16:00 ET, at P16:00 (the close of the 15:59 bar). No stop, no target, flat every day |
| **size** | one MES |
| **gross** | d · (P16:00 − P15:30) · $5 |
| **cost** | **$4.42 a round trip** (D668-A2's MES line: $3 commission plus the measured crossing, counted once) |
| **net** | gross − $4.42 |

**The candidates** are the sessions of §1.1 that are not roll sessions, have finite P14:30, P15:30 and P16:00, and
have F5 ≠ 0. The trade is D618 §3c's continuation, unchanged.

### 1.3 The two inputs, each known at 15:30

**a, the prior hour's RELATIVE size:** a = |F5| / σ_F5.
- σ_F5 is the standard deviation of F5 over the **previous 252 sessions** of §1.1's frame (at least 60), **shifted one
  session**, so it never includes today.
- That frame includes roll sessions and sessions with F5 = 0: σ is a property of the market's hour, not of the traded
  set.

**b, today's realised volatility:** b = ln √(Σ r²).
- The r are the **5-minute** log returns in bp from P09:30 to P15:30, on the grid 09:35, 09:40, …, 15:30. Each grid
  price uses §1.1's convention, so the last bar read is the one that starts at 15:29.
- Missing prices contribute nothing (`nansum`).
- A session whose sum is zero gives b = −∞, which is not finite and so is skipped by the tiers.

### 1.4 The walk-forward percentiles and the rule

**`tiers(x)`** (D671's function, unchanged):
- for each candidate, the share of the **previous 250 finite values** of x, **in candidate order and strictly
  earlier**, that are **strictly below** it;
- NaN until 250 earlier finite values exist.

**The rule:**

| step | quantity |
|---|---|
| 1 | tₐ = tiers(a), t_b = tiers(b), each over every candidate since 2016-01-04 |
| 2 | c = (tₐ + t_b) / 2, the composite (D672's construction) |
| 3 | t_c = tiers(c) |
| 4 | **TAKE the trade when t_c ≥ 0.8** (the top fifth of the composite) |

- **The walk-forward runs continuously** from 2016-01-04 across the in-sample / unseen boundary. Every tier on an
  unseen session uses only earlier candidates, some of them in-sample. Nothing is refitted: the rule has no fitted
  parameter.
- **Where it trades:** about 20 % of candidates, **about 45 trades a year**.

**What F2 does not use:** dealer gamma, implied volatility, the calendar, the side, or any dollar threshold. D705's
window also required G_SUM to be finite, because F3 needed it. F2's decision does not depend on G_SUM.

### 1.5 In-sample, as scored by D705

*D705's window: 2018-05-14 → 2023-12-29, 1,359 candidates, walk-forward.*

**Performance:**

| | F2 | take everything |
|---|---:|---:|
| trades (a year) | 252 (45) | 1,359 (242) |
| mean gross / net | +$17.63 / **+$13.21** | +$4.10 / −$0.32 |
| net HAC t (NW, 5 lags) | **2.48** | −0.21 |
| hit (net) / median net / payoff | 0.536 / +$6.21 / 1.33 | 0.464 / −$3.17 / 1.14 |
| skew / excess kurtosis | +0.81 / 7.4 | +0.97 / 14.2 |
| Sharpe (Sortino), per trade, net | 0.93 (1.59); gross 1.24 | −0.08 (−0.13) |
| Sharpe (Sortino), daily, net | **0.80 (1.37)** | −0.07 (−0.11) |
| max drawdown | $707 | $1,926 |

**Dependence:**

| | F2 |
|---|---|
| long / short net | +$17.04 / +$8.85 |
| before / after 2022-05-16 | +$14.47 / +$7.06 |
| without 2022 | +$7.17 on 186 trades |
| by year (n, net a trade) | 2018 18, +13.36 · 2019 21, −2.28 · 2020 65, +4.83 · 2021 49, +16.12 · **2022 66, +30.22** · 2023 33, +1.15 |
| 1 % trims: ex-top / ex-bottom / both | +$9.56 / +$16.16 / +$12.50 |
| ρ with the MACD arm (daily) | +0.02 |

**Nulls:**
- The best-of-three count-matched rotation had p50 +$1.44 and **p95 +$7.94**. F2's rank was 0.996, with an exact p95
  (SE 0).
- Holm p was 0.020 across three members.

## 2. The unseen data

**One look, in the joint run:** every candidate from **2024-01-01 through 2026-09-18**.

| part | span | status for this trade |
|---|---|---|
| the held slice | 2024-01-01 → 2025-02-28 | **unread for this trade.** D618 reserved it, and D702, D703 and D705 held it. Other ES constructions read these bars; none of them selected F2 |
| the vault | 2025-03-01 → 2026-09-18 | sealed; read only in the joint run (A10) |

- **The fixture ends 2026-09-09.** The last seven vault sessions are missing, and the runner counts them. Session
  dates were listed to learn this; no price was read.
- **Both parts are read together, once.** The held slice is not read first on its own: one look, one verdict.
  Scoring it separately first would be a second look at the same data.
- **Expected:** about 2.7 years, about 640 candidates and **about 120 F2 trades.**

## 3. The test (D705 §3's rule, frozen before D705 ran; only the data is extended)

**On the F2 trades in §2's span:**

| verdict | condition |
|---|---|
| **PASS** (D705's CONFIRM) | at least 30 trades, **mean net > 0 and one-sided HAC t ≥ 1.2816** (Newey–West, 5 lags; D691's `nw_t`) |
| **FAIL** | at least 30 trades, otherwise |
| **UNRESOLVED** | fewer than 30 trades |

- **Programme promotion** is flagged separately at p ≤ 0.005 (t ≥ 2.576), the family's α slot.
- **The slot:** the lowest free one, **7** (released 2026-09-29 from the opening model's H-O2; a different family).
  It is registered at freeze time. Slot 10 stays free.
- **Nothing else gates.** In particular, D705's (d) is not re-applied as a gate here (§4 reports it).

## 4. Reported beside the verdict, never gating

- **The two parts separately:** the held slice and the vault, each with its count, mean net and t.
- **All four reporting groups** at one MES, net and gross side by side:
  - Sharpe with Sortino, per trade (annualised by F2's own count) and daily;
  - max drawdown; hit, median and payoff; skew and kurtosis; the 1 % trims (ex-top, ex-bottom, both);
  - by year; long against short.
- **D705's (d) on the unseen span:** the largest calendar year's share of net, and the years positive.
- **The control:** every candidate in the span (take everything).
- **The component line:**
  - net daily Sharpe at one MES with its monthly block-bootstrap SE;
  - hit, skew, and gross beside net;
  - ρ with the admitted MACD arm wherever the arm's daily P&L exists on the span. The assembled book is the joint
    run's object.
- **The expected-profit reading (D649's template, reported only):** the unseen mean gross against 2c = $8.84.

## 5. Power (a rough estimate now; the runner computes it before the freeze)

**The per-trade sd is about $95** (D705: per-trade Sharpe 0.93 at 45 a year). About 120 unseen trades.

| effect kept | expected t | PASS probability | promotion |
|---:|---:|---:|---:|
| 100 % (+$13.21) | ≈ 1.5–1.7 | **≈ 0.6–0.7** | ≈ 0.15–0.2 |
| 50 % | ≈ 0.8 | ≈ 0.3 | — |
| 25 % | ≈ 0.4 | ≈ 0.2 | — |
| 0 % | 0 | 0.10 by construction | 0.005 |

**The runner's `--power` states two things exactly:**
1. **The size of the test:**
   - 20,000 draws of 120 trades, resampled with replacement from F2's in-sample net trades demeaned to zero;
   - the share with t ≥ 1.2816 must be **at most 0.12** (fat tails and skew can move it off 0.10).
2. **The power on contiguous in-sample windows:**
   - windows of 640 candidates (the unseen span's size), starting every 5 candidates;
   - each window's F2 trades have their net shifted so that the full-sample mean is scaled to 100 / 50 / 25 / 0 %;
   - reported: PASS and promotion rates, and the trade count.
   - The windows overlap heavily (about two independent ones), and 2022 sits in many of them. **So the 0 % line will
     not read 0.10; it shows the time concentration** (D698-A1's lesson) and is reported, not gated.

**The rule, written now:**
- **If check 1 fails, the test is miscalibrated, nothing is frozen, and the principal is told.**
- Otherwise the rule is frozen on the principal's ruling, whatever check 2 says. Its figures go into the freeze and
  the AITODO line.

## 6. Prerequisites for the vault look

1. **The price data is on disk** to 2026-09-09. No vault-input build is needed: F2 reads only `fut_ES_rth_1m.csv.gz`.
2. **The freeze** holds:
   - the sha256 (LF-normalised) of this record, the runner, and every script whose function it calls (D618, D702,
     D671, D691);
   - the fixture's sha256;
   - the in-sample known answer;
   - the power figures;
   - slot 7 registered.
3. **The principal's word** for the joint run, given on the command line.

## 7. The runner's assertions (each shown to raise in `--selftest`, or proved in `--known-answer`)

- **Known answers:**
  - D618 §3c on the in-sample frame (1,960 sessions, +0.6795 points, hit 0.4929);
  - **F2 on D705's window: 252 trades, mean net +$13.208968…,** through the runner's own build;
  - the runner's take flags and gross **equal D705's path** (D702's build, then D705's `family`) session by
    session.
- **Prefix stability:** the extended build's in-sample part equals the in-sample build bit for bit (σ_F5, b, the three
  tiers, the take flags). **The later data changes nothing earlier.** In the vault run this is re-proved on the
  extended build before a single unseen trade is scored.
- **Lag:**
  - `tier_audit` on tₐ, t_b and t_c;
  - D702's realised-volatility audit and its canary (a grid that reads the bar starting 15:30 must raise);
  - a tier canary that ranks its own value must raise;
  - a σ_F5 canary that includes today must raise.
- **Sign, in money:** a favourable continuation pays positively long and short.
- **The seal:**
  - in every mode except `--vault`, no session ≥ 2024-01-01 reaches the build;
  - `--vault` refuses without the principal's word, the freeze verifying (every hash), and a first opening (a second
    is refused).
- **The statistic:** on synthetic data, an injected edge PASSes, noise PASSes about 10 % of the time, and fewer than
  30 trades reads UNRESOLVED.

## 8. Predictions (about the unseen span, checked only in the joint run)

1. **F2's mean net is positive but below the in-sample +$13.21.** The selection path of §0 implies shrinkage; the
   post-2022-05-16 in-sample figure, +$7.06, is the better guide.
2. **The PASS is closer to a coin flip than the in-sample t suggests.** At +$7 a trade, the expected t on about 120
   trades is about 0.8.
3. **F2 beats take-everything** on the span (mean net).
4. **No calendar year in the span holds more than half of F2's net** (D705's (d), reported only).
5. **ρ with the MACD arm stays below 0.1.**

## 9. The ledger

- **The component line in §1.5 enters `docs/COMPONENTS_PROP.md` as entry #4, PROVISIONAL, on the principal's
  ruling**, with the (d) failure written into the row.
- **On the standard's point estimates**, C-a (daily net Sharpe 0.80 > 0.5), C-b (ρ +0.02 with #2), C-c (positive
  skew) and C-d (daily σ about $40 at one MES) are met. C-e is this record and D705.
- **The joint run promotes or removes it.** A PASS keeps it and puts it in the assembled book; a FAIL removes it.
- **A disclosure:**
  - F2's unfiltered parent is D618 §3c, which is not a ledger entry, so the ledger's subset rule does not bar it.
  - K3 (D466, from D463: −0.29 net, not entered) shares F2's clock, 15:30 → 16:00 on ES. It signs on a different
    quantity, the return from the previous close to 15:30. The two are not the same construction.
