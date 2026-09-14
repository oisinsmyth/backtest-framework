# D528 ADDENDUM 3 — the book, the sides, and the capital rule

Date: 2026-09-14. Runner: `working/d528_book_and_sides.py` (`--self-test`, `--run`, `--micro`).

**Nothing admitted (R15). No component line written — see §6.** In-sample only; the reserved slice
(2026-04-11 → 2026-09-09) remains UNREAD. Exploratory: this is the same 20-cell in-sample window
as ADDENDUM 2, now scored as a book.

---

## 1. The universe is the binding constraint, before any edge question

**Only 8 of the 35 roots have a micro contract.** The other 27 are traded full size, and the
measured all-in cost per round trip — that root's crossing at its own `tick_usd`, plus $3.00
commission — runs from **$13.50 to $128.00**:

| | roots | all-in $/RT | worst day-session σ |
|---|---:|---|---|
| micro available | 8 | $3.67 – $7.12 | $279 (NQ) |
| **no micro** | **27** | **$13.50 – $128.00** | **$2,806 (SI)**, $2,334 (PA), $1,848 (HO) |

Against a $50,000 account with a 4% trailing max loss, the drawdown that matters is **$2,000** —
and SI, PA and HO each have a single-session σ at or above it. **Several instruments in the
all-root book risk the entire drawdown allowance in one session.**

That shows up exactly where it should. The all-root book's maxDD is **61× to 415×** the $2,000
limit. That is not an edge result, it is the vehicle: the constraint recorded as "fee and barrier
are one constraint" (D493) and "one micro has grown into the prop barrier" (D503), landing on this
construction. **Every number below is therefore the MICRO-ONLY book (8 roots)**, which is the only
universe this account can trade; the all-root figures are kept in the log as a diagnostic, not as a
candidate.

## 2. The book, micro universe, 8 roots, 147 sessions

Size 1 contract at minimum tradable size; cost = measured crossing × `tick_usd` + $3.00/RT;
realised stop fill; 3 slots; one position per root.

| cell | trades | expo | GROSS $/tr | NET $/tr | Sharpe g | Sharpe n | win | payoff | maxDD | / $2,000 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| A as specified (`cross2`) | 1,514 | 4.6% | −3.451 | −8.194 | −5.12 | −11.59 | 38.8% | 0.83 | $12,405 | **6.20×** |
| B no classifier | 11,323 | 30.8% | −2.179 | −6.869 | −9.16 | −27.52 | 36.0% | 0.88 | $77,773 | **38.89×** |
| **C `traverse` (the principal's)** | **109** | **0.4%** | **+2.248** | −2.411 | **+0.87** | −0.92 | 42.2% | **1.15** | **$356** | **0.18×** |

### 2.1 Cell C is the only one that is even the right shape

It is the only cell with **positive gross** (+$2.248/trade, gross Sharpe +0.87), the only one with
**payoff above 1** (1.15), and the only one whose drawdown **fits inside the account** ($356, i.e.
0.18× the trailing limit). Its breakeven cost is **$2.248/RT against $4.66 actually paid — it earns
48% of its own cost.** Trimmed 1% both tails −$2.512, skew +0.43, kurt 4.2, top 1% = 14.6% of gross
positive P&L, so it is not tail-carried.

### 2.2 And it does not clear its null. UNRESOLVED, not a pass.

| cell | real Sh_g | null g p50 | null g p95 | real Sh_n | null n p5 | p50 | p95 |
|---|---:|---:|---:|---:|---:|---:|---:|
| A `cross2` | −5.12 | −4.03 | −2.44 | **−11.59** | −11.31 | −10.42 | −9.02 |
| B none | −9.16 | −11.78 | −9.84 | −27.52 | −36.30 | −32.46 | −26.80 |
| C `traverse` | **+0.87** | −0.54 | **+0.80** | −0.92 | −4.78 | −1.88 | −0.21 |

Cell C's gross Sharpe of +0.87 sits **+0.07 above a 20-draw p95 of +0.80.** CLAUDE.md's rule is
explicit: a sample p95 is biased toward the centre, so carry its bootstrap SE and **record a margin
within 2 SE as UNRESOLVED** (D373). At 20 draws the p95's own SE swamps a margin of 0.07. **This is
UNRESOLVED, and on n = 109 trades, in the same cell that inverted at s=3 in ADDENDUM 2.**

Cell A is the other end: net Sharpe **−11.59 against a null p5 of −11.31** — the construction as
specified is *worse than its own sign shuffle*, which is the third independent confirmation that
`cross2` selects trend continuation.

## 3. Long versus short: symmetric, and the null proves the noise floor

The side is fully determined by which extreme was reached — `s = −1` (low extreme, rising drift) is
a LONG, `s = +1` a SHORT — so splitting on `s` splits on side.

| cell | side | n | share | P(target) | win | mean tk | null mean tk |
|---|---|---:|---:|---:|---:|---:|---:|
| B none | LONG | 6,538 | 50.8% | 0.3732 | 40.0% | −2.952 | −3.180 |
| B none | SHORT | 6,327 | 49.2% | 0.3691 | 39.7% | −3.417 | −3.683 |

**LONG − SHORT = +0.465 tk, t +0.62 — and the sign shuffle's own asymmetry is +0.503 tk** with the
same SE. The null is symmetric by construction, so its asymmetry IS the noise floor, and the real
difference does not exceed it. Same answer in cell A (+1.502 tk, t +0.57, null +5.256).

**Cell C looks dramatic and is not.** Its shorts read +14.123 tk against longs +1.435, a −12.688 tk
split — but **the null's own split on the same 109 excursions is +6.114 tk with SE 11.8.** At this n
the noise floor is larger than the signal. This is what the null side-split column was added for.

**There is no long/short asymmetry in this construction at any power level tested.**

## 4. Prioritising capital on the expected return of a perfect set-up

Under perfect reversion the exit is the frozen level, so the gross gain is exactly `|y|`. Hence
`er_usd = |y|ᵗᵏ × tick_usd − cost_usd` is the trade's best possible dollar outcome — the same
quantity the feasibility filter gated on, used to **rank** instead of to exclude. Compared against
ranking by extremeness in σ, and against arrival order (the control that shows what ranking is
worth).

### 4.1 On the tradeable universe it is not a live lever, because the slot cap barely binds

| cell | perfect ER $ | extremeness | arrival only |
|---|---:|---:|---:|
| A `cross2`, 3 slots | −$8.19/tr | −$8.17 | −$8.19 |
| B none, 3 slots | −$6.87/tr | −$6.85 | −$6.82 |
| C `traverse`, 3 slots | −$2.41/tr | −$2.41 | −$2.41 |

Cell C has 109 candidates across 147 sessions, so 3 slots are never contested and all three rules
pick the identical book. Cell B takes 11,323 of 12,865 candidates — 88% — so the ranking only
arbitrates the remaining 12%. **Capital prioritisation is only a lever when candidates are dense
relative to slots, and on the micro universe this construction is not dense.**

### 4.2 On the all-root book, where it DOES bind, the rule made things worse

| cell | perfect ER $ | extremeness | arrival only |
|---|---:|---:|---:|
| B none, 3 slots, 35 roots | −$39.23/tr | −$35.10 | **−$33.47** |

**`er_usd` is a trade-SIZE selector, not an alpha selector.** It ranks up on a far target and on a
high `tick_usd`, and both scale the loss as hard as the win — the stop is `0.5·|y|`, so a bigger
target means a proportionally bigger stop. With a ~36% hit rate and payoff below 1, expectancy per
trade is negative, so **ranking on size makes it more negative.** The rule is correct wherever
expectancy is positive; where it is negative it is leverage.

It is visible in where the capital lands. Cell B, all roots, ranked by `er_usd`: **SI 6%, HO 5%,
PL 5%** — silver, heating oil and platinum, three of the most expensive full-size contracts on the
board. Arrival order instead gives BTC / 6E / ES.

### 4.3 The fraction of the perfect outcome actually collected

`realised/er` = gross $/trade ÷ mean perfect-set-up payoff. It caps at 1.0 and is the number the
prioritisation exists to raise:

| cell | mean er$ | realised/er |
|---|---:|---:|
| A `cross2` | $25.59 | **−0.135** |
| B none | $17.95 | **−0.121** |
| C `traverse` | $28.94 | **+0.078** |

Cells A and B collect a *negative* fraction of their own best case. Cell C collects 7.8%.

## 5. Gross is dominated by the fill convention, so read the differences

Cell B, micro: realised-fill gross −$2.179/trade, idealised-fill −$2.810... and the bracket on the
all-root book straddles zero (−$13.14 realised against **+$11.45** idealised). This is the
−1.82-tick martingale bias measured in ADDENDUM 2 §0.3 propagating into dollars. **Levels are not
interpretable; real-minus-null at a fixed convention is.** Both conventions are reported for every
cell for exactly this reason.

## 6. Disposition

**No component line, and the reason is the standard's own test:** a component line requires a
construction with positive net expectancy to score. Every cell is net-negative at every slot count,
so there is nothing to enter in `docs/COMPONENTS_PROP.md` and no correlation against K8 worth
computing. Writing one would imply a candidate exists.

**What this adds to ADDENDUM 2:**

1. The all-root book is **uninvestable at this account size independent of edge** — 27 of 35 roots
   have no micro and maxDD runs 61–415× the $2,000 limit. Any future construction on this fixture
   must be scored on the 8 micro roots or not at all.
2. **No long/short asymmetry**, at t +0.62 in the highest-power cell, against a null whose own
   asymmetry is larger.
3. **The perfect-set-up capital rule is a size selector.** It cannot help while per-trade expectancy
   is negative, and on the dense book it actively hurt. Revisit only if a construction reaches
   positive expectancy.
4. **Cell C (`traverse`, micro, 109 trades) is the first cell in D528 with positive gross, payoff
   above 1, and a drawdown inside the account.** It earns 48% of its own cost and its gross Sharpe
   is +0.07 above a 20-draw p95. **UNRESOLVED per D373.** It is not a candidate and must not be
   treated as one, but it is the only thing in this programme's mean-reversion line worth powering
   properly — which means more data, not more cells.
5. The route from ADDENDUM 2 §4.1 is unchanged and now sharper: cell C needs its cost roughly
   **halved**, and $3.00 of its $4.66 is commission, not spread. **A passive fill removes the
   crossing but not the commission**, so passive alone does not close a 52% gap — the commission
   is the larger half and it is not negotiable by execution style.
