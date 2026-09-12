# PICKUP - handoff for the next session

**What data exists, and what bites each dataset: [`docs/data-available.md`](docs/data-available.md).**

## CME FUTURES ARE NOW ON DISK — 111.0 GB, verified, 2026-09-12

Databento `GLBX.MDP3` under a one-month CME Standard subscription. Every job quoted **$0.00**
against **$7,719** at published rates; total cost was the $199 subscription.
**`data/raw/databento/<job-id>/*.dbn.zst`** — gitignored, and **NOT in `temp/`**.

| schema | scope | window |
|---|---|---|
| `ohlcv-1m` | every instrument | 2010-06-06 → **2026-09-10** |
| `mbo` order book | ES NQ RTY YM CL GC ZN ZB | 2026-08-11 → 2026-09-10 |
| `tbbo` trade+quote | every instrument | 2025-09-11 → 2026-09-11 |
| `statistics` / `definition` / `status` | 41 roots | 2010-06-06 → 2026-09-11 |
| `bbo-1m` | 41 roots | 2025-09-11 → 2026-09-11 |

**129/129 hashes and byte counts verified, 16/16 DBN headers match the request, and the ten
`ohlcv-1m` slices tile with zero gaps and zero overlaps**
([`data/futures_acquisition_verification.json`](data/futures_acquisition_verification.json)).

**Four things before anything reads it.** Prices are **UNADJUSTED raw symbols with no
continuous series at all** — the roll must be built from `definition`. The pull ends
**2026-09-10**, so "through 2026-09-11" is wrong by one session. `ohlcv-1m` arrived in **ten
jobs** and a loader must read all ten. And it is free to re-fetch only to **~2026-10-11**.

**No fixture exists over it yet.** That needs the seven gates in `fetch_futures_1m.py`
reworked: they assume a *continuous stitched* series and this is *raw-symbol full-universe
across seven schemas*, so the roll gates do not transfer.

---

## THE PROP TRACK IS NOW A COMPONENTS SEARCH — D466 / D467 / D468, 2026-09-12

**The principal's correction, and the rule it produced.** Three prop records (C1, D463, D464) were
written "closed / not a candidate" on standalone hurdle-P bars without a component line. The book
is built by **layering components with net Sharpe > 0.5 and pairwise ρ < 0.3** to reach the
account's book-level 1.5–2, never by one strategy; CLAUDE.md now carries the two-altitude rule
(*score BOTH, every time*), `docs/COMPONENTS_PROP.md` is the append-only ledger with the
pre-registered standard (C-a net Sharpe > 0.5 at **minimum tradable size and the cost that size
pays**, C-b ρ < 0.3 with every prior entry, C-c skew ≥ −0.5, C-d σ ≤ 1% of $50k, C-e provenance;
PROVISIONAL entries below a family-maximum null's p95), and **only the assembled book is tested
against hurdle P and confirmed on the unread 2024+ slice.**

**The ledger is empty after 30 constructions.** The figures that opened it (C1 0.62, NQ last-30
0.42, book 0.91) were shell-line numbers at full-size cost in basis points; under the standard
(dollars, one micro, $3 ≈ 2 bp of notional) they are **+0.37 and −0.01** (D466, `e5ad3bc`). D467
(`59a151d`, RESULT + fixtures) built **hourly session tables for ES, NQ, YM, ZN, ZB, GC, CL, 6E**
(`data/fixtures/fut_sessions_hourly.csv.gz`, 18:00→16:59, front by volume, roll nights flagged,
five gates, usable from 2016-01-04 on all eight after two gate amendments — holiday sessions have
no 16:00 print, and the pre-2016 index/crude sessions are partial). D468 (`cff45f2`, RESULT)
scored **24 windows** (full session, overnight leg, day leg × 8 roots, long only): **best ES-W1
+0.39 (SE 0.32) at the 78th percentile of the common-sign family-max null (p50 +0.55, p95 +0.95)**;
the overnight index drift is gross +0.54..+0.64 on ES/NQ/YM and the $3 micro round trip takes
30–70% of it; treasuries, gold, crude, euro carry no session drift (gross within ±0.3); W2 ⊥ W3
(ρ 0.00..−0.05); the three index roots are one construction (ρ 0.91).

**D470 stage 0 (`b3671b2`, RESULT): can a state at the entry concentrate the drift?** Four
declared gates on ES/NQ, both windows, D464's two gate nulls and a family-max null. **The
principal's continuation and above-average conditions come out with the sign reversed:** the
drift follows DOWN sessions and DOWN overnight legs on 8 of 8 cells; the cleanest cell (the
overnight leg after a negative overnight leg) is +$10.66 vs −$1.37 on ES (2.5 SE), +$13.32 vs
−$1.57 on NQ (2.1 SE), gated net Sharpe +0.70 / +0.62 at micro cost, clears the rotation and
run-length nulls on both roots — **and fails the family-max p95 on both, because its size lives
in 2020–2022** (2016–2019: the two sides are equal). A pick, not a component; an in-sample
stage 1 would re-report it; the unread 2024+ slice (~190 gated nights, SE ≈ $7.8 vs +$10.7
expected) is the only test and is underpowered — **the principal's call whether to spend it.**

**D472 (`4290eeb`, RESULT): the pick tested on what the family null had not priced.** On a
standardised scale the in-sample family bar still refuses it (z 2.78 vs p95 3.13; gated Sharpe
+0.70 vs p95 +0.79 — the rotation null is centred on the drift, so the best of eight random
45%-gates on a drifting series sits at +0.48 median; eight years cannot beat that). **On SPY and
IWM cash 2010–2015, a period and instrument outside the family, the same construction (the
overnight gap after a negative overnight gap) is +5.5 / +7.7 bp vs ≈ 0 on the other side, 1.9 /
2.0 SE, clears both single-cell nulls, and is on the right side in 11 of 12 symbol-years; over
2010–2023 it is 24 of 28.** The prior-session variant (NQ-W1's big dollar cell) does not
replicate in cash. The declared step-3 criterion fails on the family condition alone; whether the
replication outweighs it is the principal's decision. If yes: one declared component (ES or NQ
overnight leg after a down leg, one micro, $3, in-sample gated net Sharpe +0.70 / +0.62), promotion
on the unread 2024+ futures slice (weak alone, ~190 gated nights) plus the cash 2024+ reserve.
**D473 (`fb69179`, in-sample RESULT): the component record, K7.** The principal took the pick to
a component record on the replication. One declared construction, no in-sample sharpening: long the
NQ overnight leg 18:00→09:00 on nights after a negative overnight leg (prior session's leg ≤ 0),
one MNQ, $3, NQ chosen on cost share; ES the check root; the 09:30 open a declared secondary exit.
In-sample line: **+0.62 (0.25)**, gross +0.80, 887 of 2,009 nights, +$13.32 vs −$1.57 (2.1 SE), N1/N2
cleared, C-a..C-d pass; ES +0.70 (2.5 SE); **the 09:30 exit is worse (−20% mean, +0.45)**; 71% of
the gated P&L follows prior falls > 1% (16% of nights; the dose–response is monotone on ES, not
on NQ — recorded, not used); worst night −$794, none below −2% at one micro; ρ(K7, K1) 0.39.
**Not entered** (the family bar). **The forward read is declared and unrun:**
`uv run python -u scripts/run_d473_downleg_component.py --forward --principals-word` reads NQ/ES
futures 2024-01-02→2026-09-09 and SPY/IWM cash 2024-01-02→2026-08-26 and applies the rule
(PROVISIONAL if diff > 0 on NQ and SPY, pooled z ≥ 1.5, NQ net Sharpe > 0; FULL if also futures
z ≥ 2 or pooled z ≥ 2.5; REMOVED if futures diff < 0, pooled z < 0.5 or Sharpe < −0.3). **It
spends the 2024+ slice for this construction; only the principal runs it.**
RTY added to the D467 table (nine roots; eight rebuilt bit-identically) and held back on G2
(a Sunday-session volume flip, 2020-06-14). A difference-between-sides family statistic, centred
on zero, is the right declaration for any future concentration test (noted in D472 §1, not run).

**What stands.** The overnight index drift is real on the futures and **unaffordable at micro
size** (breakeven cost for C-a on ES-W1 is $1.48 a round trip); the plan's 16:10 flat rule forbids
holding across sessions; the only lever inside this family is notional per contract, which the
$50k floor forbids (one ES night σ ≈ $1,840). **Next component families must have gross mean per
round trip large against $3 and their own σ** — anything with more than one round trip a session is
dead on arrival at micro cost. Unread: 2024-01 onward on every futures fixture. Untried: the
RTY/other-root event windows on the hourly grid (FOMC 14:00, CPI 08:30 — declared nowhere yet),
and the TWS quote pull that would pin the cost lines (D336/D441, no TWS listening).

## D464 — THE PERSONAL ARMS AS GATES ON THE SESSION HOLD: BETTER NIGHTS, INSIDE THE NULL, AND LIFE BOUGHT ONLY BY NOT TRADING, 2026-09-12

S1 and S2 (the book's own code on SPY) gating C1's 18:00→16:00 ES hold, 2,043 nights 2016–2023:
S1 on 8.7% of nights at +13.8 ± 10.0 bp, S2 on 10.0% at +9.1 ± 4.7, both with a lower MAE
tail than the average night (321 vs 369 bp) — **and both inside the exact rotation null (p95
+16.7 for a tenth of a 113-bp series).** Hurdle P at whole ES contracts: one contract's
overnight σ is the 4% floor, zero size at f ≤ 0.7%, a fixed contract breaches on 791 nights; at
micros the surviving sizes earn +0.2–2.2%/yr and the gates lengthen life to at most 1.94 years
at +0.8%/yr by removing 90% of the exposure. **Not a candidate; the personal book untouched.**
**Three prop records in one day say the same thing: the binding constraint is the
instrument–account pair** (ES σ per hold vs a $50k floor), not the candidate list. Records: spec
`0391331`, RESULT `docs/decisions/D464-RESULT-…md`; BOOK_PROP updated.

## D462 / D463 — THE PROP TRACK ON THE FUTURES THEMSELVES: THE DATA LAYER, AND THE FIRST CANDIDATE SCREENED ON ES, 2026-09-12

**The archive** (111 GB, `data/raw/databento/`, moved out of `temp/` by the principal) is now a
data layer: **ES, NQ, YM one-minute regular-hours fixtures**, front month by measured volume, no
stitching, five gates (`scripts/build_fut_index_1m.py`), **usable from 2016-01-04** — the archive
carries the index futures' evening bars but not their day session on most days before 2016 (21–42%
of the calendar in 2010–12; a fifth gate had to be added to see it; every earlier ES study's
2010–2015 numbers rest on 20–85% of days). RTY failed the cross-check on the 2020-03-16
limit-down open and is not committed. **Records: D462 (`de75a63`, RESULT `d69b59e`).**

**The candidate** — market intraday momentum, the last 30 minutes, lane 13's only near-miss —
screened on ES 2016–2023 (D463, `dd5801c`): **+1.18 ± 0.86 bp per trade at a 49% hit rate, slope
+1.8 (×100) against the published 6.18, inside the sign null; net +0.07 bp at a $17 round trip.**
**Hurdle P's P3/P4/P5 computed for the first time**, on the measured 30-minute path through
D440's lifecycle model: the C4 rule sizes below one contract at f ≤ 0.4%, and at every size that
trades the worst day breaches 2% on 13–87 days, the funded account lives 0.07–0.48 years, V < 0.
**Not a candidate; closed on this window; the 2024–2026 slice unread.** The durable output is the
arithmetic: a single ES contract's 30-minute σ (~$650) on a $50k account puts the floor 3σ away
per trade, so **no single-contract ES construction at that σ clears P3/P4 on this account size**,
whatever its edge. Records: RESULT `docs/decisions/D463-RESULT-…md`; BOOK_PROP updated.

## D457 — THE 8-K ATLAS WITH RETURNS: NO CELL CLEARS, THE DISTRESS ITEMS REBOUND, THE REACTION IS IN THE GAP, 2026-09-12

17 item cells × all/pure × both sides, cap 10, C1 (state-matched, no 8-K within ±5 bars) and
C2 (exact rotation) on every cell, a family bar with 0.04 cells expected to clear both. **Zero
clear both; four clear C1 (chance 0.85) — 2.02 earnings, 8.01, 5.07, 3.01 — all LONG.** The
common finding: a name that filed *any* 8-K drifts +8 to +16 bp over ten bars against a quiet
name in the same cell, and the rotated calendar earns the same (+0.7 to +1.1 bp/bar): filer
composition, not filing timing. **Every distress item is long-favoured after the next open**
(impairments +59, delisting notices +103, auditor changes +92 per trade; medians negative) — the
fall is in the gap, what follows is a two-sided rebound lottery; every short-side sign prediction
was wrong. 5.02 officer changes: −5 bp, the one short below the rotation band. Nothing within a
factor of four of its 51–80 bp round trip. **The line closes at stage 1; the 2024–2026 slice
stays unread.** Untested: 6-K filers; a same-day construction on the 15m fixtures (its own line).
Records: spec `0aad00a`, RESULT `docs/decisions/D457-RESULT-…md`, artefact `data/d457_8k_atlas.json`.

## D456 — THE 8-K ITEM ATLAS, STAGE 0: 155k CORPORATE EVENTS, DEAD-INCLUSIVE, SAME-DAY, 15 CELLS; THE ATLAS WITH RETURNS IS NEXT, 2026-09-12

The insider line was parked (real per trade, zero net at the crossed line — the third line to end
at the cost wall). The successor is chosen for *where it lives*: corporate events resolve in days
and move names by more than their spread. Parsed from D331's cached EDGAR submissions index
(0 new requests): **154,970 8-Ks 2010–2023 on 82% of the fixture and 81% of the dead** (the 18%
gap is foreign 6-K filers), median filing lag 0–2 business days, **15 item cells with ≥ 300
filings** (1.01, 1.02, 2.01, 2.02, 2.03, 2.05, 2.06, 3.01, 3.02, 3.03, 4.01, 5.02, 5.03, 5.07,
8.01; 4.02 and 2.04 too rare). Every cell sits in the thin half of the universe; **2.06
impairments are the one distress cell in liquid names**; 3.01 delisting notices are half
late-filers who survive. **28,492 filings from 2024-01 to 2026-08 are parsed and flagged
unread — the confirmation slice for the stage-1 atlas** (long and short scored on every cell,
cap 10, state-matched control per cell, enumerated rotation, both cost lines, reproduction on
the unread slice as the family's multiplicity control; opened only on the principal's word).
Records: spec `5f8899e`, RESULT `docs/decisions/D456-RESULT-…md`, events `data/d456_8k_events.csv.gz`.

## D455 — INSIDER PURCHASES, STAGE 1: REAL PER TRADE, ZERO NET AT THE CROSSED LINE, NOT A CANDIDATE, 2026-09-12

The event book (long, cap 63, every event, 7,478 primary filings → 4,086 trades once the kernel
skips names already held): **+89 bp per trade, median +96, 2.3 control-SDs above state-matched
names in the same cell (C1 p50 +24)** — a real, contrarian insider effect on the dead-inclusive
fixture. **The book: +1.11 ± 0.56 bp/bar gross against a rotated-calendar median of +0.66 and
p95 +1.47; crossed cost 1.03 → net +0.08; passive net +0.62 (1.1 SE); 14 names to half, top 1% =
70%.** Clusters (+120) beat singles (+54); directors (+101) beat officers (+58), against the
prediction; value has no gradient; shorting insider sales loses (−23 ± 12). Cap 21 is the
strongest per bar (+1.89) and the most expensive; every hold nets ≤ 0 crossed. **Two events
lines in a row now say the same thing: a genuine per-trade effect of +65 to +170 bp over a
quarter or two, in exactly the small, thin, beaten-down names where the modelled 60–90 bp round
trip is closest to the truth, and no book at that cost.** Not a candidate; holdouts shut.
Records: spec `398669b`, RESULT `docs/decisions/D455-RESULT-…md`, artefact `data/d455_insider_book.json`.

## D454 — INSIDER PURCHASES, STAGE 0: THE DATA IS THERE, DEAD-INCLUSIVE, TWO DAYS OLD, AND SHAPED FOR THE KERNEL, 2026-09-12

The issuance line was parked (real, factor-grade, unbookable on 13 years). Its successor is an
*event*: insider open-market purchases from the SEC's Form 3/4/5 bulk data (81 quarters, 910 MB
git-ignored, `scripts/fetch_sec_form345.py`), CIK-mapped through D331. **17,270 purchase filings
2010–2023 on 1,279 names — 76% of the fixture and 71% of the dead cohort — 90% filed within the
two-business-day rule.** Insiders buy what has fallen (47% after a bottom-tercile 20-day
return), what is small, cheap and thin (60% in the bottom dollar-volume tercile), and they
cluster (a second distinct insider within a week on 47%). No abandon condition fires. **Stage 1
is the next record, and stage 0 fixed four of its choices:** separate 10% owners (18% of filings,
nine of the ten largest dollar buys: Roche in FMI, Berkshire in BAC); a family-trust guard on
clusters (Hyster-Yale's 60+ Rankin trusts are every top cluster); the state-matched control is
required (the buys sit in exactly the cells with their own hedged drift); a declared value floor.
Records: spec `4ce4b86`, RESULT `docs/decisions/D454-RESULT-…md`, events
`data/d454_insider_events.csv.gz`. Later quarters 2024q1–2026q1 are cached and unread.

## D453 — ISSUANCE STAGE 1b: THE ACCOUNTING FIX HALVES THE LOTTERY AND DOES NOT MOVE THE VERDICT, 2026-09-12

D446's trades re-accounted with a per-name beta hedge and vol-scaled weights ([K2] identity at
β=1, w=1 asserted). SE 1.52 → 1.17 at the same gross (+2.2 bp/bar); nine names to half the P&L
(was 5), top 1% 51% (was 85%), GameStop 10% of the long leg (was 29%). **Net crossed +0.86 ±
1.17; the same four tests fail; T3 passes both sides at 2.2 control-SDs.** The record's own
prediction failed the informative way: **the rotated selector's base rate did not collapse (C2
median +1.12 → +1.27) while the name-randomised selector's did (+0.39 → +0.08)** — the deciles'
composition earns in excess of beta on any dates (a low-vol / quality tilt the six tested axes do
not name); the alignment to the actual issuance year adds ~+1.0 bp/bar on an SE of 1.2. **The
issuance line now has two forward-return looks on the same trades and one answer: real per trade,
unresolvable as a book on thirteen years of one universe.** Not a candidate; holdouts shut. What
would change it is calendar time or a second universe with its own EDGAR panel — not a factor
hedge, a shorter hold or another decile (each a new selection on spent data). Records: spec
`8b7747d`, RESULT `docs/decisions/D453-RESULT-…md`, artefact `data/d453_beta_vol_book.json`.

## D446 — ISSUANCE STAGE 1: REAL PER TRADE ON BOTH SIDES, A LOTTERY AS A BOOK, NOT A CANDIDATE, 2026-09-11

The first forward-return look at share supply. Decile slot book (40 a side, cap 126) on D444's
first-filed counts through the D345 kernel. **Per trade, against state-matched names (price ×
vol × mom cells), both sides pass the gate (2.5–2.6 control-SDs above the control median; see the RESULT addendum):** net issuers shorted +72 vs the cell's −97, net
repurchasers long +208 vs the cell's +34. **The book does not collect it:** +2.3 ± 1.5 bp/bar
gross, net crossed +1.0 at 0.6 SE, era 2 flat, **five names to half the P&L, GameStop's
2021 squeeze trade (entered as a repurchaser 2020-10-15) 29% of the long leg**, three collapsed
biotechs the short leg. The exact common-offset rotation has p50 +1.1 and p95 +3.8 (a persistent
selector on the wrong dates still earns its state tilt); the persistent random selector p95 +1.8
is cleared. **Not a candidate; holdouts shut (they have no EDGAR panel anyway).** Two honest next
questions in the record §6, neither a refinement of this one. Records: spec `84793d8`
(numbered D446 because D445 was taken by another session mid-write), RESULT
`docs/decisions/D446-RESULT-…md`, artefact `data/d446_issuance_book.json`.

## D444 — THE EDGAR ACQUISITION: THE DEAD ARE SERVED, ISSUANCE HOLDS, A STAGE 1 IS THE NEXT RECORD, 2026-09-11

D443's line, re-sourced from the SEC's XBRL companyfacts (`scripts/fetch_edgar_companyfacts.py`,
7 min, 226 MB git-ignored cache; CIKs from D331's resolution). **77% of the 562 dead names now
carry a point-in-time share series** (first-filed value, available the bar after `filed`; median
lag 38 days from period end; 0.1% ever restated). D443's tables re-run unchanged on the
dead-inclusive panel: persistence **0.54** a year out (survivors 0.44), rank R² on the six tested
axes 0.10, momentum +0.04, net-repurchase share 50%. **None of the three abandon conditions
fires.** Two gaps to carry: 168 multi-class/foreign filers (11%) have no undimensioned count in
this API; filer scale errors on 0.2% of rows need a 50× guard in stage 1. **Next, on the
principal's word: a stage-1 pre-registration** — issuance as a persistent state, slot book both
sides, state-matched control, enumerated rotation, persistent-selector control, both cost lines.
Records: spec `f0d97af`, RESULT `docs/decisions/D444-RESULT-…md`; panel `data/d444_issuance_panel.csv.gz`.

## D443 — NET SHARE ISSUANCE, STAGE 0: ABANDONED ON A1 (THE VENDOR SERVES NO DEAD NAME), 2026-09-11

The first non-price-path line after the volume line's close. Alpha Vantage `BALANCE_SHEET` +
`CASH_FLOW` on all 1,573 names (51 min, cached under `data/raw/alphavantage/fundamentals/`):
**0 of 562 dead names are served**, so the pre-registered abandon condition A1 (dead coverage
< 50%) fired and the line ends on this vendor. On the 988 survivors the object itself is good:
one-year persistence 0.44, rank R² on the six tested axes 0.10, momentum correlation +0.07,
tilted to small/cheap/volatile/thin names and 62% of name-quarters net repurchasers. **If the
principal wants issuance, the source is EDGAR's XBRL `companyfacts` API (by CIK, dead-inclusive,
with filing dates)** — a data acquisition record, not a study. Records: spec `0fa0d5c`, RESULT
in `docs/decisions/D443-RESULT-…md`. Memory: the vendor's three quirks (gross flow fields
empty; shares restated for later splits on half the names; delisted tickers empty).

---

## THE VOLUME LINE — D434 → D441, PARKED ON A COST MEASUREMENT 2026-09-11; THE PULL IS THE PRINCIPAL'S

**State in one line:** a real, state-conditional volume effect (B: a 3× volume bar in a top-price
name, sold short — +21 bp per trade over its state-matched control, +64 SE over the enumerated
rotation null) that is **not a book at any cost line the repo can justify** (D440: crossed
−0.63/bar, passive +0.65 ± 0.89, era 2 +1.06 ± 1.48; cap 40 +0.95 ± 0.59). **Both daily holdouts
are unseen by this line and stay shut**: the D440 candidate condition (T1 ∧ T3 ∧ T4 ∧ T5) failed
at +0.7 SE. Nothing is admitted. The principal chose, 2026-09-11, to park B and run the quote
pull rather than refine or spend a holdout.

**The chain:** D434 volume atlas (five axes; flat as a universe average) → D435 conditional atlas
(the shock is +38 in top-momentum names and −48 in top-price ones — a universe average hid a sign
flip) → D436 stage 0 → D437 stage 1 (A and B carry a shock increment; every component net-negative
under the kernel's PUB 52–75 bp) → D438 (the increment lives in the widest spread third; only B at
every horizon) → D439 (a passive order at the open fills 92%, chase 9 bp, net capture 0.66 —
**and the modelled half-spread on MSFT-class names is 17–55 bp/side against a quoted 1–2: the
cost models are range models**) → D440 (B under both lines: not a candidate) → **D441
pre-registered `a92710a`, runner and sample `295c70f`: the quoted spreads on the 272 names B
trades, and B re-costed at the quote.**

**WHAT THE NEXT SESSION DOES — in this order, nothing else first:**

1. The principal opens TWS or Gateway (paper 7497 / live 7496; Gateway 4002 / 4001) and runs, from
   the repo root, **D336 first** (the convention question outranks B's; ~35 min):

   ```bash
   uv run --group ibkr python scripts/d336_ibkr_quoted_spreads.py --pull --host 127.0.0.1 --port <PORT> --client-id 336
   ```

   then D441 (~80 min; 17 of its 272 names are already cached by D336 and are skipped):

   ```bash
   uv run --group ibkr python scripts/run_d441_b_quotes.py --pull --host 127.0.0.1 --port <PORT> --client-id 441
   ```

   Both are resumable (a name with a CSV is skipped), `readonly=True`, need the US-equity
   historical-quote subscription, and abort on ten consecutive subscription errors or on a name
   whose BID_ASK bars violate open ≤ close on 1% of days. Raw bars land in `data/raw/ibkr/`
   (git-ignored, exchange-licensed, never committed).

2. Then, no session needed:

   ```bash
   uv run python scripts/d336_ibkr_quoted_spreads.py --compare
   ```

   ```bash
   uv run python -u scripts/run_d441_b_quotes.py --compare
   ```

3. Write the two RESULT records. **D336's is owed since 2026-09-05** and must read Q2 on the
   non-clamped subset and mark Q3's second clause not evaluable (§8a). D441's bar: T3q ∧ T4q on
   the **crossed-at-the-quote** line → candidate for a holdout read, only on the principal's word.
   **X-e already says the book most likely still fails at 2 SE even at a favourable quote** — the
   pull decides whether B is closed on cost or on its own noise, and whether the wide tercile's
   +64 passive net is a per-trade object at all. Two known deviations to disclose in D441's RESULT:
   17 (not 33) names overlap D336's sample; 11 (not 10) padded names were excluded (GOCOQ).

**Two things the pull will hit, known now:** (i) the fixture carries acquired names as `alive`
with a constant close and zero volume since the acquisition (SPLK at 156.9, SGEN, KRTX, AVNS …;
the meta counts a delisting after the span end as alive). D441 excludes them by rule; **D336's
sample has one (AVNS)** — it will come back unresolved and D336's compare counts a missing CSV,
not a failure. (ii) D441's compare *excludes and lists* a name failing `[N]` or `[G]` where D336's
aborts; the RESULT reports every exclusion by tag.

**Parked by the principal, not closed** ("keep the rest in mind", 2026-09-11): a calendar-split
stage 2 (A off-cadence long / B on-cadence short); equal-risk sizing; anything on A, C, D.
**Method yield of the line, already in memory:** align the event mask to the kernel's fill
(D434's one-bar look-ahead); condition a new feature on the atlas states before calling it flat
(D435); read the cost convention the kernel gates on before predicting a net (D437); the cost
models are range models (D439).

---

## THE SECOND-ZONE LINE — D412 → D433, CLOSED BY THE PRINCIPAL 2026-09-10, BOTH DAILY HOLDOUTS SPENT

**Read this before touching either daily holdout: they are both spent, by this line, on
2026-09-10.** `us_shorts_daily_holdout` (803 names) was read a second time under the principal's
ruling that a holdout spent by an unrelated strategy is unseen by a new line (D430);
`us_shorts_daily_holdout2` (576 names) was read once (D433). There is no unseen daily
single-name data left for anything descended from a departure-zone touch.

**The line:** D412 departure zones → D413 distance arming + cell 2 (REV/EFF/DV medians) → D414–D416
entry timing (touch-day close wins) → D417–D419, D423–D425 nine exit constructions (none beats
`t+5`, no stop) → D420–D422 the second touch (STACK2-ANY, +45 in-sample) → D426 double-down (dead)
→ D427 five layers → D428/D429 the combined long book at 3 slots, which met the in-sample
candidate condition → **D430 holdout 1: the long arm −29 gross, everything above the base
rung gone** → D431 short arm on the union (tail-carried, unbookable) → D432 breadth gate (wrong
sign), DV lever (+8 bp), gap by half (inverts) → **D433 holdout 2: net Sharpe −0.19; the touch
effect reproduces a third time.**

**What is TRUE across three disjoint name sets (1,573 / 803 / 576):** a distance-armed
departure-zone touch entered at the touch-day close and exited at `t+5` earns **+9.8 / +10.1 /
+13.0 bp gross**; cell 2 makes it **+30 / +18 / +18**. Cost is 24–34 bp. **Net Sharpe of the best
transferable object (cell 2 ∧ top-ADV tercile, 10 slots): +0.05 / −0.03 / −0.19.** File the touch
effect as a base rate a future study must beat; it is not a trade.

**What did NOT travel, on both unseen sets:** the second-touch rung (+45 → +6 / +17), the cheap
tercile (+86 → +17 / +28), long-only (+80 → −29 / −21), the gap ordering (inverts), the ADV
tercile's gross side, every exit, every gate. The short arm's mean was positive on all three
sets on a median of ~0 and no 2–5 slot book collects it. In-sample nulls (within-day
permutation, matched random pools) were passed at +5 to +10 SE by selections that did not
transfer: **they test selection inside the spent names, not transfer.**

**Process disclosure — the door.** `run_d411` installs an unconditional audit hook refusing any
path containing "holdout" (no `allow` switch; `run_d365`'s `V65.allow_holdout(why)` is the
designated, logged unlock, but it lives on a module this line's chain does not import). D430's
ADDENDUM opened each holdout in a **separate hook-free process** (`scripts/d430_oos_loader.py`,
`scripts/d433_oos2_loader.py`, `--spend-the-holdout`), wrote the panel to a cache named without
"holdout", printed a receipt with the file's SHA-256, and the runner read the cache. The
information the designated door would have logged is in the receipts (D430/D433 RESULT); the
designated function was not called. If the guard is consolidated, the two hooks should become one
with the `allow` switch, and openers should call it.

**Reusable from this line:** `scripts/run_d430_holdout.py` (a fixture-parametrised pipeline with a
`--proof` mode that reproduces in-sample bit-identically before any out-of-sample read),
`run_d431_shorts_union.py::union` (two fixtures on one calendar), the ladder printed on every
out-of-sample read so a failure is located, Sharpe with a monthly block-bootstrap SE
(`run_d433_holdout2.py`), and the memory rules written on 2026-09-10 (measure the worker before a
fan-out; a required book is not utilisation × base; a tail-carried mean does not book; layers
selected on spent names vanish out of sample).

**The one lever never measured:** execution — passive fills at the zone versus the crossed-spread
Corwin–Schultz model. Blocked on the TWS session like everything else in 0d2 (1).

---

## THE SIGNAL HUNT — D391 → D397, CHAIN RETIRED 2026-09-09, READY TO MERGE

**The principal authorised the merge on 2026-09-09**, reversing the branch's standing rebase-only
rule. **The branch is rebased onto `master` and is a clean FAST-FORWARD — 55 commits ahead, 0
behind, no conflicts and no decision-number collisions left.**

**It was NOT merged from this session, and that is deliberate.** `master` is checked out in the
main worktree and **another session is actively committing to it** — four commits landed there
during the final minutes of this one. Git refuses to update a branch checked out elsewhere, and
forcing it would desync that worktree's index under a live session. **The merge is one
fast-forward command from the main checkout; it is recorded in the handoff rather than forced.**

[D396](docs/decisions/D396-RETIREMENT-the-sign-sequence-chain.md) is the retirement record and the
place to start.

> **THE D390 COLLISION WAS RESOLVED BEFORE THE MERGE, NOT CARRIED INTO IT.** Master had taken
> `D390` **twice** — the D163 re-cost and the D280 overnight-gap pre-registration — while this
> branch was running on a reserved D390–D399 block. **The branch's D390 (the volatility tilt) was
> renumbered to [D397](docs/decisions/D397-the-volatility-tilt-zr-scored-alone.md)**, along with
> its RESULT, its runner (`scripts/run_d397_volatility_tilt.py`) and its artifact
> (`data/d397_stage0.json`).
>
> **Every reference was moved by explicit, count-asserted replacement — never a blanket sed** —
> because a blanket rename once corrupted a link to a *different* record in `RULES.md`. Nine
> references were updated across `RULES.md` (R16's three), `D392`, `D393`, `run_d392` and the
> renamed files themselves; the three *"reserved D390–D399 block"* mentions in D393/D394/D395 were
> deliberately **left alone**, since they name the block and not the study. **A leftover grep after
> the rename shows every remaining `D390` belongs to master.** D391–D397 do not collide.
>
> **BOTH OF MASTER'S TWO `D390`s HAVE NOW MOVED OUT OF THE RESERVED BLOCK.** The D163 re-cost went
> `D389 → D390 → D400`. The **D280 overnight-gap check went `D390 → D402`** on 2026-09-09 — records,
> runner (`scripts/run_d402_stale_open_check.py`) and artifact (`data/d402_stale_open_check.json`),
> by the same count-asserted replacement, with the nine collision-history mentions of `D390` in this
> file deliberately left alone. **It was taken after checking `ls docs/decisions/`, which this file
> already warned is insufficient and will collide.** Commit hashes are historical and unchanged:
> pre-registration `6843a39`, result `c6c63f6`.

**THE ONE LINE: eight candidates, zero admitted, zero holdout reads, and the chain RETIRED by the
principal on 2026-09-09.** [D396](docs/decisions/D396-RETIREMENT-the-sign-sequence-chain.md) is the
retirement record and the place to start.

| | |
|---|---|
| **Retired 2026-09-09** | **D393** sign sequences (+ 6 addenda), **D394** exit rules, **D395** the CHOP cell |
| **How far it got** | `up_run_21` E1/cap 20 cleared **all four** nulls (B the binding one at **+0.91**, resolved ABOVE only at 4,000 draws) — and **never cleared H1**, whose best-of-10 floor was never computed |
| **The one cell that reached 1.00× coverage** | cap-20 CHOP, **net −0.44** — found by searching 36 cells, at a hold that was not the declared primary, whose own primary **failed the search floor by 22 SE**. Retired with the rest |
| **Books** | **unchanged.** S1, S2, neither at capital; prop book empty |

**The instruments are the durable output and they outlive the chain:**
`scripts/lag_audit.py` (the shared `[L]` audit, built because D391 shipped a look-ahead that cost
82% of its result) · `data/d392_atlas.json` + `run_d392_base_rate_atlas.py` (193 measured base-rate
cells; `lookup` **raises** outside the grid) · **the exact permutation floor** in
`run_d395_chop.py` (best-of-N for a cell picked from a grid — no independence assumption, 10,000
draws in 44 s; **should replace normal-approximation floors programme-wide**) ·
`scripts/ragged_sign_scores.py` (Axis I; `sign_flips_21` is the most orthogonal score measured,
max |ρ| 0.025) · the shard/merge pattern with one `item_at()` and `[SHARD]` bit-identity.

**Six findings worth carrying** (full list in D396 §2): base rates are large enough to look like
signals (price tercile **36.8 bp** for a *random* long) · **the edge lives where trading is
dearest**, measured three independent ways · a clairvoyant delisting filter would **lose** money ·
hit rate is immovable at **50.1–50.8%** · eleven observables all predict both tails equally · no
exit rule closes a cost gap (126 cells, best recovered 2.53 bp of 50.88).

**Open and NOT closed by the retirement:** `sign_flips_21` as an independent *input* (retired as a
signal, not as a variable) · `working/SLEEVE-VS-ALLOCATOR-PROPOSAL.md` (three questions) ·
`working/FINDINGS-52-corollary-NOTE.md` (six questions) · the FINDINGS §48 amendment draft ·
three atlas floor gaps (cap 5 both sides, cap 1 short) · a `docs/research/the-signal-hunt-part2.md`
§2a correction already made in place.

---

**Updated 2026-09-09.** **D365 → D401.** **Three** sessions on master, plus one on a branch: the
first spent the programme's first holdout read, ran D373 and audited the hurdles that judged it; the
second built and **retired the density line (D384 → D388)** and **answered the correlation floor
(D389)**; the third **priced the prop instrument end to end (D386)**, **settled the D383 debt by
running it**, **discharged R11's re-costing corollary (D400)**, and recorded the principal's
**closure of two avenues (D401)**. Everything below §7 is older strata, newest first, kept because
the traps in them still bite.

> ## ⚠ READ THIS BEFORE YOU PICK A DECISION NUMBER
>
> **`ls docs/decisions/` IS NOT SUFFICIENT AND WILL COLLIDE.** It happened **twice within the hour**
> on 2026-09-09 — the second time *while fixing the first*:
>
> 1. Two sessions both took **D389** — the D163 re-cost pre-registered 23:17 (`7d04812`), the
>    correlation floor 00:24 (`5bd7d97`). The re-cost had it first by commit time but was renumbered,
>    because the other had already propagated `D389 = correlation floor` into this file.
> 2. It was renumbered to **D390 — which was already RESERVED.** The `worktree-signal-hunt-part2`
>    branch reserved **D390–D399** at 2026-09-08 12:27 (`fb2af62`), after master took D380, D381 and
>    D382 out from under it twice. **That reservation is a commit message on another branch** —
>    invisible to `ls`, and invisible to `git log` run on master alone.
>
> **Both records were then moved clear of the block: the re-cost is `D400`, the closure `D401`.**
>
> **THE PROCEDURE IS THREE COMMANDS, NOT ONE:**
> ```
> git log --all --oneline | grep -iE "\bD<n>\b"    # usage on ANY branch
> git log --all --oneline | grep -i "RESERVE"      # reserved blocks
> git branch -a --format="%(refname:short) %(committerdate:relative)"  # who is live right now
> ```
> **D390–D399 belongs to `worktree-signal-hunt-part2`. Master takes D400 and upward.**

**This file had been stale since 2026-09-02** (D264→D284) and both `STACK.md` and the 2026-09-07
handoff said so in writing. It is current again as of this line.

---

## 0. THE ONE-LINE STATE, 2026-09-09

**THE MOMENTUM BOOK FAILED OUT OF SAMPLE AND WAS RETIRED. ITS SUCCESSOR WAS THE SAME BOOK, AND THE
COHORT — NOT THE SIGNAL — IS ~73–80% OF ITS EDGE. THE REMAINING ~27% IS A REAL ENTRY-TIMING EFFECT
WORTH AT MOST HALF A ROUND TRIP. HOLDOUT #1 IS SPENT; HOLDOUT #2 IS BUILT AND UNSPENT. BOTH BOOKS ARE
UNCHANGED.**

**AS OF 2026-09-09: the density line is RETIRED — the object works, the conditioner is inert. The
0.44 correlation floor is ONE unidentified factor and none of the four named candidates explains it.
D383 IS RUN AND THE QUEUE IS NOW EMPTY — nothing is pre-registered and unrun. The single highest-value
item in the programme — D336's quoted-spread pull — is BLOCKED ON THE PRINCIPAL'S TWS SESSION, and it
decides whether the incumbent book is positive at all.**

**AND THE PROP INSTRUMENT IS NOW PRICED, WHICH IT NEVER WAS. [D386](docs/decisions/D386-the-prop-account-is-worth-its-buffer.md):
at zero edge a funded account is worth EXACTLY ITS DRAWDOWN BUFFER — you cannot extract more in
expectation than the amount they let you lose — and the whole question reduces to one
leverage-invariant number, CALMAR ≥ 18.9 ON OPEN EQUITY. The best audited intraday CME programme in a
199-programme database is 1.07. Twenty-two research lanes found ONE prop-eligible candidate, with a
known contamination risk. THE PROP TRACK IS NOT BLOCKED ON VALUATION ANY MORE; IT IS BLOCKED ON
HAVING A STRATEGY, and the shape it needs is now known.**

| | |
|---|---|
| **Personal book** — `docs/BOOK.md` | **S1, S2 only, neither at capital** |
| **Prop book** — `docs/BOOK_PROP.md` | **none**, and the candidate list C1–C4 is **exhausted** (D379 §6) |
| **Holdout reads spent, programme total** | **1** (D371, 2026-09-07) |
| **Retired 2026-09-07** | **S6** (nine-condition gate), **C9** (252-bar high alone) |
| **The winners'-dip avenue** | **RETIRED 2026-09-08, then REOPENED NARROWLY** for one test. **D378's gate PASSED** so the abandon condition never fired; **D380 then closed the exit half — no overlay beats not cutting.** The timing picture is complete: **the entry day carries information, the exit does not, and neither is large enough to matter after cost.** **STATUS IS THE PRINCIPAL'S.** [FINDINGS §52](docs/FINDINGS.md) |
| **Hurdles retired or replaced** | **H4 → H4′** (D374) · **1d → 1d′** (D376) · **hedge H0 → H1** for future studies (D377) · **P1 restated as a SIZING RULE, not a filter** (D375 → R11, 2026-09-08) |
| **THE DENSITY LINE — RETIRED 2026-09-09 by the principal (R15)** | D384 -> D388, five studies. **The OBJECT works** (TV 0.18-0.51, ratio CV 0.51-1.31, 2-3 modes, causal, proved). **The CONDITIONER is inert**: beats the path-shuffle null 34/36 at p to 7.2e-11, beats the ROTATED-DENSITY null 0/36, and corr(density shape, edge) is -0.027 across all 36 cells - positive in 10/36, below chance. Net negative in all 36. [FINDINGS 56](docs/FINDINGS.md) |
| **What the density line cost, and what survives** | **~4.5 h of compute, three of five studies measuring the wrong thing** (D384 wrong statistic; D385 flat object; D387 flat on half its universe with mismatched gates). Survives: the proved construction, `f_hat` constant between events under plain decay (24x), sigma-unit thresholds (rarity spread 4.37x -> 1.37x), and **beating a path-shuffle null is nearly free - the persistent-selector control is the test** |
| **ONE PRE-REGISTRATION IS AWAITING A RUNNER** | **D383** — the time-series structure screen at 15 minutes (`af91504`, amended `cb864cb`). Fixture gated `3c9d57c`. **The runner does not exist and was deliberately not built.** |

**For D285 → D364 read [`docs/STACK.md`](docs/STACK.md) §0 and §§32–42**, not this file. That is the
layer-by-layer statement of what the stack earns once costed, and its §7 records what earlier
versions of it got wrong. This section deliberately does not restate it.

**One defect to fix in the truth file:** `docs/FINDINGS.md` has **two sections numbered §51** (the
holdout read, and equal-weight sizing). The new section was added as §52; the collision is upstream
and untouched.

---

## 0a. THE HOLDOUT LEDGER — READ BEFORE ANYTHING ELSE

| fixture | slice of the pinned permutation | names | state |
|---|---|---:|---|
| mining prefix | `order[:3400]` | — | spent many times over; free to mine further (see the ruling below) |
| `us_shorts_daily_holdout.csv.gz` | `order[3400:5100]` | 803 | **SPENT 2026-09-07 (D371, momentum). READ AGAIN 2026-09-10 (D430, the second-zone line) under the principal's ruling that a holdout spent by an unrelated strategy is unseen by a new line.** Spent for both lines. |
| `us_shorts_daily_holdout2.csv.gz` | `order[5100:6300]` | **576** | **SPENT 2026-09-10 (D433, the second-zone line).** 1,532,631 rows, dead share 32.6%, gates clean; unseen by every OTHER line — the principal's per-line ruling applies |
| remaining unfetched | `order[6300:]` | **2,301** | never fetched, never scored |

The permutation is deterministic — alphabetical sort, one shuffle at `POOL_SEED = 20260828` — so any
further slice can be cut without re-picking anything.

**The 5,201 figure in the 2026-09-07 handoff was wrong.** It counted from the end of the *mining*
prefix and therefore included holdout #1 itself. The true remainder at that moment was **3,501**.
Corrected here; verified directly against `data/raw/alphavantage/daily_adjusted/_pool.json`.

**The guard is default-deny.** `run_d365_momentum_buffer.py` installs an audit hook refusing any path
containing "holdout", metadata included; an authorised process calls `V65.allow_holdout(why)`, which
prints loudly and logs every holdout file opened. CPython has no `removeaudithook`, so this is the
only way through. **Building and rehearsing on a holdout is fine. Reading is not, without explicit
specific authorisation from the principal.**

**Breadth is the unsolved problem with holdout #2.** Panel coverage per bar: mining **1,008**,
holdout #1 **534**, holdout #2 **369**. On D371's stricter study-eligibility mask holdout #1 gave
369, so holdout #2 should land near **255** — about **0.69×** holdout #1's breadth. D371 already
failed a breadth hurdle. **Decide what breadth a read needs before spending this fixture, not
after.**

---

## 0b. THE PRINCIPAL'S RULING ON MINING SPENT DATA, 2026-09-07

*Quoted because it governs every study that follows:* a **brand-new construction** may mine the
already-spent in-sample fixture, **provided nothing crosses into a holdout**. The contamination cost
rises slowly on its own as a share, and is accepted for now. D373 was run under this ruling and
nothing crossed.

---

## 0c. D373 — the last study, and what it settled

**[D373](docs/decisions/D373-the-winners-dip-long-and-the-median-criterion.md)** pre-registered
(`aa7bc2f`, amended `462f894`), **[RESULT](docs/decisions/D373-RESULT-the-winners-dip-is-the-retired-book-and-one-GME-trade.md)**
(`9162a64`). The winners' dip long: a fresh `rev_5` dip inside the `mom_252_21` **top** decile,
entered long, 40-bar cap. 3,932 trades, 796 names.

| | | |
|---|---|---|
| **H1** signal vs A′/B/B_c/C | **PASS** | +160.55 vs p95s +105.76 / +51.92 / **+155.60** / +52.72 |
| **H2** `mean > median > 0` | **FAIL** | median **+51.55**, below A′'s p95 +81.42 and B_c's +87.43 |
| **H3** era 1 standalone | **FAIL** | +16.86 vs p95s +64.60 / +77.24 |
| **H4** breadth | **FAIL** | 18 of 796 names = **2.26%** to half the P&L; bar 10% |
| **H5** capturability | **PASS** | open-entry t 5.11, retention 98.7% |
| **H7** independence | **FAIL** | **ρ = 0.9346** to the retired D365 book |

**Three things from it that outlive it:**

1. **`B_c` is the control that matters and its p50 is +126.54.** Most of the observed +160.55 is
   available to a random name drawn from the same momentum decile on the same day. **Any study
   selecting inside a cohort must null against a same-day same-cohort swap, or it is measuring
   cohort membership.**
2. **The H1 margin was one trade wide.** Top trade: **GME, entered 2021-01-04 at $17.25, held 40
   bars, +40,029 bp — 6.34% of the ledger.** Drop it and the mean falls to +150.41, **below B_c's
   p95**. So does dropping all ten GME trades, and so does dropping Nov-2020→Mar-2021 entirely.
   `scripts/d373_posthoc_probes.py`, post-hoc and labelled so.
3. **`mean > median > 0` IS CONFOUNDED WITH HOLDING PERIOD.** Re-cutting D365's *own* stored paths:
   PASS at 20/40/60 bars, FAIL at 100 and at its native ~99. D373 and D365 **agree** at equal
   segmentation. The mechanism is arithmetic — summing fat-tailed returns over a longer window lifts
   the mean and drops the median. **Within-study null comparisons hold segmentation fixed on both
   sides and stay fair; cross-construction median comparison does not.**
   `scripts/d373_segmentation_probe.py`, `docs/decisions/D373-RESULT-*.md` §3a.

---

## 0c2. D374 — the breadth hurdle was unreachable, and H4 is retired

**[D374](docs/decisions/D374-is-the-breadth-hurdle-reachable.md)** pre-registered (`4c0816c`),
runner (`c2f7887`), **[RESULT](docs/decisions/D374-RESULT-the-breadth-bar-was-unreachable-and-it-failed-the-most-diversified-book-in-the-null.md)**
(`520dd40`). A METHODOLOGY study: it adjudicates a hurdle, not a strategy, and adds no looks to any
multiplicity ledger.

**Across 4,952 defined null draws in three arms, the most diversified random book reached 2.98%. The
median reached 0.63%. The bar was 10%.** D373's book, at 2.2613%, sits at the **100.00th percentile
of its own nulls** — above A′'s *maximum*, with 0 of 1,971 A′ draws and 0 of 981 B draws as
diversified. A′ holds the name set and each name's trade count exactly fixed, so this is what a
fat-tailed return distribution does to any ~800-name book here; selection has nothing to do with it.

**H4 IS RETIRED. Its replacement, in force for all future studies:**

> **H4′** — `names_to_half_share` at or above the **p05 of A′ computed on that study's own ledger**,
> with the degenerate-draw count reported beside it. **The threshold comes from the study's own null,
> never fixed in advance of the universe.**
>
> **The top-1 and top-5 name-share bars are DROPPED, not re-thresholded.** The statistic is unbounded
> above: **233 of 1,971 A′ draws (11.8%) have a top-5 share over 100%**, with maxima to 37,546%,
> because a small positive denominator explodes it while it stays technically "defined". D371's
> real-world 142% was not exceptional. Any percentile of it is contaminated.

**Two lessons wider than this hurdle:**

1. **"Has anything ever passed this?" is a cheap and powerful test, and it has not been run on the
   rest of the hurdle set.** H4 had never once been cleared, by anything, and nobody had checked
   whether it could be.
2. **A threshold fitted to one observed failure carries no information about the next book.** D373 §5
   said in writing that H4's bars were "calibrated to exclude the shape that just failed". That was
   honest about provenance and fatal as evidence.

---

## 0c3. D375 → D377 — the hurdle audit and what it turned up

**[D375](docs/decisions/D375-the-hurdle-audit-the-stage-one-gates-are-sound-and-hurdle-P-is-half-untested.md)
(`1732fd0`), a REVIEW.** I predicted H4's disease would be widespread. **It is not**, and the reason
is structural: most stage-1 gates are built on **t-statistics, whose null centre is zero by
construction**, so `t ≥ 2` means the same thing in every universe and cannot be unreachable. **H4 was
the only threshold nothing had ever cleared.** What the audit did find:

- **Three of hurdle P's six thresholds have never been computed on anything** — **P3, P4, P5**. D266
  says outright P4 is *"not calculable from these artifacts"*. Under [R6](docs/RULES.md) the prop
  track carries three hurdles nobody has run.
- **P1 cannot fail.** It is applied by scaling until drawdown reaches 4%, so it is a **sizing rule
  that converts to a return penalty**, not a filter. R11's table lists it as one. **Recommended
  restatement, not yet made.**
- **P5 is the only surviving threshold with H4's disease** — a ratio whose denominator
  (trailing-year profit) **can cross zero**.

**[D376](docs/decisions/D376-RESULT-two-unrelated-books-here-correlate-at-0.48-and-two-cohort-books-at-0.92.md)
(`ca8a89c`) — the correlation floor.** 500 draws, 280,625 pairs.

| | p50 | p95 |
|---|---:|---:|
| A′ identical name set | +0.448 | +0.485 |
| **B unrelated books** | **+0.476** | **+0.526** |
| B_c same cohort | **+0.923** | +0.930 |

- **It is TIME, not names.** A′ books hold the *identical* names and correlate **less** than B books,
  which hold different names on the **same days**. The residual factor is a **per-bar** effect.
- **Gate 1d measures POOL OVERLAP, not independence** — same pool ≈ 0.42–0.53, different pools ≈ 0 or
  negative (the observed book sits at **−0.091** against B draws), same cohort ≈ 0.92. **1d′ therefore
  SCOPES: compare to the p95 of the candidate's OWN pool, and NAME THE POOL.** A raw correlation
  without it is uninterpretable.
- **[CLU]** — cluster the bootstrap on **books**, not pairs. 280,625 pairs came from 1,250 books.

**[D377](docs/decisions/D377-RESULT-the-beta-hedge-is-adopted-and-it-fixes-seven-percent-of-the-problem.md)
(`cd97e4f`) — the hedge.** The incumbent assumed **beta exactly 1 for every name**; a lagged
`roll_beta(63, 21)` existed unused.

| hedge | B p50 | M1 | gross/trade | kept | M2 |
|---|---:|:--|---:|---:|:--|
| H0 unit market | +0.4728 | baseline | +160.55 | 100% | baseline |
| **H1 per-name beta — ADOPTED** | **+0.4404** | PASS (10.6 SE) | +156.57 | 97.5% | PASS |
| H2 cohort | +0.3242 | PASS (38.8 SE) | **+34.08** | **21.2%** | **FAIL** |
| H3 price decile | +0.4439 | PASS (9.7 SE) | +160.47 | 99.9% | PASS |

- **H1 binds for future studies. It fixes ~7% of the problem** — the floor falls 0.473 → 0.440,
  decisive but small. **Past records stay on H0 and must be labelled**; re-basing them is the
  principal's call and is not obviously worth it.
- **The common factor is mostly NOT unhedged beta.** Untested and now the open question: **shared
  slot mechanics, equal-weighting, the eligibility floor itself.**
- **H1 and H3 are a near-tie and whether they are complementary was NOT tested** — a combined hedge
  was not in the pre-registered grid.

---

## 0c4. D378 — the entry day DOES matter, and D379 — the prop account is a barrier option

**[D378](docs/decisions/D378-RESULT-the-entry-day-does-matter-and-it-survives-losing-its-best-trade.md)
(`7117478`).** The one test the narrow reopening authorised. **A′_c**: for each observed entry, a
replacement bar drawn from the days **that same name** was eligible **and** in the top decile — name,
cohort and per-name count fixed, **only the day moves**. 2,000 draws.

| | | |
|---|---|---|
| **T1** | mean per trade > A′_c p95 | **PASS** — +160.55 vs +144.57, **+26.9 SE** |
| **T2** | *reported* — the **median** | **FAIL** — +51.55 vs +64.00 |
| **T3** | **GATE** — largest trade removed | **PASS** — **+150.41**, **+9.8 SE** |

- **A′_c's centre is +116.91**, so **73% is still cohort** — a third independent measurement beside
  D373's 79% and D377's 79%.
- **The front-loading is the dip's.** Observed bp/bar halves across caps 5→60 (7.82 → 3.94) while
  A′_c's barely moves (2.01 → 2.75). At cap 5 the observed runs at **3.9×** the control's rate.
- **The gain is in the mean, not the median.** Timing makes good trades bigger; it does not lift the
  typical trade. **Win rate is the median's neighbour — nothing shows a better one is available.**
- **Cost decides it and cost is unresolved:** the increment is **0.19–0.47× a round trip under PUB**,
  **0.50–1.21× under PB**. Which convention is right is **D336's quoted-spread pull**, which needs
  the principal's TWS session.
- **FINDINGS §52's corollary was amended** — it called the selector "a rounding error on a factor
  exposure" and that is withdrawn. **A real effect small relative to cost is a small real effect.**

**[D379](docs/decisions/D379-the-prop-account-is-a-down-and-out-call-and-hurdle-P-has-no-objective-function.md)
(`861ec8f`, amended `7b4e58f`) — FRAMING, from a session other than the one that ran D373–D378.** No
measurement on any fixture; one toy Monte Carlo, labelled as illustration and deliberately not
committed to `data/`.

- **A funded prop account is a down-and-out call**, component for component: fee = premium, P&L =
  underlying, **drawdown limit = knock-out barrier monitored continuously on OPEN equity — which is
  P1 exactly.** Accounts are purchasable in quantity, so `fee / P(pass)` is the acquisition cost of
  one funded account.
- **Hurdle P has six screens and no objective function behind them.** It admits candidates; it never
  ranks them. `E[payout]` would.
- **Measured consequence:** at zero edge on a Topstep-like eval, a **static** floor gives the
  optional-stopping **40.0%** pass rate and the **trailing** floor **26.5%** — the ratchet costs ~13
  points.
- **It changes nothing yet.** No candidate reopened, no threshold loosened, and its own bound is
  stated: *"this is a valuation framework, not an edge… the prop candidate list is exhausted, so
  there is currently nothing to value."*

---

## 0d. WHAT IS LIVE NOW, RANKED

**RE-RANKED 2026-09-09 (later), after D383 was run and the prop instrument was priced. THE QUEUE IS
EMPTY: nothing is pre-registered and unrun.** What follows is candidates, not commitments.

> ### 0d0. THE NEGATIVE-SPACE SCAN AND ITS SEVEN EXTERNAL BRIEFS, 2026-09-09 — **ELEVEN LEADS, THREE STILL STANDING AFTER THE EVIDENCE, AND THREE METHOD FINDINGS ALONGSIDE THEM**
>
> **THIS WAS COMMISSIONED AS A LEAD SCAN AND ITS DELIVERABLE IS LEADS.** An earlier version of
> this section led with *"no strategy was found"*, which measured a lead scan against a bar
> nobody set for it — a lead that survives a smell test and a costed literature check **is** the
> product here. **What follows is the inventory; §0d0a ranks it.** Testing is a separate act
> under R8 and none has occurred.
>
> **[`docs/research/the-negative-space-scan.md`](docs/research/the-negative-space-scan.md)**
> (`bbc2790`, consolidated `00eaccb`). A scan of the categories the record had **never** put in a
> runner, scored on seven axes drawn from what has actually killed studies here. **Then seven
> agents researched the published literature, one per lead, briefs in `working/leads/` under that
> directory's quarantine contract.**
>
> **Status of every item below: a LEAD.** None has been tested — that is R8's separate act and it
> has not happened. Both books are unchanged.
>
> ### 0d0a. THE INVENTORY — eleven leads, by category
>
> **REGIME DETECTORS**
> 1. **Cross-asset state** — `log(HYG/IEF)`, `log(IEF/SHY)`, defensive-vs-cyclical, as a
>    market-level time gate. **The only gate this programme could build that is not a function of
>    the equity universe it trades.** → [D404](docs/decisions/D404-the-cross-asset-state.md).
>    **STANDING**, with the horizon in doubt.
> 2. **Even-week FOMC cycle** (Cieslak–Morse–Vissing-Jorgensen, JF 2019) — surfaced by the K1
>    brief as **better founded than the pre-FOMC drift it was sent to check**: far more events,
>    causal evidence, no published OOS failure found. **STANDING, and untouched by the K1 verdict.**
> 3. Turn-of-month / day-of-week / pre-FOMC window. **FELL** — location, not decay: on FOMC days
>    the CAPM works, α insignificant, and equal weighting *shrinks* it (36→25→20 bp).
>
> **CROSS-SECTIONAL SIGNALS**
> 4. **Industry-relative reversal in liquid names + a low-volatility screen** — +0.31%/mo,
>    t=2.73, VW large-cap. **Two agents that never communicated converged on it** from different
>    literatures. **STANDING and it is the strongest of the eleven** — but it is *someone else's
>    published result*, never tested here, and in both accounts **the cost filter does the
>    rescuing, not the residualisation.**
> 5. **Combining the 16 OHLC terms** — equal-weight cross-sectional rank average, every sign
>    declared in writing, floored against a sign-fitting null. **ROSE FROM LAST TO FIRST** of the
>    unregistered leads once §59 showed our own reasoning against it was backwards.
> 6. Cluster-residual reversal. **FELL** — net moves −1.28 → −0.80%/mo, still 80 bp under water,
>    and correlation clusters give a 0.02 out-of-sample spread in small caps, which is our case.
> 7. Closed-end fund discount. **FELL** — Flynn ran the exact hedged trade on 462 CEFs, zero
>    significant alphas, and the edge is front-loaded into month one, killing the "slow" thesis.
> 8. Lead–lag between size cohorts. **DEAD** — measured into a decile averaging $47m cap.
> 9. **Geographic lead–lag** (co-HQ, different sectors), 5–6%/yr, **explicitly unrelated to size,
>    volume and coverage** — the one liquid-name variant the X2 brief found real. **STANDING as a
>    lead**, monthly, sample ends 2013, no cost test in the paper.
>
> **INDICATORS / DATA ROUTES**
> 10. Short interest and days-to-cover. **FELL** — borrow fee takes 162 anomalies from +0.14%/mo
>     gross to −0.01% net, and free FINRA exchange-listed data starts June 2021.
> 11. **FINRA daily short-sale volume + the SEC FTD file** — the replacement route the N1 brief
>     found: one-day lag, point-in-time, consolidated from 2018-08, and **the FTD file carries
>     CUSIP so it doubles as a delisted-symbol crosswalk.** **STANDING as an input, not a signal.**
>
> **Ranked for a next step: #4, then #5, then #1.**
>
> **ALL ELEVEN ARE RECORDED AS LEADS WITH FULL ANATOMY** — the quantity, why it is not in the
> catalogue, the mechanism, the data, **the premise number that kills it**, and the honest risk —
> in [the scan record](docs/research/the-negative-space-scan.md) **§§3–7** for the original seven
> and **§9b** for the four the briefs surfaced. **§8's scored table carries all eleven**, with the
> seven axis scores **deliberately left unrevised** so the scan's own calibration can be audited
> against what the literature said. **That audit is unflattering and is recorded there: the score
> did not predict the outcome** — C1 scored lowest of seven and now ranks first, while K1 and N1
> scored 17 and both fell hard. **The axis that failed was `KILL`, and it was measuring my
> knowledge rather than the lead.**
>
> **The three findings that outlive the scan, and each was RE-MEASURED here rather than quoted:**
>
> 1. **[FINDINGS §59](docs/FINDINGS.md) — a best-of-N floor prices SELECTION and is blind to
>    SIGN-FITTING.** At k=16 a composite of **pure noise** clears the selection floor by **+1.28**
>    (2.95 vs 4.23). **Pre-declaring every sign in writing is worth a factor of ~2 in the hurdle
>    (4.23 → 1.65) for no computation** — the cheapest hurdle reduction on offer here. The D395
>    floor is *not* wrong; it must be **extended** wherever a construction orients its own
>    components in sample.
> 2. **[FINDINGS §60](docs/FINDINGS.md) — `etf_wide_daily_raw` IS NOT AN ETF FIXTURE.** **≥27.2%
>    closed-end funds** and **23 of its 24 deaths are fund wind-ups**, on a fixture **D382, D384
>    and D385 already ran on**. Their P&L used total return and is unaffected; what is affected is
>    anything reading `closes` as a **level**. **A metadata correction and any re-read is the
>    principal's call** — nothing was edited.
> 3. **D280's own gloss was backwards.** Orthogonality **multiplies** detectability by `√k`
>    (3.7–4.0× for the OHLC family against 1.69× for the nine price scores). The empirical part of
>    D280 stands; **the inference that independence makes combination hopeless is withdrawn.**
>
> **The leads, after the evidence.** **C1** (combining the 16 OHLC terms) **rose from last to
> first** — it now has a nameable form and a concrete hurdle. **X2 is dead** on measurement.
> **K1, N1, V1 and X1 all fell hard**, each on a specific published quantity, not a vibe.
> **R1 is [D404](docs/decisions/D404-the-cross-asset-state.md), pre-registered and amended.**
>
> **One construction surfaced that is NOT ours and has never been tested here:** two agents that
> never communicated converged on **industry-relative reversal in liquid names with a
> low-volatility screen** (+0.31%/mo, t=2.73, value-weighted, large-cap) as the only cost-surviving
> thing in the area — **and in both accounts it is the COST FILTER doing the rescuing, not the
> residualisation.** It would need its own pre-registration.
>
> **The quarantine rule paid for itself immediately: the brief that read most confidently (R1's)
> was the one whose two headline construction claims did NOT survive measurement.** Treat an
> enthusiastic brief with more suspicion than a damning one.

> ### 0d0b. ROUND 2 — SIX NEW TERRITORIES, ALL SIX BRIEFS IN, 2026-09-09
>
> **[`docs/research/the-forced-seller-and-the-cost-wall.md`](docs/research/the-forced-seller-and-the-cost-wall.md)**
> (`335fcc0`, completed `20a083a`). Territories and the exclusion list that kept round 2 off round
> 1's ground: [`working/leads2/README.md`](working/leads2/README.md) (`f31535d`).
>
> **THE SAME SHAPE AS ROUND 1: the most valuable returns are not leads.** Four of the six most
> consequential findings are method, data or cost.
>
> 1. **THE HOUSE SPREAD ESTIMATOR IS BIASED THE WRONG WAY.** `CLAUDE.md` mandates Corwin–Schultz;
>    **Ardia–Guidotti–Kroencke (JFE 2024) find CS UNDERESTIMATES effective spreads for small,
>    illiquid stocks** — our tail. **D285's 33.8 bp/side may be a FLOOR, not an estimate**, which
>    would make every breakeven in the record more lenient than it looks. **EDGE is a closed-form
>    drop-in on the same OHLC inputs (`bidask` on PyPI). Recompute D285 under EDGE FIRST — it sets
>    the SIGN of every cost conclusion downstream.** Not computed; re-opening D285 is the
>    principal's call.
> 2. **A CLOSE-DECIDED BOOK CANNOT FILL AT THAT CLOSE.** NYSE MOC/LOC hard cut-off **3:50 pm**
>    (Nasdaq MOC 3:55, LOC 3:58). A constraint on construction, not a preference.
> 3. **THE SPIN-OFF DEFECT HAS A NAMED FIX.** The correct adjustment is a multiplicative step on
>    all PRIOR bars, `f = (P_cum − r·P_child)/P_cum` — **date-dependent, which is exactly why a
>    scalar `raw_price_factor` cannot fix it**; the child has no pre-WI history at all. **Vendors
>    log spin-off factors in the SPLIT table, so a distribution ratio read as a split ratio shifts
>    the series by a clean integer — that is the 5× shape.**
> 4. **THE SURVIVORS-ONLY IDENTIFIER TRAP, TWICE.** `company_tickers.json` and Wikipedia's
>    `List of S&P 500 companies` are both survivors-only. **The free fix: `ISSUERTRADINGSYMBOL` is
>    NOT NULL inside every Form 4**, so dead names carry their own point-in-time ticker forever.
>    Join on `(ticker, date-in-listing-interval)`.
>
> **The four signal territories, none closed.** `F1` index reconstitution — **my premise was
> INVERTED**: large-and-liquid is where the effect is dead (S&P 500 adds 7.4% → 0.3%), and where it
> survives (SmallCap 600, MidCap, Russell 2000) is where our per-share cost is worst; **but the
> 500's zero is a composition artefact — direct adds still ran +5.40%**, and **deletions of names
> that DELIST are unpublished because every study drops them, which a dead-inclusive fixture is the
> right instrument for.** `F2` insiders — data excellent, **no cost-honest post-2010 survival**;
> the one positive assumes 10 bp/side against our measured 33.8. `F3` earnings — PEAD dead outside
> microcaps since 2006, premium's published US window **ends 2004**, **but its timing split (34.6%
> pre-open / 45.4% post-close, four corroborating sources) independently corroborates D280's
> overnight finding** — and carries a day-0 lag hazard `[L]`. `F6` supply events — **three of four
> families resolve overnight, so daily bars are a bar late by construction**; only buyback
> *execution*, as a **state**, is recommended.
>
> **`F5` cost: 0.5–1.5 bp/side saveable, not 5.** Published price-improvement numbers **do not
> reach an auction-only book** — IBKR takes no order-flow payment on On Open/On Close and the
> auction print is a full half-spread, **so our cost model is CORRECT there**. One actionable
> change: **Fixed → Tiered**, and it corrects a recorded number — **the minimum binds on a SHARE
> COUNT (200 Fixed, 100 Tiered), not on "$2,100 notional"**. **The 1.92 bp intraday cell still
> loses at a zero spread.** **Dated freebie: IBKR's first amended-Rule-605 broker-level report,
> with E/Q by order size, is due published before end-September 2026.**
>
> **TWO OF MY OWN COMMISSIONING PREMISES WERE WRONG**: the 2023 granular buyback rule was **vacated
> by the Fifth Circuit 2023-12-19** before producing data (our span is Item 703 — monthly, HTML,
> untagged, 40–45 days late), and index flow does not live in large liquid names.
>
> ### 0d0c. ROUND 3 — PREPARED, NOT COMMISSIONED
>
> **[`working/leads3/README.md`](working/leads3/README.md)** (`2e89d37`, withdrawal `4f3e2e3`).
> Six lanes written up; **no agent dispatched**, deliberately — round 2's returns had to extend the
> exclusion list first. **`G1`** fund/ETF flows as the forced seller · **`G2`** the death process,
> which [`FINDINGS.md`](docs/FINDINGS.md) §60's own rule demands and which `F1` independently
> pointed at · **`G3`** halts/LULD, where D343 met the event as 4.4% of D342's P&L and excluded it
> as hygiene · **`G4`** 13D/13G · **`G5`** the revenue side of a long book · **`G6`** documented
> defects in data we own. **`G2` and `G3` are route (b)** — the first round to ask it; round 2's
> four signal lanes were all route (a), which was my omission.
>
> ### 0d1. D404 — THE CROSS-ASSET STATE, PRE-REGISTERED AND AMENDED, RUNNER DOES NOT EXIST
>
> **[D404](docs/decisions/D404-the-cross-asset-state.md)** (`fd4275e`, amended `c88673a`). All 52
> catalogue scores are functions of one name's own OHLCV; the one exception builds its market
> return from the panel's own cross-section. **No study has ever gated an equity book on another
> asset class.** The two fixtures' grids are **identical bar for bar** (4,187 dates), so the join
> needs no fetch — **the whole of the new code is the `raw` array.**
>
> **Its second question is why it exists:** D389's factor is **98.5% unexplained in arm B** and all
> four tested candidates were *internal* to the book's machinery. `data/d376_series.npz` already
> holds the 500-book matrix on the same grid, so testing a market-level state against it is nearly
> free.
>
> **§12a amendment, before the runner exists.** One alleged defect **false** (drift −0.92%/yr, not
> 2–5%, and the imbalance runs the other way), one **confirmed** (`(XLU+XLP)/(XLY+XLK)` is a sum of
> share prices; a synthetic split moves it 0.338 log units), and **one found that neither party
> had: a trailing-median rule on a TRENDING series is a TREND RULE, not a state classifier.**
> `DEFENSIVE` sits on one side 71% of the time and equal-weighting does not fix it. **A new `[BAL]`
> assertion fails any state outside 40–60%; `DEFENSIVE` fails it today.**
>
> **Recorded, not adopted:** the literature places credit/curve predictability at **quarters to
> years**, not the 20 days D404 inherited. None of those papers has been read here. **The runner
> must report the whole horizon curve h ∈ {5…252}, and if h=20 is the PEAK that is an overfitting
> flag, not a confirmation.**

**TWO AVENUES WERE CLOSED BY THE PRINCIPAL ON 2026-09-09 —
[D401](docs/decisions/D401-the-principal-closes-the-winners-dip-and-the-15m-structure-avenues.md):
the WINNERS' DIP and the 15-MINUTE TIME-SERIES STRUCTURE SCREEN.** Both are shut and neither will be
reopened. **What outlives them and must not be closed with them:** D378's entry-timing finding stands
as truth (T1 at **+26.9 SE**, largest-trade-removed gate at **+9.8 SE**); D383's **`n_eff` instruments
= 2.17 of 57 at 15 minutes** is a property of the universe and constrains any future intraday design;
and D383's **bp/bar RISES with hold** at 15m, opposite to daily, so a successor assuming daily
front-loading transfers would be wrong. D383's 111 uncorrected-p95 survivors — a volatility-timing
tilt with an undeclared direction — remain **recorded and unclaimed**, and closing the avenue does not
license mining them without a fresh pre-registration.

**ONE decision remains the principal's and blocks nothing else:** whether to **re-base past records**
onto D377's H1 hedge (D377 §4 argues not — the benefit is 0.032 on a 0.47 floor).

1. ~~D383 is a debt~~ — **SETTLED. [D383 RESULT](docs/decisions/D383-RESULT-the-time-series-screen-clears-nothing-and-its-ten-passes-are-buy-and-hold.md)
   (`c5dc05a`). 0 OF 572 CELLS CLEAR**, and the best cell at every hold sits **−0.06 to −0.95 SE of
   the floor's own CENTRE** — on the median, not near the bar. **§8's abandon condition is met; the
   close is the principal's.**
   - **THE PRE-REGISTRATION CAUGHT EXACTLY WHAT IT WAS WRITTEN FOR.** Ten cells clear on the primary
     PER-TRADE statistic and **all ten are buy-and-hold** — hold 78, exposure 1.000, 57 trades on 57
     names, median run **37,643 of 37,648** available bars, **`n_eff` trades = 1**, excess over B&H at
     matched exposure **0.00%**. That is the confound §5.1 nominated bp-per-bar to catch: **48 of 143
     hold-78 cells run >10× nominal against 0 of 143 at hold 26**, the hold nominated primary in
     advance. Choosing the primary statistic *and* the primary hold before seeing anything is what
     separated the artefact from the result.
   - **`n_eff` INSTRUMENTS = 2.17 OF 57 AT 15 MINUTES** — first measurement at this frequency, and it
     confirms FINDINGS §4's ~2.2 daily figure. **26× more sampling buys no breadth.** This constrains
     every intraday study this programme might design.
   - **Q3 falsified in an interesting direction: bp/bar RISES with hold at 15m** — the edge is **not**
     front-loaded, opposite to D378 daily. Q2 also fell (32 interior humps, not flat).
   - Recorded but **not claimed**: 111 of 572 beat their own *uncorrected* p95, and at the primary hold
     they are one coherent family — the low tail of `park_vol_21` / `gk_minus_cc` / `range_frac`, a
     volatility-timing tilt with an undeclared direction and confounded with spread.

1b. **THE PROP INSTRUMENT IS PRICED — [D386](docs/decisions/D386-the-prop-account-is-worth-its-buffer.md),
   22 lanes, `docs/research/Prop-Firm-080926/`.** Read
   [00-SYNTHESIS](docs/research/Prop-Firm-080926/00-SYNTHESIS.md),
   [23-method-lessons](docs/research/Prop-Firm-080926/23-method-lessons.md) and
   [24-candidate-ledger-both-books](docs/research/Prop-Firm-080926/24-candidate-ledger-both-books.md).
   - **At zero edge `E[extracted] = the drawdown buffer`, exactly** (optional stopping), so **the
     payout ladder is decoration** and **you cannot extract more in expectation than the amount they
     let you lose**. **94.7% of evaluations return exactly $0.**
   - **The whole question reduces to CALMAR ≥ 18.9 ON OPEN EQUITY**, leverage-invariant — verified on
     one manager's own 1× and 1.5× versions of the same book. **Best audited intraday CME programme:
     1.07. Best in a 199-programme database: 5.88.**
   - **A Calmar above 18 is a property of RECORD LENGTH, not strategy** — every Collective2 system ≥18
     is under 370 days old, zero of 37 older than two years. **That is a screening rule for both books.**
   - **The scissors close on LONG WINDOWS, not small edges.** Every rejection is a *size* rejection;
     cost is 15–20% of gross and never binding. **The binding variable is the hold.**
   - **D379 gains an uncomputed term**: the barrier is administered against a market that **can suspend
     your exit** (CME Velocity Logic halts on a rolling-millisecond move), and a floor on open equity
     keeps moving through those windows.
   - **The one quantity nobody publishes, confirmed five independent ways: MAE within the holding
     window, on open equity.** Absent from the literature, the code, the published drawdowns, the best
     retail record, and every verified CTA database.

1c. **R11's RE-COSTING COROLLARY IS DISCHARGED FOR ONE CONSTRUCTION — [D400](docs/decisions/D400-RESULT-the-D163-recost.md)
   (`7e39fe3`, renumbered D389 -> D390 -> D400).** D163's *"~315% of capital a year in fees"* is a **crypto taker
   number and is wrong by ~400×** at futures commission (0.786%/yr) — **but the closure survives on
   SIGNAL, not cost.** Gross first: BTC Design B at 15m is **−1.4 bp/trade at the 2.4th percentile of
   its own null**, below its p05. **Left to the principal: the 30m–2h band**, where cost moves three
   rungs per symbol from ruin to profit and the nulls disagree (ETH 1h clears at 96.4, BTC 1h fails at
   79.8, both fail at 2h). **R11 itself was NOT edited** — a standing-rule change is the principal's.

2. **D336's quoted-spread pull — the highest-value item in the programme, and it needs the principal's TWS
   session.** D378 put the entry-timing increment at **0.19–0.47× a round trip under PUB** and
   **0.50–1.21× under PB**. **The same measurement decides whether that effect is deployable and
   whether the incumbent book is positive at all** (D332: PUB post-D333 is −12.68 bp/bar). Nothing
   else on this list changes as many conclusions.
3. ~~Where does the remaining 0.44 correlation floor come from?~~ — **ANSWERED, and the answer is a
   sharp negative. [D389](docs/decisions/D389-RESULT-the-floor-is-ONE-factor-and-none-of-the-four-candidates-explains-it.md).**
   **It is ONE factor** — PC1 reproduces the pairwise rho to three decimals (0.449 vs 0.449), PC2 is
   0.006, all 500 books load the same sign. **And it is none of the four candidates**: slot mechanics
   0.029, equal-weighting 0.031, eligibility floor 0.052, shared hedge term likewise. **Unattributed:
   85% in A-prime, 98.5% in B.**
   - **The arms disagree by 9x and backwards.** A-prime (same names) correlates 0.480 with the market;
     **B (same days) only 0.138 and with nothing else.** B is the arm gate 1d-prime is calibrated
     against, and its floor is **98.5% unexplained**.
   - **Gate 1d-prime needs NO restating.** The floor is not a scorer artefact — 1/nlive scores 0.031.
   - **Where a successor should look:** the factor lives in **which days get traded**, not in the
     market on them — i.e. the **entry-condition distribution**, which no driver here could reach.

4. ~~Exit timing~~ — **DONE. [D380](docs/decisions/D380-RESULT-no-exit-overlay-beats-not-cutting-and-R7s-control-inherits-the-rule.md)
   (`43db0df`) and [D381](docs/decisions/D381-RESULT-a-stop-is-a-late-trigger-and-the-median-mean-exchange-rate-is-fixed.md)
   (`eac6650`). NINE ARMS, NONE BEATS HOLDING TO THE CAP** — on **gross mean per trade**, which is the
   unconstrained objective. D380's first pair were mis-scaled (±200 bp fired on ~80% of trades, caught
   by the principal); D381 re-ran them at declared **fire rates** of 5/10/20% and every arm still lost.
   - **A stop is a LATE trigger by construction.** Don't cut +160.55 · cut the worst 5% at a **random**
     bar **+226.52** · cut them at −3,229 **+142.79**. The threshold is only reached *after* the
     adverse move, and these losers recover.
   - **The median/mean exchange rate is fixed at ~0.44** and flat from a 20% to an 81% fire rate. The
     dose is free; the price is not. **A better win rate is available and costs about two basis points
     of mean for every four of median.**
   - **The R7 lessons are now in [RULES.md](docs/RULES.md) under R7** and bind future overlay studies:
     report against the baseline as well as the control; the control's difficulty is inherited from
     the rule's trade selection; the control is a null and never a policy.
   - **NOT queued, deliberately.** Under a hard drawdown limit the criterion is return per unit of
     drawdown rather than mean, and an overlay can win there while losing here (D381 §5a gives each
     arm's exact drawdown hurdle). **That is for an individual strategy and book to assess at its own
     test stage** — the principle is recorded under R7 and is not being pursued on this construction.
5. **A genuinely new construction**, designed from in-sample reasoning only and pre-registered before
   anything is fetched. **It must not select inside a narrow cohort** — [FINDINGS §52](docs/FINDINGS.md)
   closes winner-selection variants as a family.
   - **AND IT MUST HAVE ITS PERSISTENT-SELECTOR CONTROL DESIGNED IN AT PRE-REGISTRATION.** The density
     line (D384 → D388) beat a path-shuffle null at `p` = 7.2e-11 and a rotated-density null at
     nothing. **Beating a path shuffle is nearly free.** Four of five studies there would have
     reported a headline without the A′-equivalent.
   - **The most promising open lead in the programme is [FINDINGS §57](docs/FINDINGS.md)'s**: two
     unrelated books co-move at 0.476 and **98.5% of it is unexplained**, and the disagreement between
     the arms says the cause is **which days get traded** — the entry-condition distribution — not the
     market on them. That is a target, not a construction, and nothing has been built against it.
6. **P5 should be computed** on anything reaching the prop track, ahead of the other uncomputed legs
   (D379 §6). **P3 and P4 remain uncomputed** and under R6 that is a live defect.
7. **D371's 0.8% breadth failure is NOT retroactively cleared.** H4′ is per-study; that book lived in
   a different universe at roughly half the breadth and **its A′ distribution has never been
   computed.** Nothing material changes — but the record should not be read as saying its breadth
   was bad.
8. **The short side** (`hist_L` k=40, D357) lost its clean fixture when D371 spent holdout #1 on
   momentum. It needs holdout #2 or a later slice.
9. **C1's size sweep is unfinished** — extend below 0.48× and locate the value peak against D379 §4's
   ladder cap. Needs MyFundedFutures' payout ladder terms, which no record holds.
10. ~~Restate P1 as a sizing rule~~ — **DONE 2026-09-08**, R11.
11. ~~The D373 avenue~~ — retired, reopened, tested; **status is the principal's** (see §0 table).
12. ~~Audit the rest of the hurdle set~~ — **DONE, D375.**
13. ~~Make the breadth hurdles breadth-relative~~ — **DONE, D374** (H4′) and **D376** (1d′).

**The breadth test the 2026-09-07 handoff ranked first was dropped, with the principal's agreement.**
It targets a retired object, and the H5 mis-specification it was partly meant to expose is a
definition fix rather than an empirical question.

---

## 0d2. PARKED — SUPPLY AND DEMAND: THE IDEAS NOT TAKEN, 2026-09-09

**D403 was closed by the principal** — *"this construction is dead, I don't think this accurately
captures supply and demand."* The wick-stack potential map is finished and will not be reopened.
Its durable findings are in its own record; what follows is the design work that came out of the
close and is **not** spent.

**THE DIAGNOSIS THAT OUTLIVES D403, and it explains all six price-level failures at once:**

> **A wick is evidence that interest was ABSORBED, not that it REMAINS.** If price spiked to 110 and
> came back, the sellers at 110 were filled — the zone is spent. The same is true of a volume node
> (TERRAIN S1), a swing band (S5), a signed inventory field (S6), a flipped level (D211), a fair
> value gap, and D403's potential. Every one is a trace of trading that already completed, read as a
> forecast of trading still to come.

And the mechanical corollary that predicts the failure **before** a study is built: **all six maps
are pure functions of the past price path.** That is exactly why the rotation control kills them —
rotating preserves the path and destroys only the alignment, and the alignment carries nothing. **Any
candidate that is another function of OHLC alone will die the same way.** Require of a seventh that
it carry information the price path cannot.

**THE PRINCIPAL CHOSE (2) ON 2026-09-09 and it is drafted, not committed** — see
`docs/decisions/DRAFT-capital-gains-overhang.md`, uncommitted, **no decision number taken** (the
three-command procedure runs at commit time, not before). The other three are parked here:

**(1) RESTING LIQUIDITY — the order book.** Literally supply and demand, and the honest ceiling on
every approximation below it. **Blocked, not rejected.** D336's quoted-spread pull needs the
principal's TWS session and is top-of-book only; `scripts/d364_databento_equity_plan.py` is an
arithmetic-only cost plan with no submit path. **If the TWS blocker ever clears, this outranks
everything in this section.**

**(3) OPTIONS OPEN INTEREST / DEALER GAMMA.** Genuinely forward-looking and size-carrying — resting
*obligations* at specific strikes, which is the property every price-history map lacks. Nothing in the
repo. Alpha Vantage serves `HISTORICAL_OPTIONS` on the existing key, so it is reachable at request
cost and no new vendor. **Do not spend this until (2) has reported** — it is a real acquisition and
(2) tests the same "unfilled interest" thesis for free.

**(4) EXECUTION ANCHORS — VWAP and the closing auction.** Weak as *zones*, but they hold the one
property nothing else here does: somebody is **obliged** to trade there. `scripts/d364_auction_bound.py`
already documents the 1-minute call shape. Cheapest of the four; lowest ceiling.

**UPDATE 2026-09-10:** (2) the capital-gains overhang ran as D405 and **abandoned at stage 0** (the
overhang is momentum); (3) options open-interest density ran as D406 and **failed its bar**; the
departure-zone line (D412–D433, above) was the seventh price-path map and died out of sample twice.
**Never tested in this repo, and each carries information the price path cannot:** short interest /
days-to-cover as a *signal* (FINRA bi-monthly, public), insider transactions, share issuance /
buybacks / lockup expiries (the literal supply of shares), 13F holdings changes, index-inclusion
flows. Zero decision files on any of them.

**MULTIPLICITY: any of these is look #7 on price-level maps.** The R13 ledger carries 259 terrain
looks and 86 structure looks in, and D403 makes six programmes with six written closes. **None of
them paid.** That base rate is the reason (2) is drafted as a stage-0 discriminator with an abandon
condition rather than as a study with a sweep.

---

## 0e. THE LESSON THAT OUTRANKS BOTH RESULTS

**In-sample null strength does not forecast out-of-sample survival.** The momentum construction
cleared its time rotation at **164 standard errors with zero of 10,000 draws beating it**, cleared a
best-of-ten multiplicity control, and cleared a symmetric winner-removal test. **It still failed.**
Permutation nulls test whether a pattern is real *in the data you have*; they say nothing about
whether it recurs.

Three studies went into making those in-sample verdicts precise (D369) and unbiased (D370). Both
were necessary. Neither was sufficient.

**And the successor built to replace it was the same book.** D373's H7 says a construction can be
re-derived from different-sounding premises and still hold 70% of the same name-bars. **Measure
independence on day one, not at stage 5.**

**Two more, earned across D374–D377 and worth as much as the above:**

**A threshold you have never calibrated is not a hurdle, it is a guess.** H4 was unreachable by a
factor of four and failed the most diversified book in its own null. Gate 1d was measuring pool
overlap. Both had adjudicated real studies. **The cheap test — "has anything ever passed this, and
what does a null draw score?" — takes minutes and should run when the hurdle is written, not five
studies later.**

**Direction right, scale wrong — four times running.** D374, D376, D377 and D373's own predictions
all had the sign of the effect correct and the magnitude badly off, always in the same direction:
**I under-estimate how much of these books is structure and over-estimate how much a correction will
move.** Weight point estimates accordingly.

---

## 0f. TRAPS, 2026-09-07 — all cost real time

- **Persist before you render.** D371's first execution computed its evidence and lost the JSON to a
  `KeyError` in the print loop; the console had printed only booleans. D373 hit the *same shape*
  twice more (arm C's dict differs from `verdict()`'s) and lost nothing, because the artifact is
  written first. **Keep that ordering.**
- **Three D373 hurdles reported the wrong verdict from lookup faults, not from bad data.** H4 read
  `top_name_share` by `"top1"` when it is keyed by `int`, so it returned UNRESOLVED with two null
  legs; H7 was stored with no verdict and rendered as `-`, entering no roll-up. **A hurdle that
  cannot fail loudly is as bad as no hurdle** — check the roll-up actually consumes it.
- **Cumulative s/draw in a progress log is not the marginal rate.** D373's five parts printed 7.09
  s/draw at draw 130 and 5.73 at draw 400; the marginal rate was ~3.9 throughout. The numerator
  carries one-time prep. **Estimate remaining time from the last two lines, not the running mean.**
- **`_m_start_of` took the bar after the LAST undefined market bar** — correct only when every gap is
  a warm-up prefix. Holdout #1's 3 interior holiday bars gave `m_start` 4,125 of 4,190, **a 65-bar
  sample with every check green.** Fixed `ce2947c`.
- **`V58.pct_of` memoises by score NAME only.** A process touching two fixtures gets the **wrong**
  percentile grid for the second. Clear `V58._PCT` between re-points.
- **`np.savez` appends `.npz`** unless the name already ends in it; **`np.load` returns a lazy
  handle** Windows will not let you replace until closed.
- **Backticks in `git commit -m` are command substitution.** Use `-F <file>` written with the Write
  tool — the heredoc hook blocks heredocs for exactly this reason.
- **Never pipe a background command through `tail`/`grep`** — the pipe buffers and progress is
  invisible. Redirect to `temp/<job>.log` and tail the file.

---

## 0g. STANDING CONSTRAINTS FROM THE PRINCIPAL — these bind

- **R15: a signal is a positive GROSS mean per trade above its nulls.** Costs and confluences come
  later. **ONLY THE PRINCIPAL CLOSES A RESEARCH AVENUE.**
- **No holdout read without explicit, specific authorisation.**
- **Costs are IBKR's official costs.**
- **No subagents unless the work is genuinely parallel.** Build and run sequential work directly.
- **R8:** pre-registration committed *before* the runner exists; the result committed **separately**.
- **Clearing a study's hurdles does not admit a strategy.** R8 needs a separate pre-registered
  out-of-sample test on a fixture it has never seen; the prop book also needs hurdle P (R11), all six.

---

## 0h. WHERE TO READ

| | |
|---|---|
| how to work here | `CLAUDE.md` |
| rules | `docs/RULES.md` — **R8, R13, R14 + amendments, R15** |
| substantive truth | `docs/FINDINGS.md` — **§§46–51** newest |
| where the programme stands, D285→D364 | `docs/STACK.md` **§0, §§32–42, 40a**; **§7 is what earlier versions got wrong** |
| the momentum session | `docs/HANDOFF-2026-09-07-momentum-holdout.md`, `docs/decisions/D366…D371*` |
| the holdout read itself | `data/d371_read.json`; construction frozen in `data/d371_construction.json` |
| the last study | `docs/decisions/D373*` · `data/d373_winners_dip_long.json`, `data/d373_posthoc.json` |
| the two books | `docs/BOOK.md` (S1, S2), `docs/BOOK_PROP.md` (**admitted arms: none**) |

---
---

# OLDER STRATA — newest first

**Everything below predates 2026-09-05 and describes the short-side and futures work. It is kept for
the traps and the standing data constraints, not for its state claims.** Where it disagrees with §0
above, §0 wins.

---


## THE 2026-09-02 SESSION — D264 → D284, the directional shorts

*Superseded as a state file by §0 above; the closures and traps below still stand.*

### 0-2026-09-02. THE ONE-LINE STATE, AS IT WAS

**EIGHT CONSTRUCTIONS, FIVE UNIVERSES, TWO FREQUENCIES, BOTH DIRECTIONS. NOTHING SURVIVES.**

| study | construction | outcome |
|---|---|---|
| D264-D278 | the intraday single-name short, every lever | closed on `2c` |
| [D279](docs/decisions/D279-the-concentrated-short-on-dead-inclusive-names.md) | daily concentrated, top-N by score | **0 of 14.** Its first RESULT reported two survivors and **they were LOOK-AHEAD. Withdrawn.** |
| [D281](docs/decisions/D281-the-unfiltered-ranking.md) | rank the whole universe | **0 of 10**, and worse than random |
| [D282](docs/decisions/D282-the-overnight-only-short.md) | overnight-only, ascending | **0 of 19.** Loses 24 bp/night |
| [D283](docs/decisions/D283-the-descending-ranking.md) | descending, both tails | **0 of 26.** Symmetry fails BY SIGN |
| [D284](docs/decisions/D284-the-overnight-long.md) | the overnight LONG | **0 of 13.** Clears `2c` at 2.41x and dies on SPREAD |

Everything intraday closed on one condition, in which the trade count cancels and hit rate never
appears:

```
mean move per trade  >=  2c        (the round-trip cost)
2c = 4.00 bp LOW - 8.42 bp ALL - 12.84 bp HIGH
```

**Six signal families, three input families, a volume profile three ways, two exit levers, a
300-cell mine and a 16-name instrument holdout all failed that bar.** Nothing failed for want of a
null.

**D279 closed on something different and worse: it never reached the cost question.** Re-scored at
zero fees, zero borrow and zero rf, `S1_short|top25` posts **-0.432 Sharpe and -0.26% CAGR**. Every
cell in the grid has a negative net CAGR, every breakeven borrow rate is negative, and the
best-of-14 floor is **-0.178** against a best cell of **-0.337**. **On the daily fixture the binding
constraint is the drift, not the toll.**

**What is live is one pre-registered study and one untouched branch.** See section 5.

## 1. PICK THIS UP FIRST - the D279 look-ahead, because the lesson is a runner lesson

**`run_concentrated_short.top_n` ranked the qualifying names with `score[:, t]` - `hist_L` computed
from the close of the very bar the position was about to be paid for - and then held that position
through bar t's return.**

`hold_book` lags the qualifying MASK correctly and always did (`p[:, 1:] = mask[:, :-1]`), so
**which names QUALIFIED was honest and [D256](docs/decisions/D256-the-book-on-single-names.md) is
untouched.** What was contaminated is **which N of the qualifiers were HELD** - which is exactly the
quantity hurdle C exists to test.

```
corr(hist_L at t,   hist_L at t-1)   +0.9805      the score barely moves when lagged
corr(hist_L at t,   return at t)     +0.0737      ranking on this is peeking
corr(hist_L at t-1, return at t)     -0.0103      the tradeable version

top25   UNLAGGED  +1.43% CAGR  +2.250 SR      LAGGED  -0.32%  -0.638
top50   UNLAGGED  +2.05% CAGR  +1.865 SR      LAGGED  -0.56%  -0.659
```

**THE LESSON, and it is new to the programme: a lagged position built from an UNLAGGED RANKING is
still look-ahead, and the base being correctly lagged is what hides it.** Every look-ahead guard we
own points at `hold_book`, and `hold_book` was right. The defect entered one layer above it, in a
function that *filters* an already-lagged book - a place nothing was watching, because filtering a
lagged book feels like it cannot introduce a lag error. **[R9](docs/RULES.md#r9)'s third appearance**
after D224 and D248, and the second on `hist_L` specifically.

**The fix now lives INSIDE `top_n`**, not at the call site, because three other modules call it.
**One consequence:** re-running `scripts/d279_lookahead_check.py` no longer reproduces its own
UNLAGGED column - its two arms have become lag-1 and lag-2. The correlations still reproduce; the
UNLAGGED Sharpes are only reproducible against the pre-fix runner and are quoted from the withdrawn
artefact, kept as `data/d279_concentrated_summary.WITHDRAWN_lookahead.json`.

**Three further caveats in D279's corrected RESULT, all still live for anything that inherits this
construction:**

1. **Hurdle H is FAILED for that study, not passed.** `S1_short|all` scores the **100th percentile
   on both legs with -0.757 Sharpe and -2.45% CAGR**; seven of fourteen cells clear it and all
   fourteen lose money. [R7](docs/RULES.md#r7)'s corollary applies. **Do not reuse that null
   unmodified.**
2. **Hurdle C is scored against ONE random draw, not a distribution.** The same control cell scored
   **-1.528** in the runner and **-1.633** in the decomposition; at S2/N=50 the gap is 0.16 Sharpe.
   `rotation_nulls` takes 300 draws and C took one.
3. **E' degenerates on a rotating book.** `top25` scored **28.00 on 28 names** - the correlation
   matrix is the identity, because almost no *pair* shares the 250-bar overlap minimum. It silently
   became "how many names were held >=250 bars", on which `top10` scores **1.00 on one name**. **The
   runner still has this defect**; `data/d279_concentrated_summary.json` carries an
   `Eprime_panel_defect` flag on every cell and the honest values are in
   `data/d279_eprime_corrected.log`.

## 1a. THE EDGE IS ENTIRELY OVERNIGHT - [D280](docs/decisions/D280-the-forecast-precheck.md)

**TESTED FOR STALE OPENING PRINTS 2026-09-09 AND IT SURVIVED — [D402](docs/decisions/D402-RESULT-the-overnight-gap-survives-and-the-contamination-is-real-but-elsewhere.md).**
The gap is formed entirely from the vendor open and that had never been checked. **17.6% of
out-of-sample bars DO carry a detectable print artefact** — `open == prior close` exactly on
5.84% — with a **-0.1564** gap-to-intraday reversal confined to them and **+0.0082** on the rest.
**But the edge is not there:** on CLEAN bars the IC is **-0.01746 (1.14x the committed value)**,
and it is **1.8x STRONGER in the most liquid $-volume quintile than the thinnest**. A print
artefact must concentrate where prints are unreliable; this concentrates where they are most
reliable. **The measurement stands. The money question below is untouched.**


**D280 is a MEASUREMENT record - it scores no cell, ranks no name and proposes no rule, and its
ledger is 0.** It ran BEFORE any pre-registration because it decides whether there is anything to
pre-register.

**THE HEADLINE, and it is the largest result of the D264-D280 sequence.** Cross-sectional IC of the
R9-lagged `hist_L` against each PART of the next bar, out of sample. Negative = tradeable for a
short:

```
universe   target       mean IC       t
ALL        total        -0.00524   -1.79
ALL        gap          -0.01531   -4.71     <-- the edge
ALL        intraday     +0.00168   +0.65     <-- nothing
QUAL       total        +0.00462   +1.43
QUAL       gap          -0.01255   -3.45
QUAL       intraday     +0.00868   +2.85     <-- runs AGAINST the short
```

> **There is a real, correctly-signed OVERNIGHT edge and a wrong-signed INTRADAY move that cancels
> it. Close-to-close - the only quantity D256 and D279 ever measured - is the SUM OF THE TWO, which
> is why it read as noise.**

- **No intraday stop, target, partial exit or overlay can reach it**, and taking the position at the
  open to shed overnight risk discards the edge and keeps the leg that fights it. **Both branches
  close on one measurement.**
- **It is NOT ex-dividend drops** - the obvious confound, since `gap` is raw OHLC and a short OWES
  the dividend. Dividend-adjusted the IC is **-0.01498 (t -4.59)**; ex-dates excluded, **-0.01494**.
  Only 0.834% of bars go ex next session. **On those 216 bars the IC is -0.05197**, 3.4x the average,
  so the mechanism is real and localised - **charge dividends explicitly in any book built on this.**
- **AN IC IS NOT MONEY.** An overnight book trades a full round trip EVERY NIGHT - ~252/yr against
  ~17/yr for D279's ~15-day holds - so D265's bar (`mean move per trade >= 2c`, 10 bp at 5 bp/side)
  must be cleared **15x more often**. A rough prior, **not computed from these artefacts**, puts the
  per-night edge near 4 bp against that 10 bp toll. **D282 is pre-registered to measure it. Do not
  predict it.**

**THE STRUCTURAL FINDING, and it is the second thing to carry out of this session:**

> **D256 and D279 both filter on `hist_L < 0 & md_L >= 0` and then rank the survivors by `hist_L`
> again. The filter and the ranking are the SAME VARIABLE. The signal is spent by the time the
> ranking runs, and what remains inside the filtered set reverses.**

Cross-sectional IC - Spearman, within each bar, against the NEXT bar's return, out of sample:

```
hist_L over ALL live names       mean IC -0.00524   t -1.79   2,173 bars   correctly signed
hist_L over the QUALIFYING set   mean IC +0.00462   t +1.43   2,147 bars   WRONG SIGN
```

**That is the whole of why D279's ranking bought +0.203 gross Sharpe on a book sitting at -0.432.**

**What else D280 settled:**

- **The DEMA + velocity/acceleration/jerk extrapolation is dead.** It loses to naive persistence in
  **all 48** level comparisons, all nine delta comparisons and all nine range comparisons.
  Derivatives correct the smoother's own lag rather than forecasting; longer n is monotonically
  worse; jerk hurts in 8 of 12 cells (noise multiplier C(2k,k) = 20).
- **16 OHLC derivative terms carry 13.50-15.76 EFFECTIVE inputs**, not the sub-3 collapse predicted.
  **The intrabar axis is real, independent, and carries no predictive power** - the mirror image of
  D268's lesson, and it belongs beside it.
- **`open(t+1) := close(t)` is NOT free.** Median |gap| **0.5263%**, mean **0.9393%**,
  **|gap|/|body| = 0.515**. Range is separately predictable at correlation **+0.87** and
  persistence-of-range still beats the DEMA stack on MAE, so range is a sizing input at best.
- **Multiplicity: 165 statistics across five parts, 161 distinct.** The median largest |t| under a
  161-test null is **2.86**, so the best *extrapolation* result (**|t| 2.29**) is a best-of and is
  **not evidence**, and the only un-searched baseline (`hist_L` alone, all names, t **-1.79**) is not
  significant either. **The overnight numbers are the exception: |t| 4.71, 5.07 and 5.97 clear a
  best-of-161 correction comfortably**, and part 4's gap leg was declared in the script before it
  ran. **The t is small on 2.2M name-bars because n is 2,173 BARS** - the IC is computed within each
  bar and averaged.

## 2. WHAT WAS CLOSED, AND ON WHAT

| | closed by | on |
|---|---|---|
| S1 / S2 shorts, intraday, single names | D264 | 0 of 12 cells; commission alone beats the breakeven |
| entry timing | D265 | early entries are 1.57× the bar; whole-book +0.38%/yr |
| magnitude calibration, 9 price scores | D267 | 0 of 27; whole Q1–Q5 spread < one round trip |
| the consensus proposal | D268 | 2.87 effective inputs of 9; **RSI is trailing return at ρ +0.78** |
| volume as a third input | D270 | orthogonal at ρ 0.09, best cell 0.92× the bar |
| the volume profile, as an input | D272 | most orthogonal thing measured (ρ 0.085), 0 of 6 |
| the volume profile, as a travel estimator | D273 | travel is flat in room; the node is a distance |
| exits, time-based | D274 | **a random exit bar beats a fixed one** |
| change of character | D275 | legs run 182.7 bp median, the rule captures 0.57 bp |
| exits, structural | D276 | removing churn made it worse; exposure 47% → 4.5% killed it |
| the mine, 300 cells | D277 | best +0.392 against a best-of-300 floor of +0.605 |
| **all five in-sample winners** | **D278** | **every one reverses sign on 16 fresh names** |
| **the concentrated DAILY short** | **D279** | **0 of 14; `top25` is −0.432 Sharpe GROSS, so it loses before costs** |
| the DEMA derivative forecast | **D280** | loses to naive persistence in **all 48** level comparisons, all 9 delta, all 9 range |
| **intraday exit overlays on this construction** | **D280** | **the edge is entirely overnight** (gap IC −0.01531 t −4.71; intraday +0.00168 t +0.65) |
| taking the position at the open to shed overnight risk | **D280** | same measurement, reversed — it discards the edge and keeps the leg fighting it |

## 3. THE FIVE THINGS WORTH CARRYING

1. **The cost bar is `mean move per trade ≥ 2c`, and it is signal-independent.** The trade count
   cancels; hit rate never enters. Any future intraday construction should be screened on this
   first, for the cost of one measurement.
2. **Most technical indicators are monotone transforms of trailing return.** D268: nine scores,
   **2.87 effective inputs**; RSI ↔ macd_line at **+0.85**. "Several indicators agree" is usually
   one indicator agreeing with itself. `scripts/d268_score_independence.py` is the instrument.
3. **Overnight drift is a property of VOLATILITY, not of equities.** Low-vol names accrue it
   **intraday with the sign reversed** (+4.36% overnight vs +5.56% intraday); high-vol names run
   +13.81% vs −8.97%. D247's +8.59%/−0.36% is an average over instruments, not a constant. **This
   belongs in the wide extended-hours pre-registration before it runs.**
4. **A correlation on a continuous score does not survive to its tails.** ρ = −0.83 between
   `mass_imbalance` and `impulse_md` gave only **53% bar overlap** at the quintile extremes — and
   +0.392 against −0.481 Sharpe. I called them "near-identical" and was wrong.
5. **A LAGGED POSITION BUILT FROM AN UNLAGGED RANKING IS STILL LOOK-AHEAD, AND THE BASE BEING
   CORRECTLY LAGGED IS WHAT HIDES IT.** D279's `hold_book` shifted the qualifying mask by one bar
   and always did; `top_n` then chose *which N of the qualifiers to hold* on the unlagged score.
   **Every look-ahead guard this programme owns points at `hold_book`, and `hold_book` was right.**
   Anything that *filters* an already-lagged book is a place to check, precisely because it feels
   like it cannot introduce a lag error. **A second, independent re-derivation of the held set from
   `score[:, t-1]` — not a call into the same function — is the cheap guard**, and D281's runner
   is the first to carry one.

## 4. R13 IS NEW AND IT CHANGES HOW LEDGERS ARE COUNTED

**[R13](docs/RULES.md#r13): a ledger is scoped to a hypothesis and transfers only where it shaped
the search.** Written after the principal pushed back twice, correctly, on inherited counts.

- terrain's **259** is disclosed, not carried (D272)
- the ETF programme's **45,783** is disclosed, not carried — **D218 scopes its own floor to "this
  fixture"**, meaning 57 ETFs daily
- what carries into the single-name work is **~118**, because D264–D276 built the bases and scores

**D247–D276 keep the older single-cumulative convention and are NOT restated.** R13 explains the
discontinuity rather than erasing it.

**And nothing reopened.** Every closure above fired on a hurdle failure, not on multiplicity.

## 5. WHAT IS ACTUALLY LIVE

1. **The wide extended-hours decomposition** — fixture built and gated (`c25218d`), nothing
   decomposed, prediction declared. **Add the volatility split from §3.3 before running it.**
2. ~~A concentrated ranked short on the DAILY dead-inclusive fixture~~ — **RUN AND CLOSED, D279.
   0 of 14.** Its stop fired. Nothing further may be tuned on that fixture.
3. **[D281](docs/decisions/D281-the-unfiltered-ranking.md) — rank the WHOLE universe, removing the
   filter/ranking collision D280 measured and changing nothing else.** Pre-registered before its
   runner existed; **result pending at the time this handoff was written.** It inherits D280's 150
   comparisons under [R13](docs/RULES.md#r13) test 2, because D280 shaped its search space.
4. **[D282](docs/decisions/D282-the-overnight-only-short.md) - the cost arithmetic of the overnight construction** part 4 implies: ~252 round trips a
   year against D265's `2c` bar. **Pre-registered by another agent; result pending. Do not predict
   it.**
5. **The volatility tilt D280 part 4 turned up** — `zh + zv + za + zr` reaches IC **−0.01373
   (t −5.07)** on all live names, the only directional statistic in that record that clears its own
   multiplicity. **It is a volatility tilt, not a stronger `hist_L`** (flip `zr`'s sign and the IC
   goes positive), it does nothing on the qualifying set, `zr` alone was never scored, and no book,
   cost model or `sigma^2` tax has been applied to it. **Needs its own pre-registration.**
6. **The factor-neutral branch of FINDINGS §9** — still untouched after D256, D264, D279 and D280.
7. **Prop track:** rung 2's micro/mini form and rung 3, both free, both untested.
   [D266](docs/decisions/D266-the-prop-cross-screen.md) screened this session's work against
   hurdle P and the best cell earned +0.535%/yr after P1 sizing. BOOK_PROP.md stays empty.

## 6. DATA THAT NOW EXISTS

| | |
|---|---|
| `single_name_intraday_15m_{raw,panel}.csv.gz` | 8 names, 55,004 bars, 26.0/session, gates PASS |
| `holdout_intraday_15m_raw.csv.gz` | 16 names, 899,196 rows — fetch finished, D278 spent it |
| `cohort3_intraday_15m_raw.csv.gz` | **8 names, 448,861 rows, gates PASS, all 28 steps REAL. UNSPENT — spendable ONCE** |
| Alpha Vantage 15m cache | 57 ETFs + 24 single names, ~2,500 slices. **Any of these starts at zero requests.** |

**The provider limit is settled, do not re-probe it:** `TIME_SERIES_INTRADAY` serves **nothing**
for a delisted ticker (TWTR/FRC/SIVB/AABA, four for four). `TIME_SERIES_DAILY_ADJUSTED` does.
**41.6% of the 2013–17 cohort is unreachable at 15 minutes**, so every intraday single-name study
is survivor-only and the bias runs *against* a short.

---

## EARLIER THE SAME DAY — the D264 session, as it stood mid-way

*Superseded by the section above; kept because its data-layer notes are still accurate.*

---

## 0. THIS SESSION — D264 ran and closed. Three commits.

```
fc5b080  D264 RESULT: closed -- zero of twelve, and the cost decides, not the signal
7492402  Single-name 15m fixture: gates pass, and all 30 flagged steps are real
56c6156  D264 PRE-REGISTRATION, committed BEFORE the fixture is scored
```

**Working tree CLEAN. Suite 1,831 passing, 5 deselected, 1 failing** — the same pre-existing
`test_every_gap_is_a_non_empty_band_that_price_left_behind`. **Still not to be fixed.**

**Next decision number is D265.** Both counters (`docs/decisions/README.md`, `docs/RULES.md` R5)
are correct.

### What was built and is now durable

| | |
|---|---|
| `data/fixtures/single_name_intraday_15m_raw.csv.gz` | 8 names, 448,279 rows, 2018→2026, gates PASS |
| `data/fixtures/single_name_intraday_15m_panel.csv.gz` | **8 × 55,004 bars, 2,117 sessions, exactly 26.0/session** |
| `scripts/select_single_name_intraday.py` | the sample rule, on a window disjoint from the test span |
| `scripts/fetch_single_name_intraday.py` | fetcher, reusing the ETF one's helpers |
| `scripts/classify_single_name_steps.py` | D226's allow-list, built by measurement |
| `scripts/run_single_name_intraday.py` | 16 cells, six hurdles, every leg computed |

**~848 Alpha Vantage requests spent. Any further single-name intraday work on PG LMT PM MO CLF SM
YELP RH starts at zero requests.**

### THE PROVIDER LIMIT THAT SHAPES ALL FUTURE INTRADAY WORK — measured, five calls

**`TIME_SERIES_INTRADAY` serves NOTHING for a delisted ticker.** TWTR, FRC, SIVB and AABA all
return `Invalid API call` at 155 bytes; AAPL returns a clean 546 bars. **`TIME_SERIES_DAILY_ADJUSTED`
DOES serve dead names** — that is how D252 built a 35.7%-dead daily fixture.

**So any intraday single-name study on this provider is survivor-only, and 41.6% of the 2013–2017
cohort is unreachable.** Do not re-probe this; it is settled. If a dead-inclusive intraday fixture
is ever needed, it requires a different vendor (Polygon, Databento) and that is a spending decision.

### The result, in one line

**Zero of twelve short cells cleared.** The construction produces the **largest gross short edge
this programme has measured** — held bars returning **−28.87%/yr**, hurdle H cleared on both legs at
the **96.9th / 99.7th** percentile — and loses **15.84%/yr**, because:

```
exposure x edge   +8.31%/yr        (continuously compounded; percentages do not add)
- sigma^2 tax     -4.87%           59% of the gross, exactly as FINDINGS 1b describes
= realisable      +3.43%           still profitable at this point
- trading cost   -20.68%           324 turns/yr at 6.42 bp/side -- 6.0x the realisable gross
= net            -17.24%
```

**And the kill is assumption-free: mean commission ALONE is 1.92 bp against a 1.06 bp breakeven.
The cell loses at a zero spread**, so the verdict does not depend on the half-spread figure that was
named in advance as the design's weakest number.

**The closure is bounded**: it closes *that construction on those eight survivor names, personal
track*. It does not close the intraday short, because the survivorship bias runs **against** the
short and that direction was declared before the data was seen.

---

## 0b. THE THREE THINGS FROM D264 WORTH ACTING ON

### (a) OVERNIGHT DRIFT IS A PROPERTY OF VOLATILITY, AND THIS CHANGES A QUEUED STUDY

| | overnight/yr | intraday/yr |
|---|---:|---:|
| **LOW vol** — PG LMT PM MO | +4.36% | **+5.56%** |
| **HIGH vol** — CLF SM YELP RH | +13.81% | **−8.97%** |
| *57 ETFs — D247* | *+8.59%* | *−0.36%* |

**In low-volatility names the drift accrues INTRADAY and the sign reverses.** D247's figure is an
average over instruments whose volatility differs, not an asset-class constant.

> **ACT ON THIS: the wide extended-hours pre-registration in §4c below should carry a VOLATILITY
> SPLIT.** It already asks where untraded-window drift accrues across 11 instruments, and PICKUP
> already records SPY and QQQ disagreeing 33% against 91%. **D264 says that disagreement has a
> measurable axis.** Add it to the design *before* running, alongside the EEM/FXI prediction that is
> already declared.

### (b) COST PER BASIS POINT IS A FUNCTION OF PRICE — post-hoc, disclosed, NOT tested

IBKR charges **per share**, so commission in bps is inversely proportional to price. Inside the
high-vol stratum it varied twenty-fold:

| | RH | YELP | SM | CLF |
|---|---:|---:|---:|---:|
| commission, bp/side | **0.20** | 1.44 | 1.89 | **4.15** |

**A high-priced, high-volatility name gets the high stratum's edge at a fraction of its commission.**
Invisible on ETFs, which cluster in price.

> **This is NOT eligible as a D264 follow-up** — D264's stop forbids an additional stratum, and
> computing a per-symbol verdict now is precisely the complement-chasing D246 Constraint 3 forbids.
> **It is eligible as its own pre-registration with the provenance stated**, which Constraint 3
> explicitly permits. If you take it: select on price × volatility on a pre-period, fetch a fresh
> sample, and declare in advance that the breakeven must exceed commission alone.

### (c) BREADTH IS NOT CAPPED AT 2.2

**Effective instruments 3.02 of 8 single names**, against **2.23** on 57 ETFs and 1.80 of 35 on
crypto. FINDINGS §4's saturation near 2.2 is a property of the ETF universe, **not a ceiling**. Any
future breadth argument should stop quoting 2.2 as universal.

---

## 0c. WHAT IS STILL LIVE, IN PRIORITY ORDER

1. **The wide extended-hours decomposition** (§4c) — fixture built and gated, nothing decomposed,
   prediction already declared. **Add D264's volatility split before running.**
2. **Rung 2's free micro/mini form and rung 3** (§4) — untested, free, prop track.
3. **The factor-neutral branch of FINDINGS §9** — never attempted on the 1,580-name daily fixture.
4. **The price-stratified intraday question** (0b above) — needs its own pre-registration.

**Note on the personal track's short side:** with D264 closed, *directional* shorts are now closed on
liquid ETFs (D238/D240/D247/D248/D249), on single names daily (D256), and on concentrated single
names intraday (D264). **The remaining untested shapes are factor-neutral, not directional.**

---

## PREVIOUS SESSION — the futures data layer

*Written 2026-09-01 at the end of the session that built the free half of the futures data layer.
Everything below this line predates D264 and is preserved unedited; §1 and §2 restate that
session's tree state, not the current one — see §0 above for the current state.*

Read this first, then [`docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md`](docs/decisions/D262-the-futures-data-layer-and-the-free-rung.md).
Everything below is verifiable from the repo; nothing here is a plan I intend to be trusted on faith.

---

## 1. State of the tree

**Working tree is CLEAN. Everything is committed.** Nine commits this session, `520e71b..0b40695`.

```
0b40695  WP4: the 2010-2017 backfill lands, and the 57-ETF extended fixture is REFUSED
8df1bc1  fetch_databento: close the two guard gaps found by reviewing the guards
0b99ac1  fetch_etf_intraday: --extended writes its OWN fixture, and 64 bars not 26
1043544  D262: the futures data layer documented, and three corrections to the proposal
02d8277  Continuous-contract stitcher, and the gates that reject a bad splice
4ef9a61  Databento client: verify-first, and structurally unable to spend
c18a4e6  CFTC Commitments of Traders: rung 1 of the ladder, built and committed
b1af940  futures-data: close lane 01, and close the forum search entirely
520e71b  data-purchase-proposal.md: the full costing, with the tick figure corrected
```

**Suite: 1,831 passing, 5 deselected, 1 failing.** The failure is
`tests/property/test_structure_invariants.py::test_every_gap_is_a_non_empty_band_that_price_left_behind`
and it is **PRE-EXISTING and explicitly not to be fixed.** Do not "helpfully" repair it.

**Next decision number is D263.** The README counter was stale at D260 and is now correct.

---

## 2. THE ONE THING BLOCKING PROGRESS, and it is not yours to unblock

`scripts/fetch_databento.py --verify` **cannot run: there is no Databento key on this machine**, and
no account behind it.

```
key file expected at:  C:\Users\O\.config\databento\key        (does not exist)
or env var:            DATABENTO_API_KEY                        (not set)
```

**Do not create the account. Do not handle, write, or ask for the key.** The principal has been given
the two steps (sign up choosing **usage-based $0/mo, NOT Standard**; save the key to that path). If
they say it is done, run `--verify` — it is free, metadata endpoints only, ~7 calls, ~4 seconds.

### What `--verify` settles, and why it matters more than it looks

**The single inferred number the entire $181.81 costing rests on.** We derived **$28.00/GiB** from
Databento's own two worked examples. **Their published `list_unit_prices` example shows `ohlcv-1m` at
280.0** for an unnamed dataset — ten times that. Unit prices are per-dataset so it is *probably* not a
contradiction, but the spread is **$182 against $1,820** and probably is not good enough.

It also resolves `ES.c.0` / `ES.v.0` / `ES.n.0` to settle whether the roll-rule letters mean what
`databento-python`'s `RollRule` enum implies. **See §5 — this one nearly cost real money.**

---

## 3. What now exists that did not before

| | |
|---|---|
| `scripts/fetch_cftc_cot.py` + fixture | **rung 1 of the ladder, free, BUILT** |
| `scripts/futures_continuous.py` | the stitcher §12 requires, tested against **no vendor data** |
| `scripts/fetch_databento.py` | a client that **cannot spend by accident** |
| `docs/cftc_cot.md`, `docs/databento_api.md` | provider references |

**`data/fixtures/cftc_cot_raw.csv.gz` — 210,717 rows, 28 symbols, three report families,
1986-01-15 → 2026-08-25, 3.1 MB, COMMITTED.** It is the only source in the futures data layer that
may be committed, because COT is a work of the US government and is public domain.

**Also durable:** the Alpha Vantage 15-minute cache is now **complete at 11,400 slices** (526 MB,
gitignored), including the 2010–2017 backfill. **Any future extended-hours study starts at zero
requests.**

---

## 4. UPDATE — rung 1 was screened after this file was first written, and it CLOSED

**[D263](docs/decisions/D263-the-cot-positioning-prescreen.md), commits `4dd6d3c` (design, before
the run) and `48c2d36` (result).**

**Zero of eight cells cleared. Monotonicity failed on all eight**, which is the decisive one —
`nonreportable (disagg)` runs +1.83 / −5.53 / **−19.33** / +8.82 / −1.32. Best gross was
**+1.26%/yr** against a 2% bar. **2020 is not the cause**: seven of eight signs survive its removal,
so the result is *empty* rather than regime-dependent.

**Weekly category positioning is CLOSED for the prop track.** The stop applies: no threshold sweep,
no second lookback, no third category. **Do not reopen it with a variant.**

**Two things worth carrying forward:**

- **The largest spread had the WRONG SIGN** — `managed_money` at −7.32%/yr against a declared `+1`.
  Disclosed, not claimed: it is non-monotone, and D246 Constraint 3 forbids re-reading a falsified
  direction. Do not resurrect it as a momentum signal.
- **THE PANEL SURVIVES AND IS THE REAL ASSET.** 11 contract/ETF pairs, 9,232 weekly observations,
  16.2 years, **effective instruments 3.76, MDE 0.21** — assembled free from two committed fixtures
  and better powered than anything the prop track has run. `scripts/prescreen_cot_positioning.py`
  builds it in ~20 seconds. **Any future weekly cross-sectional question should be asked here.**

### So what is next

**Rung 2's free form — the micro/mini split — is still untested**, and it is a *different
construction on a different quantity*, named on the ladder before D263 ran. It is not a rescue.
Scope it to **ES/MES (272 weeks) and NQ/MNQ (302 weeks)**; M2K has 136, MYM 78, MSI 5. Thin, and R10
applies to two correlated instruments.

**Rung 3 — open interest against volume — is also untested and free.**

**And weigh this honestly before spending:** the ladder's premise was that positioning/flow is one
of the few families with the shape hurdle P wants. **The cheapest rung came back empty.** That is
evidence about the family, bought for £0, and it is exactly what §7.5 was built to produce. It does
not close intraday order flow — a weekly survey says nothing about an hours horizon — but it should
lower the prior before ~$205 is spent.

---

## 4b. The original next step (superseded by §4 above)

**Screen rung 1.** The ladder in §7.5 of the proposal says test the cheap instruments before buying
the expensive one, and rung 1 is now sitting in the repo.

> **This is a STUDY, so it needs its own pre-registration under R8 before anything is scored.**
> D262 is a *data acquisition* record — it deliberately scored nothing. Do not read the fixture and
> report a number without registering first. That is the whole discipline of this repo.

**The question worth registering:** does institutional-versus-retail positioning, as the CFTC
classifies it, carry information at a weekly horizon?

**Two constructions are available and they are not the same test:**

1. **Category positioning** — `leveraged_money` / `asset_manager` / `dealer` net positioning and its
   changes, per contract. Available on the widest history.
2. **The micro/mini split** — the free weekly form of rung 2. **THIS IS THE FINDING OF THE SESSION:**
   the CFTC reports micros as their own contracts (MES `13874U`, MNQ `209747`, M2K `239747`,
   MYM `124608`, plus micro metals), each with its own `nonrept` small-trader column. The proposal
   costs this at $14.28 of Databento minute bars to *infer* the split from contract choice; the CFTC
   classifies the traders directly.

**BUT READ THIS BEFORE SCOPING IT.** A contract enters COT only once it has enough *reportable*
traders, which lags listing by years:

| | listed | first COT report |
|---|---|---|
| MES | 2019-05-06 | **2020-07-28** |
| MNQ | 2019-05-06 | 2020-08-04 |
| M2K | 2019-05-06 | **2021-11-30** |
| MYM | 2019-05-06 | **2022-07-26** |
| MSI / MHG | 2022 | **2026-01** — unusable |

**So it is ES/MES and NQ/MNQ at ~6 years, not four pairs at seven.** Scope the registration to the
pairs that have history, and state the breadth honestly — two correlated pairs is thin, and R10
applies.

**Rung 3 is also free** and needs no new data: open interest against volume, in the fixture already.

---

## 4c. INTRADAY — a wide extended-hours fixture is built and gated, decomposition NOT run

**Commit `c25218d`. `data/fixtures/wide_extended_15m_raw.csv.gz` — 2,440,395 rows, 11 symbols,
2010-01 → 2026-08, all four gates PASS. Zero API requests; every slice was already cached.**

Built to settle a question **D259 explicitly left open**: SPY and QQQ *disagree* about where the
overnight drift accrues — the untraded 20:00–04:00 window carries **33% of SPY's and 91% of QQQ's**
— and D259 said in terms that *"nothing should be built on the untraded window's dominance."*
Four instruments cannot separate noise from structure. This is eleven.

**Universe:** SPY QQQ IWM DIA GLD SLV USO UNG GDX EEM FXI. Selected by **coverage** (median ≥45
extended bars of 64), a data-quality rule fixed before any decomposition ran and one that cannot
select on the quantity being measured.

### THE NEXT STEP, AND THE PREDICTION IS ALREADY DECLARED

**20:00–04:00 ET is Asian trading hours.** EEM and FXI track markets that are **open** during the
window the US calls untraded. **So if the untraded-window drift is a real transfer of information,
those two should show the LARGEST untraded share. If they do not, the effect is an artefact of
measuring a closed market rather than a real overnight risk** — and that would materially weaken
the case that overnight futures holds are structurally bad for hurdle P.

**Declare that prediction in the pre-registration before running it.** D263 showed the value: the
biggest number in that table had the wrong sign, and only the advance declaration made it legible
rather than reinterpretable.

**This is a STUDY. It needs its own R8 pre-registration.** Nothing was decomposed.

### Two findings from the build itself

- **THE EVENTS SIDECAR CANNOT EXPRESS A SPIN-OFF.** XLF qualified on coverage and was excluded
  anyway: it closes 23.63 on 2016-09-16 and opens 19.30 — **then holds there all day on 5.9M
  shares.** A −18.3% step persisting at full volume is a corporate action, the XLRE real-estate
  spin-off, and **Alpha Vantage's `SPLITS` reports zero splits for XLF.** `SPLITS` + `DIVIDENDS`
  between them do not cover spin-offs and this project has no general handling. **Check any new
  symbol for one before trusting its returns.**
- **D226's gate spec always required a documented real-events allow-list** — "no move above 15%
  *that is not on a documented list of real events*". The four-symbol build never needed the second
  half of that sentence. It exists now, the threshold is unchanged at 15%, and admission uses D252's
  test: does the move revert (bad print), persist at volume (corporate action), or is it
  corroborated (real).

---

## 5. Traps found this session that will bite you if you do not know them

**The symbol map is derived for a reason. Never type a CFTC contract code.**
`%CRUDE OIL%` matches **seven** contracts. Worse, **`%NATURAL GAS%` matches the main Henry Hub
contract NOT AT ALL** — the CFTC abbreviates it to `NAT GAS NYME`, so the pattern returns two
plausible wrong answers and no right one. A wrong code returns a full, well-formed series for the
wrong market and **nothing downstream errors**.

**The COT open-interest identity is not `OI == sum(long)`.** That fails on 94% of rows. A **spread
position is one long AND one short held by the same trader** — inside open interest, outside the
directional columns. It is `OI == sum(long) + sum(spread) == sum(short) + sum(spread)`, and it then
holds on **55,661/55,661 rows exactly**.

**Key COT dates on `release_date_nominal`, never `report_date`.** Report is Tuesday, release is the
**Friday of that week** — not a flat +3, because the survey day shifts on holidays. Rows before 1993
carry **no release date at all**, deliberately: there was no weekly schedule then and a fabricated
date would look usable.

**`6E` predates the euro.** Legacy rows run from 1986 under the name `EURO FX`; the euro began
1999-01-01 and continuous coverage starts exactly **1999-01-05** after a 644-week gap. **Use
1999-01-05 onward.** `RTY` separately spans an ICE venue change (2008–2017).

**The provider's typos are load-bearing.** `swap__positions_short_all` and
`swap__positions_spread_all` have **double underscores**; `noncomm_postions_spread_all` says
**"postions"**. Pinned by test. If you "fix" them the columns go silently empty.

**`ES.c.0` is almost certainly the CALENDAR roll — rolling at expiry.** §11 of the proposal
hard-coded it. That is precisely the defect §12's acceptance tests were written to catch in Yahoo's
`ES=F`. **The default is now `ES.v.0`.** Do not revert it on the basis of the proposal's text.

**The 57-ETF extended-hours fixture is REFUSED, on measurement.** Only **2 of 57 symbols** reach a
median 58 of 64 session slots; the tail is at 27–28; the raggedness is **liquidity-correlated**,
which is disqualifying for anything volume-related. And an unfiltered **+428.52%** bad print survives
(EWJ 2018-05-23 08:15 prints 11.46 on 912 shares against ~60.60 either side). `--extended` refuses
with the numbers as the reason. **Use `fetch_index_extended.py`**, which applies D259's
corroboration filter and carries a `suspect` column.

---

## 6. Two mistakes I made, so you do not repeat the shape of them

**I overwrote a committed fixture's meta.** The commit *before* it existed specifically to stop
`--extended` clobbering the regular-hours artifact. It parameterised the fixture path and the events
path and **missed the meta.** Caught only because `git status` flagged the committed file as
modified. Fixed by giving one function (`build_targets`) all three paths, plus a test asserting
`do_build` reaches for no unparameterised output constant. **Three constants with two swapped hides
the one you forget.**

**I wrote gates that were wrong before they were right** — the open-interest identity passed on 5.82%
of rows on its first version, and the release convention put a Friday report's release on itself
(zero lag, look-ahead by construction). Both were found by *looking at the output*, not by reasoning.
**Run the gate and read the number before believing it.**

**Practical note:** `Bash` heredocs on this machine mangle backslashes — a `"\n"` inside a Python
heredoc became a literal newline and silently broke a string, and an earlier `str.replace` missed for
the same reason. **Use the Edit/Write tools for anything containing escapes.**

---

## 7. Standing constraints — these do not lapse

**Alpha Vantage key** at `C:\Users\O\.config\alphavantage\key`, read via `ALPHAVANTAGE_API_KEY`
first. **Never inlined, never printed, never logged, redacted from any displayed URL.** Pace at
**66 req/min** against the 75 ceiling. Cache every response; hard stop after 5 consecutive failures.
**The ToS requires this repo stay private.**

**Exchange-licensed data is NEVER committed.** CME, Sierra Chart and NinjaTrader all forbid
redistribution. `.gitignore` carries `data/raw/databento/`, `data/raw/futures/`,
`data/fixtures/*futures*`, `data/fixtures/*glbx*`. The pattern is **gitignored cache + committed
re-fetch script + committed `.meta.json`**. CFTC COT is the sole exception and only because it is
public domain.

**Raw caches are not committed (D191); derived fixtures are.**

**No purchase without the principal's explicit decision.** `--submit` refuses without a passed
`--verify` *and* an accepted figure, and is then deliberately unwired. **Leave it that way** until
the purchase is actually decided — wire it up in the same commit, not before.

---

## 8. Where things are

| | |
|---|---|
| the costed purchase | `docs/research/futures-data/data-purchase-proposal.md` |
| the twelve-lane free search | `docs/research/futures-data/00-SYNTHESIS.md` |
| this session's record | `docs/decisions/D262-...md` |
| standing rules R1–R12 | `docs/RULES.md` |
| the two books | `docs/BOOK.md` (personal), `docs/BOOK_PROP.md` (prop — **admitted arms: none**) |
| substantive findings | `docs/FINDINGS.md` |
| providers | `docs/alpha_vantage_api.md`, `docs/cftc_cot.md`, `docs/databento_api.md` |

**Prop track status: every candidate so far is closed.** C1, C2, C3 and D261's spreads all failed —
three of them on **shape** rather than return, which is why the smart-money detector was worth
reaching for: order flow and positioning are among the few signal families with the shape hurdle P
wants. **Rung 1 is the cheapest available test of that idea and it is ready to screen.**

---

## 9. If you do only one thing

**Pre-register the COT screen and run it.** It costs nothing, the data is committed, and a negative
result is worth as much as a positive one — it would tell the principal not to spend £205 on the
Databento purchase at all.
