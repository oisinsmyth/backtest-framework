# D504 — the MACD arm across every year the fixture holds: the signal clears its null by **35 SE**, the concentration objection is an artifact, and the binding constraint **crossed over in 2021**

**2026-09-13.** Runner [`scripts/d504_arm_full_history.py`](../../scripts/d504_arm_full_history.py) ·
artifact [`data/d504_arm_full_history.json`](../../data/d504_arm_full_history.json).

**A description, not a study.** One frozen construction, every year on disk. No search, no grid,
no threshold, no selection — so nothing is pre-registered, because nothing is being decided.
Nothing admitted ([R15](../RULES.md#r15)). The 2024+ slice was already spent by
[D503](D503-RESULT-the-Sharpe-transferred-and-nothing-else-did-one-MNQ-has.md);
describing it is not a re-read, and nothing here sharpens any cell.

Requested by the principal after [D503 §9](D503-RESULT-the-Sharpe-transferred-and-nothing-else-did-one-MNQ-has.md)'s
correction: *"do a full study of the arm across the full range of dates we have available."*

---

## 1. Overall, 2016–2026 — 2,508 sessions, 2,543 trades

| | |
|---|---:|
| **net Sharpe** | **+0.698** (SE 0.353) |
| gross Sharpe | +0.941 |
| mean / session | +$10.25 |
| daily σ | $233 — **0.47% of $50k**, inside C-d |
| **total** | **+$25,697** |
| max drawdown | $7,814 |
| worst day | −$1,761 = **88% of the $2,000 budget** |
| skew / kurtosis | +0.56 / 16.8 |
| trips / session | 1.01 |
| hit rate / payoff | 50.5% / 1.13 |
| mean / trade, net | +$10.11 |
| **mean / trade, gross** | **+$13.61 = 3.88× the $3.50 cost** |
| **P3a** | **0.50 breaches/yr — PASSES the amended bar of 1.0** |

### And it clears its rotation null decisively

| | observed | null p50 | null p95 | margin |
|---|---:|---:|---:|---:|
| net Sharpe, signal rotated, 2,000 draws | **+0.698** | −0.226 | **+0.272** | **+35.3 SE — CLEARS** |

**D503's "does not clear" was slice length and nothing else.** On 652 sessions the null's p95 was
+0.758; on 2,508 it is +0.272. Length buys resolution — not a better signal.

## 2. The concentration objection is an artifact of looking at one side

| | share of total P&L |
|---|---:|
| top 1 session | 10.3% |
| top 10 sessions | 52.6% |
| **top 1% (25 sessions)** | **+98.2%** |
| **bottom 1% (25 sessions)** | **−89.9%** |
| **P&L with BOTH 1% tails cut** | **$23,564 = 91.7% of the total** |
| P&L with the best *and* worst 10 sessions cut | $23,663 |

**The tails nearly cancel and the middle 98% of sessions carries 91.7% of the money.** "Ten
sessions carry half the P&L" is true and meaningless on its own — it is exactly the statistic
CLAUDE.md calls *"a flag, not a verdict… on a two-sided fat-tailed book it always frightens."*
**I quoted the one-sided version twice** (D503 §2 and again in conversation) before computing its
counterpart. The symmetric per-trade trim agrees: **+$8.50 against a raw mean of $10.11 — 84%,
and 2.4× the cost.**

## 3. Per year — and the yearly Sharpe is not a track record

| year | sess | trades | mean $/d | σ $ | Sharpe | (SE) | total $ | worst $ | % budget |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 2016 | 235 | 233 | −0.60 | 52 | −0.18 | 1.04 | −140 | −155 | 8% |
| 2017 | 233 | 238 | −1.36 | 43 | −0.50 | 1.10 | −316 | −131 | 7% |
| 2018 | 232 | 242 | +3.24 | 120 | +0.43 | 1.09 | +752 | −394 | 20% |
| 2019 | 233 | 232 | −3.25 | 80 | −0.64 | 1.14 | −757 | −285 | 14% |
| **2020** | 237 | 237 | **+36.89** | 208 | **+2.81** | 2.29 | **+8,744** | −523 | 26% |
| 2021 | 238 | 245 | +7.63 | 191 | +0.63 | 1.13 | +1,815 | −852 | 43% |
| **2022** | 235 | 238 | +23.94 | 334 | **+1.14** | 1.33 | **+5,625** | −1,315 | 66% |
| 2023 | 233 | 243 | −1.29 | 206 | −0.10 | 1.04 | −300 | −682 | 34% |
| 2024 | 235 | 239 | −0.09 | 256 | −0.01 | 1.04 | −21 | −880 | 44% |
| **2025** | 232 | 231 | +23.64 | 391 | **+0.96** | 1.26 | **+5,484** | −1,761 | **88%** |
| **2026** | 165 | 165 | +29.15 | 386 | **+1.20** | 1.62 | **+4,810** | −1,645 | 82% |

**Every yearly SE is ≈ 1.0 or worse.** A column swinging ±1 is what *no* edge looks like over one
year, so no year in this table is individually interpretable — only §1's pooled row is. The
column is here to show *shape*, not to be read as a record.

**The shape is a regime strategy.** Six of eleven years are positive on the point estimate, and
**2020 + 2022 + 2025 + 2026 = $24,663 of the $25,697 total — 96%.** 2016, 2017, 2019, 2023 and
2024 are flat to negative. It earns in volatile, trending years and does nothing in quiet ones.
Note 2023–2024 were *high-σ and flat*, so "high volatility" alone is not the condition — what
tracks the good years is the **gross/cost ratio** (11.5, 7.7, 7.8, 9.3 in the four winners
against 0.1–1.0 in the flat ones).

**Diagnostic only, below the fixture's usable start** (GLBX covers 21–42% of index day sessions in
2010–12, ≥96% from 2016 — D462): 2010 −7.64, 2011 −2.72, 2012 −1.41, 2013 −1.70, 2014 −0.10,
2015 −0.99. **Every pre-2016 year is negative**, on 20–206 present sessions a year, with the fee
at 8–17.5% of the move. Excluded from every total above.

## 4. The crossover — this is the finding

| year | NQ level | 1 MNQ notional | **× the $50k account** | E\|move\|/trade | **fee/move** | gross/cost |
|---|---:|---:|---:|---:|---:|---:|
| 2010 | 1,973 | $3,946 | **0.08** | $20 | **17.5%** | −2.11 |
| 2015 | 4,437 | $8,874 | 0.18 | $43 | 8.1% | −0.02 |
| 2018 | 7,001 | $14,002 | 0.28 | $84 | 4.2% | 1.89 |
| 2021 | 14,457 | $28,915 | 0.58 | $142 | 2.5% | 3.11 |
| 2023 | 14,237 | $28,473 | 0.57 | $154 | 2.3% | 0.65 |
| **2026** | **27,512** | **$55,024** | **1.10** | $273 | **1.3%** | 9.32 |

**Two constraints moved in opposite directions on a fixed $0.50 tick and a fixed $3 commission,
and they crossed around 2021.**

- **The fee stopped mattering.** 17.5% of the average move in 2010 → **1.3% in 2026.** The cost
  objection that dominated this line for weeks — D469, D486, D493, D499 — is a 2010s problem.
- **The contract grew into the barrier.** 0.08× the account in 2010 → **1.10× in 2026**, against a
  drawdown floor that never moved. The worst day went from 8% of the loss budget to 88%.

**So the binding constraint is no longer the edge or the fee. It is the account.**

## 5. Replaceable-account economics, every fee paid

Profit realised *inside* each account life, a breach forfeiting what was still open, $209 per 50K
account:

| era | deaths | mean life | realised | fees | **net** | $/yr | **%/yr** |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2016–2023 (in-sample) | 7 | **256 sess** | $15,423 | −$1,463 | **$13,960** | $1,875 | **3.8%** |
| 2024–2026 (spent holdout) | 11 | **53 sess** | $10,274 | −$2,299 | **$7,975** | $3,180 | **6.4%** |
| **2016–2026 (all usable)** | **18** | **137 sess** | $25,697 | −$3,762 | **$21,935** | **$2,204** | **4.4%** |

**Positive in both eras, and better in the recent one** — the earnings rate rose even as the
account life collapsed from 256 sessions to 53. **The fee/move and notional/account columns are
both doing exactly what §4 says: more money per session, and a shorter life to collect it in.**

**The caveat that decides whether this is real money:** it assumes profit is *withdrawn* before a
breach. A breach forfeits the open profit, and 2024–26's total leans on one life that made $7,671
in 39 sessions. **MyFundedFutures' withdrawal mechanics have not been read**, and they decide
whether a 53-session life can be banked.

## 6. What this changes

- **The signal is established on this fixture.** +35.3 SE over its rotation null on 2,508
  sessions, gross 3.88× cost, symmetric trims holding at 84–92%. It is not a tail artifact and it
  is not a short-sample fluke.
- **It is a regime construction**, and the record should say so wherever it is quoted: four of
  eleven years carry 96% of the money.
- **The P3 bar I set on 2026-09-13 is a moving target.** Overall P3a is 0.50/yr and passes; 2022,
  2025 and 2026 read 2.14, 2.17 and 1.53 and fail. A rate bar calibrated on a pooled window does
  not survive a price level that doubles.
- **The open question is the vehicle, not the strategy** — a larger account, a wider floor, or a
  smaller-notional instrument. At σ $233 pooled the $2,000 floor gives a 137-session life; at
  2026's σ $386 it gives 53.

## 7. Checks

15 checks, all passing. The ones that matter:

- **The Sharpe SE column is verified against Lo (2002)**: a one-year Sharpe of 0 carries SE
  exactly 1.00, ten years carries 1/√10, and a higher Sharpe carries a *wider* SE. Without this
  column the yearly table would read as a track record.
- **The account walker** is checked on a hand-built series: one death, the dead life's realised
  total equal to its own sum, the open life carried separately, one fee per death, and
  `net = dead + open − fees`; a series that never breaches is proven to pay **no** fee.
- **The trims are proven undefined below 100 trades** and reported as `None` rather than as a NaN
  that reads like a number.
- **The one-sided trim is proven to mislead** on a synthetic two-sided book — the assertion that
  it reads *below* the symmetric trim, which is the error §2 documents me making twice.
- `simulate_trades` is asserted bit-identical to D491's `simulate` on the real series before any
  per-trade statistic is computed.

## 8. Limitations

- **Pre-2016 years are diagnostic only** — the GLBX archive does not hold the index day session
  reliably before then.
- **2024-01-02 → 2026-09-09 was spent by D503.** This describes that series; it must not be used
  to sharpen or re-score anything.
- **A one-year annualised Sharpe carries SE ≈ 1.0.** The yearly column is shape, not evidence.
- **Fills are open-of-next-segment at the measured half-spread** — no queue, no partial fills, no
  slippage on a flip. Every figure is an upper bound, and the worst day is the figure most exposed
  to that optimism.
- **2026 is a partial year** (165 sessions to 2026-09-09).
