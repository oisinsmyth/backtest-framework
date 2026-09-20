# D568 — PRE-REGISTRATION: the **corn post-harvest carry narrowing, flat by default** — long the March contract, short the May, held December 1 → the last session of February, one contract a leg; the stocks-to-use gate as a declared secondary cell

**Pre-registration. Committed before the runner exists (R8). Result in a separate file.** In
sample 2016-01-04 → 2023-12-29; the long window 2011 → 2023 is a declared diagnostic; **the 2024+
slice is RESERVED AND NOT READ, on every source — the settlement strip, the breadth fixture, the
COT fixture and the WASDE fixture alike.** Nothing admitted (R15).

*2026-09-20. The second per-root avatar pre-registration after D565 (NG). D567's Stage 0 designed
the grains at harvest before reading them and found the merchant-at-harvest avatar failed on corn:
the harvest carry is priced by the end of August. What survived on corn was the window the design
declared for the other half of the merchant's year — **the post-harvest carry narrowing**, December
through February, when the merchant who was paid the carry at harvest to hold the crop sells it
into the pipeline, the deferred's premium over the nearby is earned down, and the front gains
against the deferred. Stage 0 read it at +0.74 % a window, the front gaining in 9 of 12 years
(t +2.57), and monotone in the state variable the design declared: tight stocks-to-use, the
front gains most (+1.11 %); full, least (+0.24 %). That is the construction pre-registered here,
with its window, direction and state variable as declared in D567 and nothing added from the
table.*

**Stage 0 disclosure — what has been seen, exactly.** The per-year window return of the H/K
spread and of the H outright over December → February, 2011 → 2022 (twelve windows; the 2023
window's January and February are in the reserved slice); their Spearman correlation with
stocks-to-use, with the formation carry ratio and with the COT commercial net short at formation;
the in-sample stocks-to-use terciles of those twelve windows. All in `data/stage0_d567_grains.json`.
**Not seen:** the daily path inside any window; the per-month split (December, January, February);
the placement null; the cost; the dollar book; the always-on control; the real-time gate's
composition; the COT's movement *through* the window. The primary statistic below is on the
daily book, which was not read, but its sign and rough size follow from the seen table and the
point-range prediction says so.

**Correction to the D567 record, made here and dated.** D567's RESULT describes the WASDE fixture
`data/fixtures/wasde_grains_su.csv` as 978 rows over 163 releases ending 2023-12-08. That is the
in-memory table Stage 0 scored on. The file it wrote holds every release the raw cache has —
1,170 rows over 195 releases, 2010-04-09 → 2026-09-11 — because the builder wrote the file before
applying its own date filter. The 2024+ rows are a state variable, not an outcome, and nothing in
Stage 0 read them; but a fixture whose span its record misstates is a defect and this runner
**filters the fixture to releases before 2024-01-01 as its first act on it** and asserts the
count it scored on. The correction paragraph is appended to D567's RESULT with this record's
result commit.

---

## 1. The construction

- **Instrument.** The corn (ZC) calendar spread, **long T1, short T2**, one full contract a leg
  (5,000 bushels; the fixture quotes cents a bushel, $50 a point, tick $12.50; ZC has no micro
  and the breadth meta says so). T1 is chosen at each formation by D564's grains delivery rule —
  the first listed delivery month **≥ *m*+2** — and T2 is the next listed month with a settlement.
  For a formation at the last session of November that is **March (H) / May (K)**; at the last
  sessions of December and January it is the same pair, so the position is one pair held through
  the window and nothing rolls inside it. The runner asserts, every positioned month, that T1's
  delivery month is strictly after the window's last month (**the survival rule**, D567's
  correction): a pair that could expire inside the window is a runner error, not a data fact.
- **Window.** **Positioned on every session whose calendar month is December, January or
  February**; formed at the last session before December (the pair is re-read at each month-end
  under the same rule and must come out the same); **flat from March 1 to November 30.** No
  threshold, no signal: the schedule is the whole rule in the primary cell.
- **Return space (PRIMARY).** The daily spread return `y = r1 − r2` on the held pair, same-contract
  settlement to settlement, zero on flat sessions; **sign +1** (long the spread: it pays when the
  front gains on the deferred, i.e. when the carry narrows). Single root, so the book is the
  series.
- **The state variable, read once a window.** Stocks-to-use = ending stocks ÷ total use for the
  new-crop marketing year (`Proj.`), from the **last WASDE released strictly before the window's
  formation session** — the November report — in `data/fixtures/wasde_grains_su.csv`, filtered to
  releases before 2024-01-01 before any use.
- **Dollar book.** One ZC long T1, one ZC short T2; $6 a round trip plus one tick per leg per
  side; **four sides a window** (open two legs on the first December session, close two on the
  last February session), plus four more only if the rule changes the pair at a month boundary
  inside the window (it should not; the runner counts it). The pair's P&L from the strip's
  settlement changes × $50.

| cell | | |
|---|---|---|
| **spread, Dec → Feb, ungated (PRIMARY)** | long H / short K, one pair, every window | the construction; flat by default |
| **spread, Dec → Feb, gated on stocks-to-use (SECONDARY)** | the same pair, positioned in a window **only if** the November stocks-to-use is **≤ the median of every prior November's** stocks-to-use in the fixture (2010 onward; at least three prior Novembers, so the first gated decision is November 2013); flat otherwise | the state variable, real-time, one cut and that cut is not read from any table; **diagnostic** — the in-sample composition of this cell can be worked out by hand from the seen Stage 0 stocks-to-use column, so the cell is declared and not promotable |
| control: spread, always on | long T1 / short T2 by the same rule, every month, rolled at each month-end where the rule changes the pair | the flat-by-default rule must beat it **per day positioned** |

**Family for N2: the two declared cells** (primary and gated). The control is a control, not a
member. The per-month decomposition (December, January, February) is diagnostic. The in-sample
stocks-to-use terciles of the positioned windows are reported as the state test, with the cut
points printed, and are the seen cut, not a rule.

## 2. The statistic

> **PRIMARY: gross annualised Sharpe of the daily spread-book return, 2016-01-04 → 2023-12-29,
> flat sessions included as zeros**, with a monthly block-bootstrap SE; Sortino beside it (R17).
> Beside it: the per-window statistics — the positioned windows in sample (2015-16's January and
> February, 2016-17 → 2022-23 complete, 2023-24's December: 24 positioned months), their return,
> mean, median, hit, worst; the 39 positioned months over 2011 → 2023; the same per month of the
> window.

## 3. Nulls

**N1 — window placement.** D555's rotation applied to this book: the held-sign series is rotated
within the primary span by a common offset, purged 252 sessions at both ends, enumerated (every
offset, SE exactly 0), so every surviving offset is a three-months-a-year long-spread schedule
placed at a different phase of the calendar. The primary's rank in N1 is the direct test of "the
post-harvest window and not any other placement" — the seasonal question D567's vacuous
leave-one-year-out control could not ask. **N2** — the family maximum over the two cells, same
rotation. **N3 (diagnostic)** — the always-on control: if its Sharpe exceeds the primary's, the
window is a drawdown instrument on a positive carry-narrowing book, not a selector.

**PASS requires: the primary > 0, above its N1 p95, the family maximum above its N2 p95, AND the
primary's mean return per positioned day above the control's mean per day.**

## 4. Predictions — in the runner's quantities

| # | prediction | value declared | source |
|---|---|---|---|
| **P-1** (primary) | gross Sharpe 2016–2023 **> 0, above N1 p95**; point **0.3 – 0.9** | | the seen per-window table: about +0.7 % a window against a window sd near 1 %, one window a year, diluted by nine flat months; the range is informed by seen data and the record says so |
| **P-2** (per position) | hit rate of the 24 positioned months **≥ 0.55**; median monthly return > 0; per-window hit on 2011–2023 ≥ 0.65 (seen: 9 of 12) | | the window hit is seen; the monthly hit is not |
| **P-3** (control) | mean return per positioned day of the primary **> the always-on control's**, and the control's Sharpe **< the primary's** | | Stage 0's other corn windows: the Z/H harvest spread +0.27 % over Sep–Nov and the weather-window spread −0.39 % over Jun–Aug, both smaller per day than the post-harvest window; the always-on book carries them |
| **P-4** (placement) | primary's N1 rank **≥ 0.90** | | the window is the one the mechanism names; if any three-month placement does as well, the effect is the corn curve's average carry-narrowing and not the post-harvest schedule |
| **P-5** (tail) | worst positioned month of the primary **> −2 %**; worst window on 2011–2023 > −1 % (seen: −0.47 %) | | the spread is tail-limited; a month worse than −2 % on a long H/K spread would mean an inverse building into the front, which is the tight-stocks summer story, not the winter one |
| **P-6** (the state, seen and real-time) | (a) seen, recorded: Spearman(stocks-to-use, window return) on 2011–2022 **≤ −0.3** (Stage 0 read −0.43) with the tight tercile above the full; (b) **unseen, the test:** the gated cell's mean return per positioned window **≥ the ungated cell's** over the windows in which the gate could decide (2013 onward), and its per-window hit ≥ the ungated's | | (a) is the design's state variable with the design's sign; (b) is whether a real-time reading of it, with one declared cut, keeps the good windows and drops the poor ones |
| **P-7** (vehicle) | daily σ of the dollar book **< $150** over positioned sessions (one full contract a leg; ZC's outright one-contract σ is $376 a day by D564, the spread's a fraction of it) | | C-d passes with room; if the spread's σ is above $150 the pair is not the tail-limited object the mechanism describes |
| **P-8** (the avatar) | in the COT legacy fixture (on disk), the corn **commercial net short share of open interest** — (short − long) ÷ OI — at the last report before the window's last session is **below** its value at the last report before formation in **≥ 8 of 12 windows**, 2011–2022, and in ≥ 4 of 7 in sample | | the merchant is long cash and short futures at harvest; selling the stored crop through the winter lifts the hedge; if commercial net short does not fall through the window the merchant's selling is not what moves this spread and the record says the avatar is unsupported whatever the P&L |
| **P-9** (cost) | modelled cost **< 25 % of the gross** positioned-month mean (four sides a window at $3 + $6.25 a side on a ~$25,000 leg is about 15 bp a window against a seen +74 bp) | | cost is not the question on a full-size grain spread held three months |
| **P-10** (falsifiers) | primary **below N1 p50** → there is no post-harvest carry premium here beyond the curve's average; control beating the primary per day → the schedule adds nothing; P-8 failing → the merchant avatar is unsupported on corn in both halves of its year and the record closes the avatar, not the root; P-6(b) failing while P-1 holds → the state variable is a story and the calendar is the rule | | |

Reported beside them: net beside gross with the four-sides-a-window cost and breakeven per side;
per-window and per-month tables; per-year; the basis at each formation in cents and as a ratio to
full carry (D567's convention, 5 ¢ a month plus interest at 2.5 %, declared and flat); the T1/T2
pairs held; the dollar book's total, max drawdown, hit, skew and σ; the C-d line; the seen
stocks-to-use tercile table with its cut points.

## 5. The component line

The dollar book above is the component line: C-a net Sharpe at one contract a leg under the cost
that size pays, C-c skew, C-d daily σ, hit, gross beside net, ρ with the ledger's live entry
(absent: the MACD arm's daily P&L is not on disk; by instrument and clock — a corn calendar spread
held three months against an NQ day session — expected near zero, which is an expectation). A
single-root, flat-by-default component is entered in `COMPONENTS_PROP.md` on its numbers whether
or not it clears; under D468's rule a component that clears C-a and sits below its family null's
p95 enters PROVISIONAL. The assembled book's forward read, if any, is the principal's call and is
pre-registered separately when taken; the record will say what the ZC 2024+ slice offers (two
windows and a December).

## 6. Runner assertions

- **Pair by a second path:** T1/T2 at every formation recomputed from the raw strip by a pandas
  implementation of the ≥ *m*+2 rule (D564's `strip_pivot` route, never `choose_nearby`); exact
  agreement; proven to raise on a shifted formation date.
- **Survival audit:** for every positioned month, T1's delivery month index > the window's last
  month index; proven to raise when the pair is replaced by the ≥ *m*+1 rule's.
- **Held-contract audit:** both legs settle at each positioned month's last session in 100 % of
  positioned months.
- **Lag audit:** the position grid is non-zero only on sessions strictly after a formation session
  and within the declared months; an independent pandas calendar path builds the same mask;
  proven to raise on a grid that starts on the formation session.
- **Sign in money:** on the positioned session with the largest `dP1 − dP2`, the dollar P&L equals
  `+(dP1 − dP2) × 50` exactly; proven to raise on a negated and a mis-lagged grid.
- **Right quantity:** the grid changes only at a month boundary; proven to raise on a daily grid.
- **Gate by a second path:** the gated mask recomputed by a pandas expanding-median on the
  November rows; exact agreement; proven to raise when the median includes the current year.
- **Exactness guard** on 20 offsets against the plain loop. `REQUIRED_OUTPUTS`;
  `max_drawdown_convention` first; `encoding="utf-8"` everywhere.

## 7. What is read, and what is not

The settlement strip for ZC from 2010-06 (warm-up) through **2023-12-29**; the breadth fixture for
the session calendar and the ZC specification; the WASDE fixture filtered to releases before
2024-01-01; the COT legacy fixture (commercial category) through 2023. **Not read: any session,
release or report from 2024-01-01 onward, on any source.**

## 8. What this record does not do

No threshold beyond the one declared expanding median; no sizing beyond one contract a leg; no
other window on corn (the harvest and weather windows are Stage 0 findings and stay there); no
other root; no netting with any other window. A flat result is a result about the corn
post-harvest carry narrowing on this window and no more. If it passes, the forward read is the
principal's call and the record will say what the slice offers.
