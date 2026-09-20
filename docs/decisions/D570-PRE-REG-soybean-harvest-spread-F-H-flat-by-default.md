# D570 — PRE-REGISTRATION: the **soybean harvest spread on the F/H pair, flat by default** — short January, long March, formed at the last session before September and held to November's last session, one contract a leg; written **as seen**, with the avatar recorded as **unsupported**; the stocks-to-use gate as a declared secondary cell

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29; the long window 2011 → 2023 is a declared diagnostic; **the 2024+
slice is RESERVED AND NOT READ on every source** (strip, breadth fixture, COT, WASDE — the WASDE
fixture is filtered to releases before 2024-01-01 first, D568's rule). Nothing admitted (R15).

*2026-09-20, on the principal's word after D569. This is the third per-root avatar
pre-registration and the first written **as seen**: D567's Stage 0 read the thirteen per-year
returns of this exact object, and D569's addendum read, on the same object and its rule-rolled
cousin, everything a pre-registration would otherwise hold back — the always-on control per day,
the per-month split, the placement rank, the gate's outcome, the COT through the window, the
without-2012 mean. There is no unseen in-sample statistic left on this window. What this record
adds is the discipline: the construction fixed in writing, the nulls run on the daily book with
the purge and the exactness guard, cost and the dollar line under the ledger's standard, and
every prediction stated so that the one clean test — the ZS 2024+ slice, the 2024 and 2025
harvests, six positioned months — has something to confirm or refute.*

**What has been seen, exactly (D567 Stage 0; D569 addendum).** The F/H pair's per-year window
return 2011–2023 (short pays 11 of 13, mean +0.53 %, 2012 +3.47 % half the total, without 2012
+0.28 % and 10 of 12); its per-month split (Sep +0.27 %, Oct +0.05 %, Nov +0.21 %; short pays
10 / 8 / 8 of 13); the rule-rolled cousin's per-day return in the window (+0.42 bp) and always-on
(−1.15 bp) and by calendar month; the rule-rolled cousin's exact placement rank on 2011–2023
(0.972); the August stocks-to-use for every year and the gate's composition and outcome (open
2016, 2021, 2022, 2023, all four paid, +0.71 % against +0.16 % ungated); the formation basis
each year; the COT commercial net short at formation and through the window (falls in 8 of 13;
Spearman with the spread +0.57); a one-contract dollar line for the cousin (σ $50 a day; net
+0.66 on 2016–2023, cost 39 % of gross with its October roll). **Not seen:** any statistic of
this object on the 2016–2023 daily book with flat sessions as zeros — its Sharpe, Sortino,
drawdown, the placement null of *this* construction (declared below, never run), its own dollar
line, its worst month. Those are what the runner reads; every prediction below is informed by
the seen table and says so.

**The avatar.** D567 named the merchant clearing full bins by price and the data reversed the
state sign; D569's re-derived avatar (a pre-harvest inverse collapsing) failed its formation
test, and the COT moved the wrong way for both. **This record makes no avatar claim.** The
constrained party is unidentified. The record says so on its face and asks the forward slice
only whether the schedule and the state hold.

---

## 1. The construction

- **Instrument.** The soybean (ZS) calendar spread, **short T1, long T2**, one full contract a
  leg (5,000 bushels; cents a bushel, $50 a point, tick $12.50; no micro). At the formation
  session — **the last session before September** — T1 is the **first listed delivery month
  strictly after November** (January, F) and T2 the next listed (March, H), from the settlement
  strip with D564's five-session formation read. The pair is fixed for the window; nothing
  rolls inside it. The runner asserts, on every positioned session, that T1's delivery month is
  after November (the survival rule).
- **Window.** Positioned on every session of **September, October and November**; **flat from
  December 1 to August 31.** No threshold in the primary cell.
- **Return space (PRIMARY).** The daily spread return `y = r1 − r2` on the held pair, same-contract
  settlement to settlement, zero on flat sessions; **sign −1** (short the spread: pays when the
  front falls against the deferred, i.e. when the carry widens).
- **The state variable, read once a window.** Stocks-to-use for the new-crop marketing year
  (`Proj.`) from the last WASDE released strictly before the formation session — the August
  report — in `data/fixtures/wasde_grains_su.csv`, filtered first.
- **Dollar book.** One ZS short T1, one ZS long T2; $6 a round trip plus one tick per leg per
  side; **four sides a window**.

| cell | | |
|---|---|---|
| **B — F/H, Sep → Nov, ungated (PRIMARY)** | short F / long H, one pair, every window | the construction; flat by default |
| **B gated on stocks-to-use (SECONDARY, seen)** | the same pair, positioned only if the August stocks-to-use is **≤ the median of every prior August's** in the fixture (2010 on; ≥ 3 prior, first decision 2013); flat otherwise | the one declared cut, unchanged from D569, where it opened four windows and all four paid; **seen**, declared, non-promotable on its own |
| **A — the rule-rolled cousin under the same mask (DIAGNOSTIC)** | short the first-nearby by the grains rule (delivery ≥ *m*+2), T2 next, re-read monthly, Sep → Nov: X/F then F/H, one roll inside the window | D569's object; the placement null N1 is built on its always-on series because that series exists every session |
| control: A always on | the same, every month, rolled monthly | **B must beat it per positioned day, and it must be ≤ 0** |

**Family for N2: the primary and the gated cell.**

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of B's daily return, 2016-01-04 → 2023-12-29, flat
> sessions included as zeros**, monthly block-bootstrap SE, Sortino beside it (R17). Beside it:
> the 24 positioned months in sample (2016–2023, eight windows), their mean, median, hit, worst;
> the 39 on 2011–2023; per month of the window; per window; **the primary window contains no
> 2012**, which the record states as the reason the in-sample number is the honest one.

## 3. Nulls

- **N1 — the schedule's placement.** D555's rotation of the Sep → Nov mask through the primary
  span over A's always-on series, purged 252 both ends, enumerated (exact). It asks whether
  September → November is a special placement for a short nearby soybean spread. It is run on
  A because only A exists every session; its rank is reported for A-under-the-mask, and D569's
  2011–2023 value (0.972) is seen — the 2016–2023 value is not.
- **N2 — the construction's placement, twelve ways.** B's exact rule — form at the last session
  before month *m*, hold *m*, *m*+1, *m*+2, T1 the first delivery strictly after the third
  holding month, T2 the next, short T1 / long T2, one pair — placed at each of the twelve
  calendar months; *m* = 9 is the primary. Scored on the 2016–2023 daily book and on 2011–2023.
  Enumerated (twelve), so the finest rank is 11/12. The family (primary, gated) is scored
  against the twelve placements of the ungated rule.
- **N3 (diagnostic)** — the always-on control's per-day return and Sharpe.

**PASS requires: the primary > 0; B's 2016–2023 Sharpe the best of the twelve N2 placements;
A-under-the-mask above N1's p95 on 2016–2023; AND B's mean return per positioned day above
the always-on control's, with the control's ≤ 0.**

## 4. Predictions — in the runner's quantities, all informed by seen data and said so

| # | prediction | value declared | source |
|---|---|---|---|
| **P-1** (primary) | B gross Sharpe 2016–2023 **> 0**, point **0.5 – 1.2** | | the seen eight windows 2016–2023 average +0.35 % on a window sd near 0.4 %, one window a year, diluted by nine flat months |
| **P-2** (per position) | hit of the 24 positioned months **≥ 0.60**; median monthly return > 0; per-window hit 2011–2023 ≥ 0.75 (seen 11 of 13) | | the seen per-month split averages 0.67 |
| **P-3** (control) | B's mean per positioned day **> 0** and **> A's under the mask**; A always-on **≤ 0** per day | | D569: +0.42 (A window) vs −1.15 (always on); B's per-day is the seen per-window mean over ~63 sessions, +0.8 bp |
| **P-4** (N1) | A-under-the-mask N1 rank on 2016–2023 **≥ 0.90** | | D569 read 0.972 on 2011–2023 |
| **P-5** (N2) | B is the **best of twelve placements** on 2016–2023 and on 2011–2023; the placement two months later (Nov → Jan) is **negative** | | D569's calendar profile: the short earns only in Sep and Nov and loses Dec → Aug |
| **P-6** (the gate, seen) | the gated cell's mean per positioned window ≥ the ungated's over the decidable windows and its hit ≥; in sample the gate opens 2016, 2021, 2022, 2023 | | seen in D569; recorded, not a test |
| **P-7** (2012) | on 2011–2023 without 2012: mean ≥ +0.25 %, short pays ≥ 9 of 12; 2012 ≤ 55 % of the thirteen-year total | | seen: +0.28 %, 10 of 12, 50 % |
| **P-8** (tail) | B's worst positioned month, 2011–2023, **> −1.5 %**; worst window > −0.5 % (seen −0.17 %) | | the cousin's worst month was −1.29 % |
| **P-9** (vehicle) | daily σ of the dollar book **< $150** over positioned sessions | | D569's cousin: $50 |
| **P-10** (cost) | modelled cost **< 20 % of gross** in dollars, 2016–2023 (four sides at $3 + $6.25 on a ~$50,000 leg against a seen +0.35 % window) | | no roll inside the window |
| **P-11** (falsifiers) | B **not** the best of twelve → the harvest placement is not special for this construction; A-under-the-mask below N1 p50 → no schedule; B per day below A per day → the object choice was wrong and the roll was not the cost; gated hit < ungated → D569's four windows were the composition, not the state | | |

Reported beside them: net beside gross with cost and breakeven per side; per-month, per-window,
per-year; the pairs and formation basis; the dollar book's total, max DD, hit, skew, σ; the C-d
line; the twelve N2 placements' Sharpes in full; the COT through-window figure for the record
(seen; no prediction).

## 5. The component line

The dollar book is the component line: C-a net Sharpe at one contract a leg, C-c skew, C-d
daily σ, hit, gross beside net, ρ with entry #2 (absent: the MACD arm's daily P&L is not on
disk; expected near zero by instrument and clock). Entered in `COMPONENTS_PROP.md` on its
numbers whether or not it clears. **If it PASSES and clears C-a, it is the ledger's fourth
entry** (#3 was removed in D566), entered as a component written as seen with the avatar
unsupported, and the assembled book's forward read — the MACD arm plus this spread on the ZS
2024+ slice — is the principal's call, pre-registered separately when taken. **If it clears
C-a and sits below its N2 best-of-twelve, D468's provisional path applies.**

## 6. Runner assertions

- **Pair by a second path:** T1/T2 at every window's formation recomputed from the raw strip by a
  pandas implementation of the survival rule (D564's `strip_pivot` route); exact; proven to raise
  on a shifted formation.
- **Survival:** on every positioned session T1's delivery index > November's; proven to raise
  on the ≥ *m*+2 rule's pair (X in September).
- **Held-contract:** both legs settle at every positioned month's last session, 100 %.
- **Lag:** the mask is non-zero only on sessions strictly after a formation session and inside
  the declared months; pandas calendar path agrees; proven to raise on a formation-session mask.
- **Sign in money, short:** on the positioned session with the largest `dP1 − dP2` the dollar
  P&L equals `−(dP1 − dP2) × 50`; proven to raise on a negated and a mis-lagged grid.
- **Right quantity:** the mask changes only at month boundaries; proven to raise on a daily grid.
- **Gate by a second path:** pandas expanding median on the August rows; proven to raise on
  shifted decisions (the current-year-median break is recorded as inert if it is).
- **N2 by construction:** placement *m* = 9 reproduces the primary's daily series exactly.
- **Exactness guard** on 20 offsets against the plain loop for N1. `REQUIRED_OUTPUTS`;
  `max_drawdown_convention` first; `encoding="utf-8"` everywhere.

## 7. What is read, and what is not

The ZS settlement strip 2010-06 → 2023-12-29; the breadth fixture for the calendar and the
specification; the WASDE fixture filtered to releases before 2024-01-01; the COT legacy
fixture through 2023 for the recorded figure. **Not read: anything from 2024-01-01 on, on any
source.**

## 8. What this record does not do

No summer construction (the mechanism's other side, unseen as a schedule); no cut other than
the one declared; no netting with any other window or root; no avatar claim. If it passes, the
forward read is the principal's call and offers the 2024 and 2025 harvests.
