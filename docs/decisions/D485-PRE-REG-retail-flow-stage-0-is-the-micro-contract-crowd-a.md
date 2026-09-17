# D485 — PRE-REG, retail flow stage 0: is the micro-contract crowd a distinct population on the ES and NQ tape, and does its divergence from the E-mini flow carry a signed intraday edge?

*Filename shortened 2026-09-17 ([D540](D540-local-config-a-clone-never-receives.md)); was `D485-PRE-REG-retail-flow-stage-0-is-the-micro-contract-crowd-a-distinct-population-on-the-ES-and-NQ-tape-and-does-its-divergence-from-the-E-mini-flow-carry-a-signed-intraday-edge.md`. The H1 above is the full title.*

**2026-09-12. Committed before the fixture builder and the runner exist (R8).** Line opened by the
principal ("Lets try using more auxiliary data. Lets hunt retail traders"); scoping in
[`docs/research/retail-flow/00-scoping.md`](../research/retail-flow/00-scoping.md). Stage 0 by the
programme's definition: a premise check with an abandon condition, then one declared in-sample
return read. **Nothing is admitted by this record; no holdout of any line is touched.**

## 1. The premise, and why it must be checked before anything is traded

The claim is that the CME micro contracts (MES, MNQ; one-tenth of ES, NQ; launched May 2019; sold
by the exchange to "active individual traders" and the instrument every futures prop account
trades) carry a crowd whose signed order flow is **not** the E-mini's scaled down. If it is the
same population at a tenth of the size, the two imbalances move together and there is nothing to
read. [[stage-0-premise-check]]: measure the conditioner before designing on it.

**The tape signs every trade.** The `tbbo` schema carries the exchange's aggressor side
(`side` = B buy aggressor, A sell aggressor; N unsigned, 4 of 610,145 in the probe) and the best
bid and ask at the trade. Signing is therefore exact, not the sub-penny inference the equity
literature has to use (Barber et al. 2024 mis-signing 28% → 5%). A gate checks the two agree.

## 2. Fixture (data layer, built and gated first, no study in it)

`scripts/build_fut_micro_flow.py --build` → `data/fixtures/fut_micro_flow_5m.csv.gz` + `.meta.json`.

- **Source:** `data/raw/databento/GLBX-20260911-6DA3JPNQE3/*.tbbo.dbn.zst`, 13 monthly files,
  2025-09-11 → 2026-09-10, all instruments; only the outrights of **ES, MES, NQ, MNQ** are read.
- **Front month per session:** the contract with the highest full-session traded volume on the
  E-mini root for that session (D448/D467's rule); the micro follows its E-mini's month. Roll
  sessions flagged, kept.
- **Session:** 18:00 ET day a → 16:59 ET day b (D467). Regular hours = 09:30–16:00 ET.
- **Rows:** one per (pair ∈ {ES/MES, NQ/MNQ}, session, 5-minute bucket, contract class ∈
  {mini, micro}): `n_trades`, `vol`, `buy_vol`, `sell_vol`, `unsigned_vol` (side N), `lot1_vol`
  (trades of size 1), `lot_le2_vol`, `vwap`, `last_px`, `first_px`, and `mid_agree` (trades whose
  side matches the midpoint rule). Times are bucket START; a bucket holds trades with
  `ts_event` in [start, start+5min).
- **Gates, all asserted in `--gates`, written to the meta:**
  - **[T1] sign agreement:** among trades strictly at the bid or the ask, `side` agrees with the
    price side on ≥ 99% per contract class per month (probe row 1: at the bid, side A — sell).
  - **[T2] cross-schema volume:** per session and contract, Σ`size` from tbbo equals the
    `ohlcv-1m` session volume already on disk (D467's table for ES/NQ; for MES/MNQ a fresh
    `ohlcv-1m` read) within 0.5%. This is the check that the tbbo read is complete.
  - **[T3] presence:** a session is PRESENT when RTH holds ≥ 70 of 78 buckets on both classes;
    absent sessions listed, not silently dropped.
  - **[T4] no future:** every bucket's fields are recomputable from trades with
    `ts_event < bucket_end`; asserted by rebuilding ten random buckets from raw trades.
  - **[T5] scale:** micro RTH volume ÷ mini RTH volume per session is reported (prediction §5).
- **Cost:** decompression is the whole cost (`bench_decode_pipeline.py`: 254 MB/s a worker);
  35 GB compressed across 13 files → processes over `files[i::N]`, projected **under 15 min** at
  6 workers; one worker's RSS printed before the pool ([[measure-the-worker-before-the-fan-out]]).

## 3. The premise checks (in-sample window §4), each with its abandon clause

All on RTH buckets, both pairs, reported per pair. `OI = (buy_vol − sell_vol) / (buy_vol + sell_vol)`
per bucket; `OI_day` = the same ratio over 09:30–16:00.

| | measurement | passes if | abandons if |
|---|---|---|---|
| **P1 distinct population** | (a) `lot1_vol / vol` micro vs mini; (b) per-session Pearson correlation of `OI_micro` and `OI_mini` over the 78 RTH buckets, reported as the median and the 10th/90th percentiles | median corr ≤ 0.80 **and** micro 1-lot share exceeds the mini's by ≥ 15 pp | **median corr > 0.90 → the proxy is not a distinct crowd; the line closes on this record, no return is read** |
| **P2 the crowd behaves like retail** | correlation across sessions of `OI_day_t` with the prior session's RTH return `r_{t−1}`, micro and mini separately; the literature's retail is contrarian (buys losers) | `corr_micro < 0` and `corr_micro < corr_mini` | neither holds → recorded as "micro flow is not contrarian"; the return read still runs (P2 is descriptive, not a gate) |
| **P3 the prop-firm fingerprint** | (a) micro sell share of RTH volume in the last 30 minutes (15:30–16:00) vs the first six hours; (b) `corr(cumOI_micro[09:30→15:00], r[15:00→16:00])` across sessions, and the same for the mini | (a) last-30 sell share differs from the day's by ≥ 3 pp in either direction, at ≥ 2 SE (bootstrap over sessions); (b) micro corr ≠ mini corr at ≥ 2 SE | not met → "no fingerprint at this resolution"; recorded |

## 4. The return read (in-sample, one declared family, the principal's constraints)

Prop constraints (R11, D473): intraday-closable, **one round trip a session**, hours-scale hold,
scored in dollars at one micro under the $3 round trip (`data/futures_contract_specs.json`).

**Windows.** In-sample = sessions 2025-09-11 → **2026-06-30**. **Reserve = 2026-07-01 → 2026-09-10
(~50 sessions), unread until a pick is declared in writing;** it is small and is not a holdout
in the R8 sense — an R8 test needs new tape (the subscription can extend the pull for $0 until
~2026-10-11).

**The signal.** `Dv = z(OI_micro) − z(OI_mini)` over a formation window, z-scored within the
in-sample window per pair (the z removes the mini's own information so that what remains is the
micro crowd's *divergence*). Two formation → hold cells per pair, long the sign of `−Dv`
(**against** the micro crowd's excess flow; the contrarian reading of the extreme, Barber et al.
2022) — and the sign is declared, not fitted: a positive result with the opposite sign is
reported as *with-the-crowd* and does not count as a pass.

| cell | formation | hold (one round trip) |
|---|---|---|
| F1 | 09:30–10:30 | 10:30 → 16:00 |
| F2 | 09:30–15:00 | 15:00 → 16:00 |

Family = 2 cells × 2 pairs = **4 cells**, declared here; nothing else is read.

**Statistic per cell.** Mean signed P&L per session in dollars at one micro, gross and net of $3;
the Spearman correlation of `Dv` with the hold return; count of sessions; hit rate; median;
1% symmetric trim; worst session; the tercile split of the hold return by `Dv` (dose–response).

**Nulls, both required.** (N1) the **exact** rotation: shift the `Dv` series by every k ∈ [1, T−1]
sessions against the fixed return series (T ≈ 200 → enumerated, SE 0; D464's convention);
(N2) the common-offset **family maximum** over the four cells; the family statistic is the
**difference between the sides** (top vs bottom `Dv` tercile, D472 §1), centred on zero.
[S] sign audit in money; [M] `assert_matches_scorer` once; [X] a deliberate break of the
aggressor sign must flip the P&L sign and fail [T1].

**Pass (stage-0 criterion).** A cell is a **pick** if its side-difference exceeds N1's exact p95
**and** the family-max p95, with gross mean > 0 and net mean > 0 at one micro. A pick is not a
component; it goes to the reserve and then to new tape under its own record.

## 5. Predictions (checkable from the runner's quantities)

1. **T5 scale:** micro RTH volume is 20–45% of E-mini volume on ES and NQ (CME states micros are
   "over 30%" of equity-index volume). Outside → the front-month rule or the read is wrong.
2. **P1:** micro 1-lot share 55–75%, mini 25–45%; median within-session correlation of the two
   imbalances **0.35–0.70**. I predict P1 passes: the populations differ. Above 0.90 is the abandon.
3. **P2:** `corr_micro` between −0.15 and 0, `corr_mini` closer to zero or positive. Weak power:
   SE ≈ 0.07 at T ≈ 200, so a null result here is uninformative and is said so.
4. **P3(a):** the last-30-minute micro sell share is 2–6 pp above the day's (forced flattening);
   **P3(b):** a negative correlation of the day's cumulative micro flow with the last hour's
   return, −0.05 to −0.20, larger in magnitude than the mini's.
5. **The return read:** F2 (the flatten-window cell) is the likelier pick; F1 within noise. Family
   maximum p95 will sit near $8–15 a session on MES at one micro; I predict **no cell clears
   both nulls** (a stage 0 on ~200 sessions is underpowered for a $5-a-session effect at σ ≈
   $150), and the value of the record is P1–P3.

## 6. What this record does not do

No holdout of any line is read. Nothing enters `COMPONENTS_PROP.md` or either book. No cell
outside §4's four is scored; a P1 failure closes the proxy in writing and the return read does
not run. The Robintrack and RTAT equity sources (scoping §2 B, C) are separate records.
