# D556 — PRE-REGISTRATION: carry timing **as published** (Koijen–Moskowitz–Pedersen–Vrugt 2018) on the 36-root breadth fixture, the settlement-strip fixture it needs, and the trend + carry combination

**Pre-registration. Committed before the runner and before the fixture exist (R8). Result in a
separate file.** **In sample 2016-01-04 → 2023-12-29; the long window 2011-01-03 → 2023-12-29 is a
declared diagnostic; the 2024+ slice is RESERVED AND NOT READ** (the fixture may hold it; nothing
scores it). Nothing admitted (R15).

*2026-09-19. Second study from the deposit folder (`PUBLISHED_STRATEGIES.md` §3 and §8), taken
after D555's harness check passed at ρ = 0.815 against AQR. Carry needs the second-nearby
contract, which no fixture holds; this record specifies that fixture and its gates first, and the
study second. The null is the purged form D555 arrived at, declared here from the start.*

---

## 0. The fixture — every settlement, every listed month, 36 roots

**`data/fixtures/fut_settle_strip.csv.gz`** (gitignored by suffix, registered in the data manifest
with its sha256, sidecar `.meta.json` tracked): one row per (root, contract, session) with the
settlement price from the `statistics` schema (`stat_type` 3), labelled from the **windowed** id
mapping (D520/D521), sessions labelled exactly as D526's strip labels them (`ts_ref` + 1 day, ET).
Exact-zero settlements are dropped as the second missing-value marker (D526); negatives are kept
(CL settled −37.63 on 2020-04-20). Builder `scripts/build_fut_settle_strip.py`, 17 files on 8
processes, projected under three minutes from the open-interest builder's 250 s serial decode.

**`data/fixtures/fut_curve_front_next.csv.gz`**, derived from it and from the breadth fixture: per
root × session, the **front** contract (the breadth fixture's own front-by-volume election, so the
carry is read on the contract the position holds), its settlement, the **next** contract (the
nearest later delivery month with a settlement that session), its settlement, `months_between`
(delivery-month difference), and

```
carry_ann = (F_front − F_next) / F_next × 12 / months_between
```

positive in backwardation. The deposit applies this futures-implied form to every asset class; so
does this record, and it says plainly that on rates, FX and equity index the number embeds the
financing and dividend terms KMPV treat as carry.

**Gates, all computed and stored in the meta; the build raises on failure:**

| | gate |
|---|---|
| **G1** | the CL and GC rows agree **exactly** with `data/d526_curve_strip_CL_GC.csv.gz` on its window — same rows, same settlements to the ULP. This is the harness check: the extraction reproduces the one D526 already committed |
| **G2** | per root from its live start (D555's rule), a front settlement on ≥ 98% of the breadth fixture's sessions and a next settlement on ≥ 95% |
| **G3** | per root, median \|log(front settle / breadth session close)\| < 0.5%; anything over 2% is a labelling error and raises. Reported per root |
| **G4** | `months_between` in 1 … 12; no exact zeros; no weekend sessions; the only negative settlements are CL in April 2020 |
| **G5** | one worker's RSS printed before the pool is opened (memory: *measure the worker before the fan-out*) |

## 1. The constructions — fixed from the paper and the deposit, nothing tuned

Everything not stated here is **exactly D555's**: 36 roots and live spans; same-contract daily
returns off the breadth fixture with placeholder rows dropped; MOP's EW volatility (centre of mass
60 days) and 40% target; positions set at the month-end and held; the equal average over live
roots; the dollar book at minimum size with $3/$6 a round trip plus one tick, rolls charged, BZ and
SR3 excluded. The runner imports D555's functions rather than re-implementing them.

| cell | signal at month-end m | note |
|---|---|---|
| **A — carry sign (PRIMARY)** | `sign(carry_ann)` read from the month-end session's settlement | KMPV's timing rule as the deposit states it: long backwardation, short contango |
| **B — carry demeaned** | `sign(carry_ann − mean of the root's own month-end carry from its live start)`; flat until 12 month-ends exist | the deposit's alternative; no lookback parameter |
| **C — trend + carry** | `(sign_trend12 + sign_carry) / 2` × the vol scale; `sign_trend12` is D555's 12-month sign | the deposit's §8 combined forecast at equal weights; the dollar form is `sign(sum)`, flat on disagreement |

**Family (the declared unit of selection): 6 cells** = {A, B, C} × {published return-space book,
dollar book at minimum size}. Per-root, per-sector, commodity-only, per-year and per-era figures are
diagnostic and unpromotable. No de-seasonalisation of NG or the grains: the paper's basic measure
has none, and the per-root table will show what that costs.

**Causality.** The month-end session's settlement is published about 21:00 ET that evening and the
position earns from the next session; D497 established the same ordering for the statistics schema.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of cell A's published book, 2016-01-04 → 2023-12-29**, with a
> monthly block-bootstrap SE.

## 3. Nulls — D555's amended form, declared here from the start

**N1** — enumerated sign rotation within each root's live span, offset common to all roots and
cells, **offsets within 252 sessions of either end of the cycle purged** (D555 §2: the near-end
offsets are look-ahead on one side and a staler copy of the same signal on the other). The full
offset profile is stored. **N2** — the family maximum at each surviving offset.

**PASS requires: the primary > 0, above its N1 p95, AND the family maximum above its N2 p95.**
p50 and p95 reported beside every cell; SE 0 by enumeration.

## 4. Predictions — in the runner's quantities

| # | prediction | source |
|---|---|---|
| **P-1** (primary) | cell A gross Sharpe 2016–2023 **> 0, above N1 p95**; point **0.2 – 0.5** | deposit §3: 0.25–0.45 net for the diversified timing book |
| **P-2** (the reason carry is here) | daily correlation between cell A's book and D555's 12m book, 2016–2023: **\|ρ\| < 0.3**; point ≈ 0.1 | deposit §7: "roughly 0 to 0.2" |
| **P-3** (combination) | cell C gross Sharpe **> max(cell A, D555's 12m = +0.304)** | the diversification claim of §8 |
| **P-4** (shape) | cell A's daily skew **< 0**, and its **March 2020** return **< 0** | "picking up nickels"; carry loses in liquidity crises |
| **P-5** (slowness) | annual turnover of cell A in weight units **< D555's 14.7**, and the median per-root month-to-month sign persistence **> 0.8** | carry changes slowly |
| **P-6** (breadth) | cell A P&L positive on **≥ 21 of 36** roots over 2011–2023 | same bar as D555 P-4 |
| **P-7** (sectors) | commodity-only cell A Sharpe **< the diversified** cell A Sharpe | deposit: the 0.6 average leans on currencies and bonds |
| **P-8** (falsifier) | G1 or G3 failing means the fixture is wrong and nothing is interpretable; the primary below its N1 p50 with the gates green means carry did badly here | |

## 5. Cost line and component line

As D555 §5, both lenses: bp-of-notional turnover cost and breakeven bp/side for the published books;
$3/$6 + one tick, rolls as two sides, for the dollar books, with C-a/C-c/C-d, hit, skew, σ, the
C-d-eligible sub-book, and ρ with the ledger's live entry (absent unless its daily P&L is on disk).
**Every cell gets a component line whether or not it clears.**

## 6. Runner assertions

D555's three, re-run on this runner: the lag audit (an independent pandas derivation of the held
carry sign, proven to raise on the unlagged grid), the sign audit in money (proven to raise on a
negated and on a mis-lagged gross grid), and the right-quantity audit (the held grid changes only
after a month-end, proven to raise on a daily grid). Plus one new: **the carry sign at each
month-end equals the sign of `F_front − F_next` recomputed from the raw strip by a second path that
never reads the derived table.** `REQUIRED_OUTPUTS` guarded.

## 7. What is read, and what is not

The strip and the breadth fixture from 2010-06-07 for warm-up; **scored 2011-01-03 (diagnostic) and
2016-01-04 (primary) through 2023-12-29**; D555's 12m sign grid rebuilt in-process for cells C and
P-2. **Not read: any session from 2024-01-02 onward.** No published carry factor series is freely
available for a correlation check like D555's; the harness check is G1 (exact agreement with D526's
independent extraction) and G3 (settlement against session close), and the record says that is
weaker than D555's.

## 8. What this record does not do

No de-seasonalisation, no curve beyond the two nearest months, no cross-sectional sort (the deposit's
strategies 3–5), no weight other than 0.5/0.5 in cell C, no lookback for cell B. A finding that
carry is flat on 2016–2023 is a finding about carry on this universe and window, not about the
fixture, provided G1–G4 hold.
