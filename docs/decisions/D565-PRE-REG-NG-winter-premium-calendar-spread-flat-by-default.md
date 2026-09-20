# D565 — PRE-REGISTRATION: the **NG winter-premium calendar spread, flat by default** — short the first-nearby, long the second, held only through the EIA withdrawal season (November → March), one micro a leg

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29; the long window 2011 → 2023 is a declared diagnostic; **the 2024+
slice is RESERVED AND NOT READ.** Nothing admitted (R15).

*2026-09-20. The first per-root avatar study after D564. The principal asked for each root's
strategy built to the party its constraint binds, flat by default. NG's Stage 0 (this session,
diagnostic, not a record) found that the storage state the deposit's mechanism names — working gas
against its five-year band — predicts nothing about the next month of the NG curve once the
calendar is removed (residual Spearman −0.02, year-block p 0.7), and that the calendar itself is
where the curve moves: the front contract falls into the withdrawal season and the front-minus-
second spread is small, steady and short-paying. The avatar is therefore not the storage owner but
the **obligated winter buyer** — the utilities and distributors that must secure supply and pay a
premium into the winter contracts, which decays as the season resolves without a cold shock, and
reverses with a tail when one arrives. This is hedging pressure with a schedule, and a schedule
is what flat-by-default needs.*

**Stage 0 disclosure.** Before this was written, the per-year return of the front and of the
spread was read for five fixed calendar windows — October, November, December, February, March —
on 2011–2023. The window declared below is **the EIA withdrawal season, November 1 → March 31**,
which was chosen from the agency's definition and not from that table: it includes January, which
was not read, and excludes October, which was read and was flat. December's outright front return
was the strongest single window seen; it is declared as a secondary cell and marked seen.

---

## 1. The construction

- **Instrument.** The NG calendar spread: **short T1, long T2**, where T1 is the first-nearby by
  D564's energy delivery rule (delivery month ≥ *m*+3, so the held contract never expires inside
  the holding month) and T2 the next listed delivery month, chosen at formation from the
  settlement strip with D564's five-session formation read.
- **Windows.** Five monthly positions a season: formed at the **last session before** each of
  November, December, January, February and March, held to that month's last session, then
  re-formed (the pair rolls with the delivery rule). **Flat from April 1 to October 31.** No gate,
  no state variable, no threshold: the schedule is the whole rule.
- **Return space (PRIMARY).** The daily spread return `r1 − r2` on the held pair, same-contract
  settlement to settlement, zero on flat sessions; sign −1 (short the spread). The book return
  series is this one root's, so the equal-average machinery is the identity.
- **Dollar book.** One MNG (2,500 MMBtu) short T1 and one MNG long T2; $3 a round trip plus one
  tick per leg per side, four sides a month (open and close two legs); the pair's P&L from the
  strip's settlement changes × usd_per_point.

| cell | | |
|---|---|---|
| **spread, withdrawal season (PRIMARY)** | short T1 / long T2, Nov → Mar | the avatar's construction |
| December outright, secondary (**seen in Stage 0**) | short T1 alone, December only | the premium's largest decay month; declared, not promotable |
| control: spread, always on | short T1 / long T2, every month | the flat-by-default rule must beat it **per day positioned** |

**Family for N2: the two declared cells** (primary and December outright). The control is a
control, not a member. Per-month decomposition (Nov, Dec, Jan, Feb, Mar) is diagnostic.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of the daily spread-book return, 2016-01-04 → 2023-12-29,
> flat sessions included as zeros**, with a monthly block-bootstrap SE; Sortino beside it (R17).
> Beside it, the per-position statistics: the 40 monthly returns (8 seasons × 5), their mean,
> median, hit rate, worst, and the same on 2011–2023 (65 months).

## 3. Nulls

**N1 — window placement.** D555's rotation applied to this book is a rotation of the schedule
through the calendar: the held-sign series is rotated within the span by a common offset, purged
252 sessions at both ends, so every surviving offset is a five-month-a-year short-spread schedule
placed at a different phase. The primary's rank in N1 is the direct test of "the withdrawal season
and not any other placement". **N2** — the family maximum over the two cells. **N3 (diagnostic)** —
the control's own daily return, which is the same position every day: if the always-on control's
Sharpe exceeds the gated primary's, the window is a drawdown instrument, not a selector.

**PASS requires: the primary > 0, above its N1 p95, the family maximum above its N2 p95, AND the
primary's mean return per positioned day above the control's mean per day.**

## 4. Predictions — in the runner's quantities

| # | prediction | value declared | source |
|---|---|---|---|
| **P-1** (primary) | gross Sharpe 2016–2023 **> 0, above N1 p95**; point **0.4 – 0.9** | | Stage 0: about +0.5 % a positioned month at a monthly sd near 1 %, diluted by seven flat months |
| **P-2** (per position) | hit rate of the 40 positioned months **≥ 0.60**; median monthly return > 0 | | Stage 0: 10 of 13 seasons in each of Nov, Feb, Mar |
| **P-3** (control) | mean return per positioned day of the primary **> the always-on control's** mean per day, and the control's Sharpe **< the primary's** | | Stage 0: always-on short spread +0.29 % per 21 sessions against +0.5 % in the windows |
| **P-4** (placement) | primary's N1 rank **≥ 0.90** | | the season is the placement the mechanism names |
| **P-5** (tail) | worst positioned month of the primary **> −3 %** in return space; December outright's worst month **< −10 %** (the 2018 spike, seen) | | the spread is tail-limited where the outright is not |
| **P-6** (the avatar) | in the COT legacy fixture (on disk), NG **commercial long share of open interest** in the formation months (October, November) exceeds its April–September level in **≥ 9 of 13 years**, 2011–2023 | | obligated buyers hedge forward into winter; if they do not show up in the positioning data the avatar is a story |
| **P-7** (vehicle) | daily σ of the dollar book **< $150** over positioned sessions (one micro a leg; D564's outright MNG σ $150) | | C-d passes with room |
| **P-8** (secondary, seen) | December outright: mean front return over 2011–2023 **< 0**, short paying in ≥ 8 of 13 | | Stage 0 read −11.1 %, 10 of 13; recorded as seen |
| **P-9** (falsifiers) | primary **below N1 p50** → there is no seasonal spread premium here; control beating the primary per day → the schedule adds nothing; P-6 failing → the avatar is unsupported and the record says so whatever the P&L | | |

Reported beside them: net beside gross with the four-sides-a-month cost and breakeven per side;
per-month and per-season tables; per-year; the basis at each formation; the T1/T2 pairs held;
the dollar book's total, max drawdown, hit, skew and σ; the C-d line.

## 5. The component line

The dollar book above is the component line: C-a net Sharpe at one micro a leg under the cost that
size pays, C-c skew, C-d daily σ, hit, gross beside net, ρ with the ledger's live entry (absent:
its daily P&L is not on disk). A single-root, flat-by-default component is entered in
`COMPONENTS_PROP.md` on its numbers whether or not it clears.

## 6. Runner assertions

- **Pair by a second path:** T1/T2 at every formation recomputed from the raw strip by a pandas
  implementation of the delivery rule (D564's `strip_pivot` route, never `choose_nearby`); exact
  agreement; proven to raise on a shifted formation date.
- **Held-contract audit:** both legs settle at the window's last session in 100 % of positions.
- **Lag audit:** the position grid is non-zero only on sessions strictly after a formation session
  and within the declared months; an independent pandas calendar path builds the same mask;
  proven to raise on a grid that starts on the formation session.
- **Sign in money:** on the positioned session with the largest `dP1 − dP2`, the dollar P&L equals
  `−(dP1 − dP2) × usd_per_point` exactly; proven to raise on a negated and a mis-lagged grid.
- **Right quantity:** the grid changes only on the first session of a declared month and the
  session after its last; proven to raise on a daily grid.
- **Exactness guard** on 20 offsets against the plain loop. `REQUIRED_OUTPUTS`;
  `max_drawdown_convention` first; `encoding="utf-8"` everywhere.

## 7. What is read, and what is not

The settlement strip for NG from 2010-06 (warm-up) through **2023-12-29**; the COT legacy fixture
for P-6 through 2023; the breadth fixture for the session calendar and the MNG specification.
**Not read: any session from 2024-01-02 onward, on any source.** No EIA series enters the rule
(Stage 0 showed it adds nothing beyond the calendar); it is on disk for the record.

## 8. What this record does not do

No state gate; no threshold; no sizing beyond one micro a leg; no other root. A flat result is a
result about the NG withdrawal-season spread premium on this window. If it passes, the forward
read is the principal's call and offers two seasons; the record will say so.
