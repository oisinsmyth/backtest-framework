# Brief: find a NEW type of effect that predicts reversion, at micro size

## The question

The principal asked: *"What predicts reversion that we have already found?"* The answer (verified against the
records) was: reversion is real in many places in this repo, but what predicts it is the move's ORIGIN (forced or
predictable flow), the market's STATE (quiet, long dealer gamma) and the ROOT/CLOCK (some roots revert, some
continue). **Every reversal found grosses less than a micro round trip (about $3–6).** The principal then said:
*"So what I read here is that if we want to predict a reversion, then we need a new type of effect?"* — and asked for
two pairs of agents (one conservative, one creative in each) to argue until each pair has **5 solid leads**.

Your job is to find a new type of effect — a predictor, conditioner or mechanism — that tells us a move will REVERT,
by enough dollars to clear the micro cost. "New" means not a re-run of anything in the tried list below; a new angle
on a known mechanism counts only if you can say concisely what is different and why that difference should change
the outcome.

## The account's hard rules (any lead that breaks one is not a lead)

- **Prop book only:** CME micro futures (MES, MNQ, MYM, M2K, MGC, SIL, MHG, MCL, MNG, M6E, M6A, MBT, micro
  rates/ags where they exist), **ONE micro contract**, intraday, **flat by 16:10 ET**, fully algorithmic, no hedging.
  Overnight/Asian-session trades are allowed if they are flat by 16:10 ET the same trading day.
- **Costs:** `data/futures_costs.json` (micro commission about $3 a round trip plus the spread; e.g. MES about
  $4.42, MGC $5.93). **Score every effect in dollars at one micro, gross beside net.** A per-trade gross under about
  $3.5–6 does not pay, and passive entry recovers only about 2/3 of the crossing (D770).
- **The principal's dislikes (closure reasons in their own right):** rare, lumpy or spiky edges (a few days a
  year); "dumb follow" strategies; edges carried by one year (2020 or 2022) or one season; break-even trading (a
  strategy must earn when it trades, else abstain).

## Seals — NEVER violate

- **Read nothing dated on or after 2024-01-01** in any test. In-sample is ≤ 2023-12-31. (The vault 2025-03 →
  2026-09, the forward recorder and D626's energy sample are sealed. The "free last 12 months" of Databento data is
  inside the sealed period too.) Every script you write must assert this.
- Never read `data/forward/`.

## What you may and may not do

- **May:** read anything in the repo; search the web and fetch papers; write and run small Python premise tests in
  YOUR scratch directory (given in your prompt) on data already on disk; free Databento metadata calls
  (`get_cost`, `get_billable_size`) to price data.
- **May not:** edit, create, stage or commit anything inside the repo (no git writes at all); claim decision
  numbers; download or buy any data (purchases need the principal's explicit permission — you may quote a cost);
  delete, move or write into `data/raw/` (a costly cache; `data/raw/databento/china_window_2016_2023/` is PAID and
  read-only); spawn further agents.
- **Machine:** it is shared with three other agents. Use at most 4 worker processes; run anything over ~2 minutes in
  the background.

## Environment

- Repo (a git worktree): `C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674`. Raw data
  lives in the MAIN checkout: `C:\Users\O\Desktop\Projects\Backtest Framework\data\raw\` (read-only).
- **Python:** `uv run --no-sync python ...` inside the worktree (repo packages; NEVER plain `uv run`), or the system
  `python` for databento/pyarrow scripts. **The system python has no scipy** — use rank-Pearson via pandas
  `rank()` for Spearman. Never `python - <<EOF` heredocs (they hang); write a .py file and run it. All text IO with
  `encoding="utf-8"`.
- **What data exists: `docs/data-available.md`** — read it first. 1-minute futures bars on many roots (2010+),
  signed 1-minute aggressor fixtures for ES and YM (`fut_ES_signed_1m`, `fut_YM_signed_1m`), dealer-gamma series,
  calendars, settlement windows, the paid GC/MGC tick-and-quote China window (2016–2023, 18:30–03:15 ET).
  Databento `ohlcv` bars are stamped on ts_recv (see the memory notes if needed).

## What has been tried (do not re-propose without a stated, testable difference)

Read `docs/research/mean-reversion-inventory.md` (covers D1–D752), `docs/FINDINGS.md`, and `docs/internal/AITODO.md`
(D733–D771 live only in the decision records and AITODO). Summary:

**Reversion found, but sub-cost at micro:**
- Forced-flow windows: NG settlement fade +$29 t 3.98 (full size; ~$2.90 per MNG), CL settlement 14:29→14:59
  $22.34 t 3.18 (full; ~$2.23 per MCL), Treasury auction V t 4.98 (net −$1.18 a leg), gold China-open first half
  hour (ρ −0.063; +$3.18–4.25 gross vs $5.93; passive −$0.92; D765/D767/D770 — OPEN line), CME bitcoin expiry window
  (+$2.96 vs $4.31, gone after 2020; D764), month-end rebalancing (faded after 2018; D685–D687).
- Quiet state (D528): low recent vol predicts that an excursion returns (t −155) but the payoff collapses 6× —
  gross −$0.15. Long dealer gamma deepens 5-minute reversion, mostly the vol level (D683/D684; $0.22 a trade).
- Root/clock: ES first half-hour reverses into the last (−0.102, −4.3 SE, mostly 2020–22; D487); YM gives back in
  the morning while NQ continues at every clock (D727/D728); ES/NQ/YM off-hours big hours revert (D499, ES +$2.12
  gross per MES); rates revert intraday (D526); reverting days are worth +$34 a 10:00 fade if known, but no
  detector reaches the 43.5% precision needed (D756–D760).
- Personal-book equities (out of scope here): rev_5, gap-up fades in bear markets — real, lose at their spreads.

**Tested and found NOT to predict reversion:** aggressor order flow (D695, D715, D717, D770), dealer gamma as a
direction (five tries), early move size (big early moves are trend starts, D757), session anchors/VWAP/the open on
NQ (D724), yesterday's levels (sticky, not magnets, D725), pre-open variables (D756), bitcoin funding (D766), round
numbers (D761), queue imbalance at the touch (D771), volume-at-price / terrain / density / wick / overhang maps
(D189–D203, D272, D273, D384–D388, D403, D405, D411–D413), the cash close (D762), the AM-expiry open (D763), weekend
bitcoin gaps (D758), absorption at long gamma (D760), cross-asset confirmation of the China open (D767).

**The repo's recurring failure modes:** the effect is real but smaller than the micro round trip; a map/level is a
location not a barrier; a score is momentum in disguise; the edge lives in 2020–2022; a rotation null does as well;
flows that were real early decay as the market deepens; a high win rate bought by a bracket (positive median,
negative mean).

## Method standards (from `CLAUDE.md` — read it)

- A premise test is quick and honest: in-sample ≤ 2023, the predictor uses only information available before
  entry (assert it), a placebo or rotation null where cheap, and the result in DOLLARS PER ONE MICRO, gross and net.
- Report a mean beside its median and the year split; name the top trade; a mean carried by 2020 or 2022 is a flag.
- Check the "oracle" first where possible: how big is the reversion on the days it happens, and what precision does
  a selector need to break even?

## What a SOLID LEAD is (the bar the pair must agree on)

1. **New:** not on the tried list, or a clearly stated and testable difference from the nearest prior record
   (cite its D-number).
2. **A mechanism:** who is forced or mistaken, and why the price must come back — with a source (paper, exchange
   rule, market-structure fact) where one exists.
3. **Size:** a premise test on data on disk (≤ 2023) shows the reversion, or the conditional reversion, is plausibly
   ≥ the micro cost in gross dollars — OR, if data is missing, a sourced size estimate plus what the data would cost
   (a free metadata quote).
4. **Frequency and stability:** enough events a year (not rare and lumpy), not carried by one year.
5. **Pre-registrable:** a precise construction (instrument, clock, trigger, entry, exit), the predictor defined
   with pre-entry information only, the null, and the result that would kill it.

## Output format for each lead

```
LEAD n: <name>
- Mechanism (who is forced/mistaken; source):
- New because (nearest prior D-number and the difference):
- Instrument / clock / trigger / entry / exit:
- Predictor (pre-entry only):
- Premise test (script path, data, window, n, effect, gross and net per micro, null/placebo, year split, top trade):
  or, if untested, the sourced size estimate and the data cost:
- Frequency per year; stability:
- Kill criterion for a pre-registration:
- Prior (your honest probability it survives a full Stage 0):
- Conservative's verdict / creative's rebuttal (filled during the debate):
```
