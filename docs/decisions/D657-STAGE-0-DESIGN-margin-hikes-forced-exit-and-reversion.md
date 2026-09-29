# D657 STAGE 0 DESIGN — margin-driven deleveraging: does a CME margin increase force positions out, does the price it moves come back, and does it forecast volatility beyond what the volatility already said?

*Drafted 2026-09-28 on the principal's word ("Write the margin deleveraging Stage 0"). Committed alone, before any
margin data is fetched and before its runner exists (R8). **No margin event has been read, and no price has been
read around one.** Personal book for any construction; the volatility premise (M3) would route to the prop ledger as
an overlay.*

## 0. What this tests, and what is already known against it

`ALPHA_PROGRAMME.md` §5.3 ranks "margin-driven deleveraging" as partially derivable (the trigger is public, the
response is not), and no record here has touched it. The mechanism: CME Clearing raises the initial margin on a
contract; holders who cannot or will not post more must cut; if that trading is forced, it should leave a footprint.

**Two papers already set the bar for this record, and the stronger one says the obvious trade does not exist:**

- **Hedegaard (2014), *Causes and Consequences of Margin Levels in Futures Markets*,** 16 commodity contracts,
  2000–2011, 597 changes (350 increases, mean +20 %). Margins are set at about **2.5 daily standard deviations** of the
  contract's own return. After a typical increase, **open interest grows 0.09 % a day more slowly than the control group
  for 50 days** (speculators −0.12 %, hedgers −0.06 %), and **price impact rises about 15 %** (9 % beyond a control group
  whose own impact also rose: a funding spillover). **Realised variance jumps more than 50 % on the day of the increase
  and stays 50–80 % higher for two weeks.** **No abnormal return follows an increase**, including in an interaction
  with the speculators' net position, a test with 95 % power against a shock of a tenth of a daily standard deviation.
  The reason he gives: **both sides exit, and the speculators' long/short ratio does not change.** Every contract has
  two holders; forced exits that are symmetric push no price.
- **Abruzzo and Park (2014, FEDS 2014-86),** CME margins: CME **raises margins quickly after volatility spikes and
  lowers them slowly**, and **announces a change at least 24 trading hours before it takes effect.** A margin increase
  is therefore a lagged, public label on a volatility spike, and its effective date is known in advance.

So this record does **not** re-test Hedegaard's directional claim (a hike moves the price one way, or one way given
positioning); that has been tested with power and failed. It asks three different things, each of which his findings
leave open:

1. **M1: does the forced exit happen on these roots and in this era** (33 roots, 2020–2023, and 2010–2019 if the build
   gate in §2 passes)? M1 is the foundation: if open interest does not fall, M2 has nothing to explain.
2. **M2: does the price move during the forced-exit window revert afterwards, whichever way it went?** Symmetric exits
   push no *average* price, but a 15 % rise in price impact means whatever order imbalance the exits leave on a given
   day moves the price further than usual, and impact that is transient reverts. This premise is direction-agnostic:
   it conditions on the window's own move, not on anyone's position.
3. **M3: does a margin increase forecast volatility beyond the volatility that caused it?** Hedegaard's two weeks of
   higher variance may be CME anticipating correctly. The question is the residual against a forecast built only on
   data before the notice. It is not a futures trade: if it holds, it routes to a risk overlay on the components
   already in `COMPONENTS_PROP.md` (size down after an increase), scored there.

## 1. The events

**Source (A), 2020 → the in-sample end: CME's per-product margin histories** ("List of Historical Margins by Name",
`cmegroup.com/solutions/risk-management/margin-services/historical-margins.html`), one PDF per clearing code, 2020 to
present, split at each product's SPAN 2 migration (energy 2023-10-20, equity index 2024-10-18). **33 of the 36 breadth
roots have one:** ES, NQ, YM, NKD, CL, NG, RB, HO, GC, SI, PL, HG, ZN, ZB, ZF, ZT, UB, TN, SR3, 6E, 6J, 6B, 6A, 6C, 6S,
ZC, ZS, ZW, ZL, ZM, LE, HE, BTC. RTY, BZ and PA do not, and are out.

**Source (B), 2010–2019: the clearing advisories,** numbered PDFs at
`cmegroup.com/tools-information/lookups/advisories/clearing/files/Chadv{yy}-{nnn}.pdf` (probed 2026-09-28: `10-100` and
`12-521` exist; `08-100` does not). Each performance-bond advisory lists the products changed, their current and new
requirements, the notice date and the effective date. Walked by number; only performance-bond advisories are kept.

**Both sources are CME's pages and need the principal's approval to fetch** (the site refuses a script and serves the
files only to a browser session): about 40 history PDFs (gold's is 1.46 MB) and, for (B), about 500 advisories a year
at about 40 KB, most of them not about margins. **Nothing is fetched until the principal says so.**

**The event:** an **increase in the outright initial margin** for the product's **front** tier (the first contract
month or months, as each source labels it; the speculator or "non-member" rate where the source distinguishes it),
by at least **5 %**. The notice date N and the effective date E are recorded; source (A) carries only E, so N is taken as
the business day before E and checked against (B) wherever both exist. **CME's rates take effect after the close on E**,
so the first session traded under the new margin is **E+1**. Increases on the same root within 10 sessions of each
other are merged into one event dated by the first (the second is the same episode).

**The in-sample window: events with E ≤ 2023-12-15**, so every window in §3 ends by 2023-12-29. **Nothing after
2023-12-29 is read for prices.** The loader filters before 2024-01-01 and asserts after. Margin *events* after 2023
may appear in the parsed table; the runner drops them before joining any price. D626's sealed energy sample is
post-vault and not touched.

**Clustering, stated before the run:** CME changes many products in one advisory (March 2020 and 2022 especially).
Every standard error is clustered by notice date, and the effective sample size (distinct notice dates) is reported
beside the event count.

## 2. The build gate (G0), before any premise

The margin table is parsed from PDFs whose text is font-encoded (it did not extract in a browser probe), so the parse
is a claim that needs checking before anything is joined to it.

| gate | declared |
|---|---|
| **G0-a** | Source (A) parses for all 33 roots: every row has a date, a product and an amount, and amounts are positive |
| **G0-b** | Hand check: for three roots (GC, CL, ZC), ten rows each, drawn by seed 657, printed beside the page they came from and checked by eye before the run continues |
| **G0-c** | Source (B) against (A) where they overlap (2020–2023): ≥ 95 % of (A)'s increases are found in (B) on the same effective date and the same new amount. **If G0-c fails, 2010–2019 is dropped** and the study runs on 2020–2023 alone, with its power stated |
| **G0-d** | The count of in-sample increases per root and per year is printed before any price is read. **If fewer than 100 events (after merging) remain, M2 and M3 are reported UNRESOLVED by power** and only M1 is scored |

## 3. The premises

**Returns** are settlement to settlement on the breadth strip (`fut_settle_strip.csv.gz`), in log points, on **the
nearest contract whose first notice day (or last trading day, for cash-settled roots) is at least ten business days
after E+7**: no window holds a physically delivered contract near delivery (the principal's standing rule), asserted.
**Open interest** is the root total from the `statistics` schema (stat_type 9), volume-filtered so dead contracts do not
carry forever (D521, D526's `INT64_MAX` sentinel dropped), and aligned to the session it describes: CME publishes
open interest the evening before the trade date it is keyed on (data-available). **Realised variance** is the sum of
squared hourly log returns across the day session in `fut_breadth_hourly.csv.gz`, Sunday placeholders dropped (D555).

**The control, for every premise: the same root on days with the same volatility state and no margin change.** A
margin increase follows a volatility spike (Abruzzo and Park), so a control that ignores volatility compares a
volatile week with an average one (the rule: a control must share the treatment's nuisance). For each event, the
control pool is every session on the same root that (i) is at least 20 sessions from any margin change on that root,
(ii) has trailing 20-session realised volatility in the same within-root quintile as the event's at N−1, and (iii) has
the trailing 20-session return of the same sign. Each premise's statistic is computed on 2,000 draws of one control
date per event (seed 657), which is also the placement null: **p50, p95 (or p05) and the p95's bootstrap SE are
reported, and a margin within 2 SE is UNRESOLVED** (D373).

### M1 — the forced exit

- **Quantity:** `ΔOI = log OI(E+5) − log OI(N−1)`, the root's open interest over the notice, the effective date and five
  sessions of margin calls; its abnormal part is ΔOI less the matched control's.

| bar | declared |
|---|---|
| **M1-B1** | mean abnormal ΔOI < 0, clustered t ≤ −2.0 |
| **M1-B2** | the event mean below the control-draw null's p05 |
| **M1-B3** | negative in every leave-one-year-out fit |

### M2 — the forced-flow move reverts

- **The window:** `W = log F(E+2) − log F(N−1)`, from before the notice to two sessions into the new margin (anticipation,
  the effective close and the first two sessions of calls).
- **The target:** `Y = log F(E+7) − log F(E+2)`, the next five sessions, same contract, not overlapping W.
- **The statistic:** `Y = a + β · W/σ + ε`, with W scaled by the root's trailing 20-session daily volatility at N−1 so
  that roots and eras pool. Reversion means β < 0.

| bar | declared |
|---|---|
| **M2-B1** | β < 0, clustered t ≤ −2.0 |
| **M2-B2** | β below the control-draw null's p05: the same regression on matched non-event windows of the same length. Futures carry a short-horizon reversal of their own; this bar asks for more than that |
| **M2-B3** | β < 0 in every leave-one-year-out fit (2020 and 2022 hold the most events, and neither may carry it alone) |
| **M2-B4** | the trade clears its cost: `|β| × median |W/σ| × median σ` over five sessions is ≥ 3 × the root's round trip, pooled in basis points, where the round trip is D651's quoted spread at the root's settlement bucket plus $6.00 a contract (D591), at full size and at the minimum tradable size (the micro where one exists) |
| **M2-B5** | M1 passes. A reversion with no forced exit under it is some other mechanism and is not this record's to claim |

### M3 — volatility beyond its forecast

- **Quantity:** the residual `u = log RV̄(E+1 … E+10) − forecast`, where RV̄ is the mean daily realised variance over
  the ten sessions after the change takes effect and the forecast is a HAR model (Corsi 2009: daily, weekly and monthly
  averages of log RV) **fitted per root on sessions before N−1 only** and projected from N−1.

| bar | declared |
|---|---|
| **M3-B1** | mean u > 0, clustered t ≥ 2.0 |
| **M3-B2** | mean u above the control-draw null's p95 (matched days carry their own HAR residuals) |
| **M3-B3** | positive in every leave-one-year-out fit |

## 4. Routing

- **G0 fails on source (A) → no study; the record reports why.**
- **M1 fails → close the line.** Without a forced exit there is no mechanism for M2 or M3 to belong to.
- **M2 passes every bar → a pre-registration of the reversal for the personal book**, carrying the principal's
  expected-profit filter (trade an event when the point-in-time projected move `|β̂| × |W|`, β̂ from earlier events only,
  is at least twice the round trip), put to the principal before any 2024+ price is read.
- **M3 passes every bar → a pre-registered overlay test on the prop ledger's components** (halve size for ten sessions
  after an increase on the traded root), scored as the ledger scores overlays. It is not a strategy.
- **M2 and M3 both fail with M1 passing → recommend closing the line:** the exit happens and leaves nothing to trade.
- The premises are a family of three; any pre-registration that follows states it.

## 5. Why the obvious designs are not here

- **A directional return after an increase** (short the hiked contract): Hedegaard tested it, unconditionally and
  interacted with speculator positioning, with power, and found nothing. Re-running it on overlapping years spends a
  test for a known answer.
- **Margin decreases:** Hedegaard finds no volatility effect and no forced flow around them (no one is forced *in*).
  Reported descriptively in M1's table, not scored.
- **The day of the notice alone:** the notice is a public document issued after the close and the change takes effect
  a day later; any trade on it is inside the window W, which M2 already carries.

## 6. Predictions, written before the run

1. **G0-c passes**: the advisories back to 2010 parse to the 95 % standard.
2. **M1 holds**: open interest falls relative to the matched control, by 0.5–2 % over the window.
3. **M2 fails at B2**: β is negative (futures revert over days anyway) but not beyond the matched control's.
4. **M3 holds at B1**, and is borderline at B2 (the matched control also carries high-volatility persistence).
5. **2020 and 2022 hold at least 40 % of the in-sample events.**
6. **At most one of M2 and M3 routes.**

## 7. Files

`scripts/build_cme_margin_events.py` (fetch only on the principal's approval; parse; G0) →
`data/cme_margin_events.csv` + meta, manifest-hashed. `scripts/stage0_d657_margin.py` (`--selftest`, `--run`) →
`data/stage0_d657_margin.json`. The selftest must show:
- the parser reproduces a hand-typed page of one history PDF exactly;
- merging joins increases on one root within ten sessions and not beyond;
- no window holds a contract within ten business days of its first notice day;
- the control pool excludes every session within 20 of a margin change, and matches the volatility quintile and the
  trend sign;
- W and Y do not overlap, and Y's contract is W's contract;
- the HAR forecast uses no session on or after N−1 (a planted future spike leaves it unchanged);
- the M2 regression recovers a planted β = −0.3 and returns ≈ 0 on a random walk;
- the holdout guard raises on a 2024 settlement.

## 8. Amendment A1, 2026-09-28: the source, before any margin file was downloaded

The principal approved fetching both sources from 2010 at no cost ("fetch both, 2010 onwards spend no money"). **Fetching
from cmegroup.com through a scripted browser session is not used**: CME refuses automated clients, and routing around
that is evading its bot protection. **The files come from the Internet Archive instead** (`web.archive.org`, whose
CDX index and `id_` raw captures exist for programmatic use), and they are CME's own files. The index was read for
metadata only (file names, capture dates, sizes); no content was opened.

- **Source (B) becomes CME's earlier per-product histories as archived:** `{code}_2008_to_present.pdf` (latest
  captures 2015-05 to 2017-03, so running to about then), `{code}_2009_to_2013.zip`, `{code}_2014_to_present.zip`
  (captured 2017-11), `{code}_2019-to-present.pdf` (captured 2024-07, the rates products) and the 2020-to-present
  files (captured 2025–2026). **121 files, about 126 MB**, the latest capture of each, for the 33 roots.
- **The index shows a hole for most roots, from roughly late 2015/2017 to 2019/2020**, where no archived history
  covers the dates. It is reported per root, and no event is inferred inside it.
- **The clearing advisories are kept for notice dates only:** 1,841 archived `Chadv{10–16}-{nnn}.pdf` (about 75 MB,
  roughly 55–65 % of each year's numbers; none after 2016 under that path). Where an advisory covers an event, N is its
  notice date. Elsewhere N is the business day before E, and the share of events whose N was checked is reported.
- **G0-c is replaced.** Where two archived files cover the same dates for the same product (the 2008 file against the
  2009–2013 zip, the 2019 file against the 2020 file, and so on), **≥ 95 % of the increases in the overlap must agree on
  effective date and new amount**, or the later file is used alone and the disagreement is reported. G0-a, G0-b
  (now on four roots: GC, CL, ZC and one pre-2014 file) and G0-d stand.
- The fetch is `scripts/fetch_cme_margin_archive.py`: sequential, at least 1.5 s between requests, backing off on 503,
  into the main checkout's gitignored `data/raw/cme_margins/`, every file logged with its capture timestamp, URL and
  sha256.
