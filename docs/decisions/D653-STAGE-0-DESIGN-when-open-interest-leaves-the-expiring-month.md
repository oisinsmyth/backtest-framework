# D653 STAGE 0 DESIGN — when does open interest leave the expiring contract, how much of it leaves outside the index roll windows, and could anyone trade it without holding the expiring month?

*Drafted 2026-09-28 on the principal's word ("Write Stage 0"). Committed alone, before its builder exists (R8).
**It reads open interest and cleared volume only: no price, no return, no position.***

## 0. The question, and what bounds it

**The mechanism.** A trader who cannot take or make delivery must close or roll a physically delivered contract
before its deadline: the first notice day where there is one, otherwise the last trading day. The deadline is
published, and the population subject to it is named by the exchange's rules. `ALPHA_PROGRAMME.md` lists
"expiry and delivery mechanics" as fully derivable forced flow (§5.3) and as roadmap item 12. No record has
tested it. [D582](D582-CLOSED-the-deposit-and-the-mechanism-programme-synthesis.md) closed the deposit's list; the
principal's instruction reopens this item.

**Two boundaries, both set by the principal before this record:**

1. **No position in an expiring physically delivered contract near its delivery window, on either book** (2026-09-28:
   a risk "hard to account for in a backtest" and "a risk that I am not willing to take regardless"). So the only
   constructions this line could ever reach are ones **without the expiring leg**: the forced roll's other side on
   the *next* contract, hedged with the one after it. This Stage 0 is scoped to that.
2. **Multi-day, so the personal book only.** Prop firms force-flatten before expiry and require a daily flat.

**What is already being tested, and must not be duplicated.**
[D635](D635-PRE-REG-gate-c0-index-roll-flow-in-the-settlement-window.md) (the index-reweight programme, a parallel
line) tests whether the commodity indices' scheduled roll (BCOM and GSCI, business days 5–9) reaches the
settlement window and moves the calendar spread, 2016-02 → 2025-02. The ETF rolls are the settlement ledger's
(P8a/P8b). **The only part of the forced flow that is this line's own is the drain that happens OUTSIDE those
scheduled windows**: deadline-driven exits and rolls by everyone else. If that part is small, unpredictable,
mostly exits rather than rolls, or lands where the next-but-one contract is too thin to hedge, there is nothing
here that D635 does not already cover. This Stage 0 decides that before any price is read.

**Read before this record, all disclosed:** the exchange spec file's settlement type and termination rule for
the 23 roots it holds (`data/futures_contract_specs.json`; MCL is financially settled and terminates one business
day before CL); the expiry file's coverage of the 26 roots below; D635's pre-registration; the index methodology
facts (`data/index_reweight/methodology_facts.json`: BCOM roll BD6–10, hedge roll BD5–9, counted on the BCOM
business-day definition); `gsci_schedule.csv`'s designated-contract columns; and the ledger's CL/NG calendar flags.
**No open-interest figure of any contract has been looked at for this question.**

## 1. The roots and their deadlines

Physically delivered roots on the breadth set, 26 of them:

| group | roots | deadline |
|---|---|---|
| energy | CL, HO, RB, NG | **last trading day**, from `data/fut_expiries_from_definition.json` (delivery follows expiry) |
| FX | 6E, 6J, 6B, 6A, 6C, 6S | **last trading day**, from the same file |
| metals | GC, SI, HG, PL, PA | **first notice day** = the last business day of the month before the delivery month |
| Treasuries | ZN, ZB, ZF, ZT, UB, TN | **first notice day**, the same rule |
| grains | ZC, ZS, ZW, ZL, ZM | **first notice day**, the same rule |

Excluded as cash-settled or not deliverable in this sense: the equity index roots and their micros, NKD, SR3, BZ,
BTC/MBT, HE; LE, whose delivery runs through the month.

**The first-notice rule is declared from the exchange rulebooks and is not in a sourced file on disk.** So it
carries a gate (G-FND, §4): if a root's open interest has not mostly left by the declared day, the rule is wrong for
that root, and the root is reported on its last trading day instead, with the failure named.

**Business days** are the root's own publication sessions (a reference session on which the root published open
interest). "BD k" is the k-th such session of the calendar month.

## 2. What is built

`data/fixtures/fut_oi_expiry_cycles.csv.gz` (gitignored like every panel; meta tracked): per (root, contract,
reference session), the contract's **open interest** (`stat_type` 9, `quantity`) and **cleared volume** (`stat_type`
6), from the `statistics` pull `GLBX-20260911-SDNLQ6M99S`, with:

- the **windowed** instrument-id mapping (D520/D521: a flat id map counted an Australian-dollar contract as crude);
- `ts_ref` read as the session start the evening before the trade date it describes (the reference session is the
  next calendar session), exactly as `build_fut_open_interest.py`;
- UNDEF and negative values dropped, and duplicate publications kept once;
- **reference sessions 2016-01-04 → 2023-12-29 only.** The builder filters at extraction and asserts after
  (`frozen.filter_before`, `assert_none_at_or_after`): nothing from 2024 onward is read, for this line or any other.

**A cycle** is one contract's approach to its deadline D, with D on or before 2023-12-29. For each cycle:

- **the expiring contract** is the one whose deadline is D;
- **the receiving contract** is the later delivery with the largest open interest at d = −20 (it takes the roll: the
  next active month, not necessarily the next listed serial month);
- **the hedge contract** is the delivery after the receiving one with the largest open interest at d = −20;
- d counts the root's business days to D (d = 0 is the deadline), over d = −30 … 0.

## 3. The measurements, per root

| | measurement | definition |
|---|---|---|
| M1 | the drain profile | median over cycles of OI_exp(d) / OI_exp(−30), for d = −30 … 0 |
| M2 | the half-drain day and its predictability | the first d at which OI_exp ≤ 50 % of OI_exp(−30); per root the median and the **IQR across cycles**, and the median by year |
| M3 | the share outside scheduled windows | of the drain ΣΔOI_exp over d = −30 … 0, the share on days that are NOT BD4–BD11 of their month (a padded superset of the BCOM/GSCI BD5–9 hedge window, allowing a day either side for calendar differences), and NOT a ledger `fund_roll` day (CL, NG). Roots in neither index (the Treasuries, FX, PL, PA) have no index window and are reported both ways. The padding makes the outside share conservative |
| M4 | roll, not exit | −ΣΔOI_recv / ΣΔOI_exp over d = −30 … 0: the share of the expiring month's drain that reappears in the receiving month. Only a roll pushes the receiving contract; an exit touches nothing a no-expiring-leg construction can hold |
| M5 | size against the receiving contract | the largest five-day drain of the expiring contract **outside** the scheduled windows × M4, divided by the receiving contract's cleared volume over the same five days |
| M6 | can the hedge leg be traded | the hedge contract's median cleared volume over d = −30 … −10, divided by the receiving contract's |

Reported beside, not gating: the root's total open interest through the cycle (does it fall, meaning exits?);
the year-by-year table of M2–M5; the five largest outside-window drains, named.

## 4. The gate and the bar

**G-FND** (the declared deadline is right): for a first-notice root, in at least 90 % of cycles, OI_exp at d = +1 is
below 25 % of OI_exp(−30). A root that fails is re-scored on its last trading day and reported as such.

**A root qualifies** if all five hold:

- **Q1** M3 ≥ 0.5: most of the drain is outside the scheduled windows D635 and the ledger own.
- **Q2** M2's IQR ≤ 3 business days: the timing is predictable from the calendar.
- **Q3** M4 ≥ 0.5: most of it is a roll into the receiving month.
- **Q4** M5 ≥ 0.10: the outside-window roll flow is at least a tenth of the receiving contract's volume over its
  five heaviest days (at a tenth of volume, square-root impact is about a third of a day's sigma).
- **Q5** M6 ≥ 0.05: the hedge contract trades at least a twentieth of the receiving contract's volume, so a
  receiving-against-hedge spread exists to hold.

**Routing.** **Three or more qualifying roots** → a pre-registration of a no-expiring-leg construction on those roots
(short the receiving contract against the hedge contract into the outside-window drain, flat before the expiring
month's deadline, personal book), with its price nulls, costs from D651's map, and forward power stated, put to the
principal before any price is read. **Fewer than three** → the line is covered by D635 or not tradeable under the
principal's rule, and the recommendation is to close it.

## 5. Predictions, written before the build

1. **G-FND passes** on the metals, Treasuries and grains: open interest is mostly gone by the first notice day.
2. **The Treasuries and FX** drain inside the last seven business days, with M2's IQR ≤ 2 and M4 ≥ 0.8. They then
   **fail Q5**: the quarterly contract after the next one is too thin to hedge (M6 < 0.05).
3. **CL** has M3 between 0.4 and 0.7 (its last trading day sits around the 20th, after the index window), M4 ≥ 0.7
   and Q5 passes: CL is the most likely root to qualify.
4. **The grains and metals** have M3 ≥ 0.5, because the first notice day falls at the month's end, after BD5–9.
5. **Between two and five roots qualify.**

## 6. Files and cost

`scripts/build_fut_oi_expiry.py` (`--selftest`, `--build`, `--report`), system interpreter for the Databento read,
strided worker processes over the pull's files; the fixture and its meta; `data/stage0_d653_oi_expiry.json`. Probed
on one file before the full build. The selftest must show: the windowed mapping refuses a reissued id; the
reference-session label is the trade date; the extraction refuses a 2024 session; the first-notice rule lands on the
right day across a month-end holiday; the receiving and hedge contracts are chosen on d = −20 open interest and never
the expiring one; and M3's window test counts a BD5 drain as inside and a BD12 drain as outside.
