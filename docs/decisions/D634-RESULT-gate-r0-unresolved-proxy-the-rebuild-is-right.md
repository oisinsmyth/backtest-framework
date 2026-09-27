# D634 RESULT — Gate R0 is UNRESOLVED (proxy). The rebuilt subindices match the published ones; the misses are the fund proxy, two data holes in 2020, and the LME stand-in

*Run once on 2026-09-27 (`scripts/run_gate_r0.py --run`). The runner was committed at `a4ebd9b`, after the
pre-registration `8fb1619` and its §8 amendment; a crash fix was committed at `68397c2` before the first completed
run, and no output existed before it. Output: `data/index_reweight/gate_r0.json` and the tracker panel
`drift_tracker_daily.csv.gz`. Sections 1–3 are the registered result. Section 4 is POST HOC
(`scripts/explore_gate_r0_diagnosis.py` → `data/index_reweight/gate_r0_posthoc.json`) and never replaces it.*

## 1. The verdict: UNRESOLVED (proxy)

- **Clauses that hold:**
  - R0-a: all known answers hold. Table 13 is reproduced; the deposit's unit tests 1–8, 12 and 13 pass; the weights
    equal the targets at every det to 1e-12; ICE Brent equals NYMEX BZ on 99.99% of 60,886 contract-days (maximum
    $0.03).
  - R0-c: coverage passes on all 15 CME components. There is no missing lead or next settlement on any open
    business day.
  - **The daily rule passes for every single-commodity fund, on roll days AND on other days:**

| fund | subindex | roll days within 5 bp | other days | monthly within 5 bp | median daily error |
|---|---|---|---|---|---|
| BOIL | natural gas | 99.8% | 99.6% | **51.8%** | 0.33 bp |
| KOLD | natural gas | 99.4% | 99.1% | **23.6%** | 0.55 bp |
| UCO | WTI (to 2020-03) | 99.7% | 99.7% | 100% | 0.23 bp |
| SCO | WTI (to 2020-03) | 100% | 99.2% | 94.1% | 0.25 bp |
| UGL | gold (from 2019-01-07) | 100% | 99.6% | **75.7%** | 0.26 bp |
| GLL | gold | 100% | 99.6% | **62.2%** | 0.33 bp |
| AGQ | silver (from 2019-01-07) | 100% | 99.6% | **63.5%** | 0.32 bp |
| ZSL | silver | 100% | 99.6% | **55.4%** | 0.41 bp |
| UCD | BCOM (2016-01 → 08-25) | **12.5%** | **17.4%** | **0%** | 16.1 bp |
| CMD | BCOM | **14.6%** | **15.6%** | **25%** | 16.6 bp |

- **What fails:** the monthly rule (≥ 90% of months within 5 bp) fails for six single-commodity funds, and the BCOM
  aggregate fails both rules.
- Under D634 §4 that is **UNRESOLVED (proxy)**, not FAIL: no single-commodity series fails the roll-day rule, and
  coverage holds. The misses are decomposed below and **Gate C0 waits for the principal's ruling.**

## 2. What was built (D634 §1)

- **The calendar:** 2,555 BCOM business days, 2015-01 → 2025-02. Each CME root has 4 holiday republications,
  which are not counted as settlements.
- **det = BD4 of January.** It agrees with BCOM's printed date in 7 of the 9 years with a printed date. It differs
  in two:
  - 2016: the rule gives Jan 7, BCOM printed Jan 6;
  - 2022: the rule gives Jan 6, BCOM printed Jan 7.
  - At the printed dates (§5, reported beside), the largest weight difference is 0.40% (2016) and 0.11% (2022).
    Wheat's 2016 flow flips sign, because its gap is near zero.
- **The CIMs and drifted weights for 2016–2025,** and ΔN for the 15 CME components.
  - The full index nets to zero to 1e-16 each year (§4.5). The CME subset's net is reported per year: −0.36% of AUM
    in 2025.
  - Examples, as target gap and contracts:
    - 2020 natural gas: +2.22% of weight, **+92,665** contracts (NG fell ~40% in 2019);
    - 2025 gold: −3.12%, −11,824 contracts;
    - 2025 soybeans: +1.59%, +32,529 contracts.
- **The bands:**
  - LME (IR-A4): the 3-month end moves any drifted weight by at most 0.015%, and flips no ΔN sign in any year.
  - AUM (IR-A5): it scales ΔN and never flips a sign.

## 3. What each miss is

1. **Two data holes, 2020-02-27 and 2020-06-30.**
   - `fut_settle_strip` has no settlement for most CME roots on those two days: the known 2020 holes. The ledger's
     `fill_settle_holes_2020.py` filled them for NG and CL only, from EIA.
   - Those days then fall below the 50% rule and are not business days. The next NAV interval carries two days'
     moves, giving paired errors of 200–930 bp (for example AGQ −596 bp on 06-30 and +650 bp on 07-01).
   - That breaks the monthly figure for February–March and June–July 2020 in every fund on those subindices.
2. **The fund proxy's accrual** (§4 below). Outside those months, the part of the monthly error that is our rebuild's
   is 0.2–1.0 bp at the median. The fund part is a steady −3.6 to −6.2 bp a month.
3. **The BCOM aggregate (2016).** Its daily error is 16 bp at the median. The single-commodity rebuilds are exact at
   the bp level, so the aggregate's error sits in what the single funds do not test:
   - the non-CME components' prices;
   - the multipliers across components.
   The post hoc regression points to the base metals (§4).

## 4. POST HOC: rebuild or proxy?

- **The split.** For each subindex, a +2× and a −2× fund track the same index.
  - An error in the rebuilt subindex enters both funds' monthly errors with the SAME sign.
  - An accrual the NAV model misses (interest, fees, swap financing) has the same sign in both funds' NAVs, so after
    dividing by ±L it enters with OPPOSITE signs.
  - So the half-sum is the rebuild's part and the half-difference the proxy's.
- **Excluding the four hole months:**

| subindex | rebuild part: median / share of months within 5 bp | proxy part: median / mean |
|---|---|---|
| natural gas (106 months) | **1.0 bp / 98.1%** | 5.8 bp / −6.2 bp |
| WTI (49) | **0.2 bp / 98.0%** | 3.3 bp / −3.6 bp |
| gold (70) | **0.4 bp / 100%** | 3.6 bp / −4.0 bp |
| silver (70) | **0.4 bp / 100%** | 4.3 bp / −5.1 bp |
| BCOM aggregate (8) | 12.6 bp / 12.5% | 3.7 bp / −3.9 bp |

- **Reading:**
  - **The rebuilt single-commodity subindices meet the deposit's 5 bp-a-month bar in 98–100% of months.** What
    fails the registered monthly rule is the fund proxy: a steady under-accrual of 4–6 bp a month, the same sign in
    every subindex. It is consistent with the funds earning more on collateral than the OECD 3-month rate, or with
    a fee or financing term the model lacks.
  - In the hole months the rebuild part is large and same-signed in both funds (silver −302 and −311 bp in June
    2020). That is the rebuild's input, not the proxy.
- **The aggregate.** The daily index-level error on the rebuild part (163 single-day intervals, median 8.3 bp) was
  regressed on each component's daily return. R² is 0.61.
  - The largest implied weight errors are the metals: copper −4.3%, aluminium +2.9%, nickel +2.5%, zinc +1.9%.
  - An error loading against COMEX copper and toward the LME metals is what a **timing mismatch** in the LME prices
    would produce. Westmetall's "cash-settlement" is the LME's official price, set around midday London; if BCOM
    values its LME components later in the day, our LME returns trail by part of a day.
  - This is a hypothesis, not a finding. The metals are highly correlated and the regression has 163 days.
  - Its effect on ΔN is bounded by the LME band above: at most 0.015% of weight, and no sign flip.

## 5. What this means, and the ruling needed

- **The drift tracker is right where it can be checked.** The rebuilt natural gas, WTI, gold and silver subindices
  match the published ones to 0.2–1.0 bp a month and pass the roll-day rule at 99.4–100%. The failures belong to
  the fund proxy, two missing days of input data, and the LME stand-in.
- **The rulings needed before Gate C0:**
  1. **The two 2020 holes.** Fill every CME root's settlements on 2020-02-27 and 2020-06-30 from Sierra Chart's
     daily files, which equal the CME settlement exactly on 1,095 of 1,095 checked days (IR-A13), and re-run R0
     once as a logged data fix. Alternatively, accept the result with those days as they are.
  2. **The monthly rule.** Accept the rebuild-versus-proxy split (§4) as the resolution of UNRESOLVED (proxy), or
     ask for a different reading of it.
  3. **LME timing.** Leave it as a band (its effect on ΔN is ≤ 0.015% of weight), or source the LME closing
     prices BCOM uses.
  4. **det.** Keep the rule's BD4 as pre-registered (IR-A3), with BCOM's printed dates reported beside.
- **Recommended:** 1 (fill and re-run once), 2 (accept), 3 (leave as a band) and 4 (keep). Then freeze the tracker
  and pre-register C0. C0 also has to settle the ZL/ZM roll-in gap in the Sierra flow files (AITODO).
