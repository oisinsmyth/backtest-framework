# D586 — FIXTURE: the **CME settlement-window table with effective dates**, 17 products across four exchanges, sourced sentence by sentence from CME's own procedure pages and Special Executive Reports — and a loader that **RAISES** rather than serve a window it cannot date

*2026-09-21. A data record, not a study. No strategy return is computed here. Built for the two
deposit docs that both declare a per-product settlement-window table as a shared dependency —
`SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.4 ("verify and record") and `INDEX_REWEIGHT_FLOW_PREREG.md`
§3.4 ("**No window time may be assumed**"). Table `data/settlement_windows.csv`, loader
`scripts/settlement_windows.py`, sources `data/settlement_flow/SOURCES.md`, tests
`tests/unit/test_settlement_windows.py` (48, offline). Wall time end to end: about 95 minutes, of
which the measurement is **11 seconds** and everything else is sourcing.*

---

## The answer to the question the ledger asked

**`SETTLEMENT_FLOW_LEDGER_PREREG.md` §3.4 guessed "about 14:28–14:30 ET for NG and CL; verify and
record". Verified, exactly, and dated.** SER-4867 (notice 26 May 2009, effective **01 June 2009**):

> "Effective June 1, 2009, the first six contract months in these products will be settled by
> Exchange staff based solely upon CME Globex activity during the closing period, from 2:28:00 to
> 2:30:00 p.m. Eastern Time."

So §7.1's candidate entry times `{13:50, 14:00, 14:10}` ET need no shift, and §7.3's "the entry must
be complete at least 3 minutes before `W_start`" resolves to 14:25:00 ET. **One caveat the doc does
not carry:** that is the *active month* window. On its last trading day the expiring month settles on
the VWAP of 14:00:00–14:30:00 ET, a thirty-minute window — so an expiry-day trade in the ledger's
sense is aiming at a different object, and §3.5 already flags expiry days.

---

## The table

| products | exchange | window, CT | window, ET | how it is struck (CME's own wording, abridged) | `effective_from` | `history_status` |
|---|---|---|---|---|---|---|
| **CL NG HO RB** | NYMEX | 13:28:00–13:30:00 | **14:28:00–14:30:00** | active-month VWAP of outright Globex trades; other months from the calendar-spread VWAP in the same window | **2009-06-01** | `dated_notice` |
| **GC** | COMEX | 12:29:00–12:30:00 | **13:29:00–13:30:00** | active-month VWAP; spreads 13:15–13:30 ET, ≥25 lots | 2026-09-21 | `current_only` |
| **SI** | COMEX | **12:24:00–12:25:00** | 13:24:00–13:25:00 | active-month VWAP; spreads 12:10–12:25 CT, ≥25 lots | 2026-09-21 | `current_only` |
| **HG** | COMEX | 11:59:00–12:00:00 | **12:59:00–13:00:00** | active-month VWAP; spreads 12:30–13:00 ET | 2026-09-21 | `current_only` |
| **ZC ZS ZW KE ZL ZM** | CBOT | **13:14:00–13:15:00** | 14:14:00–14:15:00 | lead-month VWAP of outright trades, ties to the prior settle; deferreds off the spread VWAP | 2026-09-21 | `current_only` |
| **LE HE** | CME | **12:59:30–13:00:00** | 13:59:30–14:00:00 | **each contract month** settles to its own VWAP — no lead-month anchor, no spread tier | 2026-09-21 | `current_only` |
| **ES NQ** | CME | **14:59:30–15:00:00** | 15:59:30–16:00:00 | lead-month VWAP; if no trade, the **midpoint of the Bid/Ask** over the window; deferreds off the spread then a carry calculation | **2020-10-26** | `dated_notice` |
| ES NQ, superseded | CME | 15:14:30–15:15:00 | 16:14:30–16:15:00 | blended floor+Globex VWAP, floor lots ×5, to the nearest .10 index point | — (`effective_to` 2020-10-23) | `record_only` |
| ZC ZS ZW ZL ZM, superseded | CBOT | 13:59:00–14:00:00 | 14:59:00–15:00:00 | blended pit+Globex lead-month VWAP | 2012-06-25 (end unsourced) | `record_only` |

**17 of 17 products mapped, 0 unmapped.** 24 rows: 17 served, 7 `record_only`. Micros inherit
through a module-level map, not duplicate rows: `MNG→NG MCL→CL MGC→GC SIL→SI MHG→HG MES→ES MNQ→NQ`.

## Four things that bite, found on the way

1. **CME does NOT publish these in Chicago time — it publishes half of them in New York time.** The
   brief's premise, and the natural assumption, is that a CME window is a CT window. CME's own
   `Daily Settlement Time Details` page states **CME and CBOT** products (livestock, grains,
   equities, FX, rates) in **CT** and **NYMEX and COMEX** products (energy, metals) in **ET**. Silver
   is stated in CT on its product page and in ET on the master table, the same window twice. Every
   row here stores both spellings, G4 asserts the +1 h identity on every row, and the `notes` column
   names which zone CME itself used. **A study that read "14:28–14:30" off the energy page as CT
   would be an hour early on the largest flow in the ledger.**
2. **The three COMEX metals do not settle together.** Copper at 13:00 ET, silver at 13:25, gold at
   13:30 — 30 minutes apart. `INDEX_REWEIGHT_FLOW_PREREG.md`'s Construction B unit test 11 requires
   "each leg exits at its own product's `W_end`" and a common entry preceding the earliest window;
   with metals, grains, livestock, energy and equities in one basket, the earliest `W_end` is HG's
   13:00 ET and the latest is ES's 16:00 ET — **three hours apart**, which is what that test is for.
3. **Two of the seventeen windows are THIRTY SECONDS long** (livestock and equity index), and two
   more are sixty. A one-minute bar cannot resolve a 30-second window, so the measurement below
   scores the containing minute — which overstates the window and is the conservative direction for
   a spike claim, and is recorded as `sub_minute: true` in the meta rather than smoothed over.
4. **The grains window moved twice and nobody wrote down the second move.** SER S-6245R put it at
   13:59:00–14:00:00 CT effective 2012-06-25 alongside extended open-outcry hours; SER-6617 cut
   CBOT grain trading hours effective 2013-04-08 and the close returned to 13:15 CT, which is
   consistent with today's 13:14:00–13:15:00 CT — but **no notice stating that settlement-window
   change was found**, so it is not asserted. The 2012 window is carried as `record_only` and the
   current one as `current_only`.

## What could not be sourced, and what the loader does about it

**`window_for(root, date)` returns a `SettlementWindow` or raises. It never falls back.**

- `UnmappedProduct` for a product with no served row — `window_for("XX", …)` raises, and so does
  every micro whose parent is unmapped. This is `INDEX_REWEIGHT_FLOW_PREREG.md` unit test 12.
- `UnsourcedDate` for a date below the product's earliest **sourced** effective date. For the eleven
  `current_only` products that floor is the access date, so **`window_for("GC", "2023-06-01")`
  RAISES**. That is not a defect; it is the pre-registered consequence of "no window time may be
  assumed". `window_for("NG", "2023-06-01")` returns the sourced 14:28–14:30 ET window because NG's
  history *is* dated.

Not fetched, recorded as such in the meta:

| what | why |
|---|---|
| GC SI HG history | no SER establishing the COMEX metals windows was found |
| ZC ZS ZW KE ZL ZM current window's start | SER-6617 is a trading-hours notice, not a settlement notice |
| LE HE history | the December-2014 move off pit-only settlement is in the secondary literature (a CFTC paper); **no CME notice stating the window was located, and a secondary source is not a source for a time** |
| ES NQ pre-2020 start | SER-8591 dates the END of the 15:14:30 CT window (its Exhibit B blackline) but never its start |
| SER-9637's contents | CME serves it only as an embedded PDF the browser will not render as text; its *effective date* (12 Jan 2026) is sourced from the notice page, its body is not |
| KE volume | KE is not among the 36 roots of `fut_day1m.parquet` |

**A third `history_status` was added beyond the two the brief named.** `record_only` is a window read
verbatim from a dated source whose own start (ES/NQ) or end (the CBOT ags) is not sourced. It is
carried so the finding is not lost, is **never** returned by `window_for`, and is excluded from the
G5 overlap check. The alternative was to invent a boundary date or to throw the finding away.

## Gates (in the meta, each proven to RAISE by `--selftest`)

G1 every mapped row has an `https` URL, a 20-character `Z` access time and a basis of real length ·
G2 `window_for` on an unmapped product raises · G3 `window_for` below the earliest sourced effective
date raises · G4 CT→ET is exactly +3600 s on all 24 rows · G5 no overlapping served periods within a
root · G6 all 7 micros map to a mapped parent.

**Each break hits the scalar the assertion reads.** G1's break strips the URL; G4's sets `start_ct`
equal to `start_et` and the message reads "ET-CT is 0s"; G5's adds a second open period to a root
that already has one; G6's deletes the parent row. **G2 and G3 pass BY raising, so their break is the
opposite shape** — the probe is swapped for one that is mapped (`MNG`) or one day *above* the floor,
and the gate must then fail with "window_for did NOT raise".

**Ledger unit test 13 (DST) is the seventh check.** CT and ET are asserted one hour apart through
`zoneinfo` on every day of **both** transition weeks of 2020–2023 — 56 days, **2,688 CT/ET pairs**,
including the Sundays the clocks move (2023-03-12 and 2023-11-05 among them) and the trade dates
either side. Its break makes one row's ET spelling an hour wrong and the audit names the row and the
day.

## Measurement — reported, NOT gated

Share of session volume in the stated window against the five minutes either side, from
`data/fixtures/fut_day1m.parquet` (present=True bars, per root by pyarrow filter, 11 s).
**In-window volume per minute ÷ pre-5-minute volume per minute** — the per-minute form, because a
1-minute window against a 5-minute flank is not a like comparison in raw share:

| root | window ET | 2016 | 2017 | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| HE | 13:59:30–14:00 | 13.5 | 14.8 | **16.9** | 15.5 | 14.4 | 13.7 | 14.4 | 13.6 |
| LE | 13:59:30–14:00 | 12.3 | 12.9 | **14.6** | 12.5 | 13.5 | 12.5 | 13.2 | 11.2 |
| ES | 15:59:30–16:00 | 7.1 | **8.2** | 6.8 | 6.4 | 6.0 | 6.4 | 6.1 | 7.2 |
| HG | 12:59–13:00 | 6.1 | 6.5 | 5.9 | 6.2 | 6.5 | 7.4 | 8.2 | **8.3** |
| SI | 13:24–13:25 | 6.1 | 6.0 | 6.2 | 5.0 | 5.7 | 6.6 | **7.5** | 6.2 |
| ZW | 14:14–14:15 | 7.4 | 8.0 | 6.6 | 6.1 | 6.3 | **8.3** | 8.1 | 7.2 |
| ZC | 14:14–14:15 | 7.3 | **8.6** | 6.3 | 5.2 | 6.0 | 7.1 | 6.6 | 7.0 |
| GC | 13:29–13:30 | 4.0 | 3.8 | 4.6 | 3.7 | 3.7 | 5.8 | **6.6** | 5.6 |
| NG | 14:28–14:30 | 5.9 | **6.4** | 5.0 | 5.2 | 5.1 | 4.2 | 4.7 | 4.8 |
| ZM | 14:14–14:15 | 5.1 | 6.2 | 5.8 | 4.9 | 5.8 | 6.5 | **7.0** | 5.9 |
| ZL | 14:14–14:15 | 5.6 | **6.2** | 5.9 | 5.4 | 5.7 | 6.0 | 6.0 | 6.1 |
| ZS | 14:14–14:15 | 5.3 | 5.7 | 5.6 | 4.9 | 4.8 | 5.2 | **6.0** | 5.5 |
| RB | 14:28–14:30 | 3.7 | 4.2 | 4.0 | 3.5 | 3.8 | 4.6 | 4.8 | **5.8** |
| NQ | 15:59:30–16:00 | 3.9 | 3.9 | 3.5 | 3.2 | 3.0 | 2.8 | 3.6 | **4.4** |
| HO | 14:28–14:30 | 3.5 | 3.8 | 3.9 | 3.7 | 4.1 | 4.3 | 4.7 | **5.9** |
| CL | 14:28–14:30 | 3.6 | 2.9 | 2.9 | 2.5 | 3.0 | 3.5 | **3.9** | 3.6 |

**Every one of the sixteen measurable roots lifts, in every one of the eight years — 128 of 128
root-years above 2.5×, none below** (weakest CL 2019 at 2.53×, strongest HE 2018 at 16.86×). Against
each root's own session *mean* minute the lift is larger still, 3.5× to 40.7× over the same 128
cells: HE 29.7–40.7×, LE 23.0–31.6×, ZC 13.8–22.1×, ZW 15.3–21.9×, ES 13.5–21.8×, ZL 13.6–17.0×,
ZM 11.6–17.4×, RB 10.9–15.5×, HO 10.0–14.9×, ZS 10.3–13.6×, HG 8.8–13.3×, NG 8.6–12.2×, SI 6.1–9.2×,
CL 4.5–7.6×, NQ 4.9–7.4×, GC 3.5–6.8×. **There is no root to report as flat.** The share of the whole
session's volume that trades in the window, min–max over 2016–2023: HE 7.08–9.69%, LE 5.47–7.52%,
RB 5.20–7.36%, HO 4.76–7.11%, NG 4.12–5.82%, ZC 3.28–5.26%, ES 3.23–5.20%, ZW 3.64–5.22%,
ZL 3.24–4.05%, ZM 2.77–4.13%, CL 2.15–3.61%, ZS 2.46–3.25%, HG 2.10–3.16%, SI 1.46–2.20%,
NQ 1.17–1.75%, GC 0.83–1.61%.

**Band.** Every mapped window falls **inside** the fixture's 09:00–15:59 ET band, because each sits
at or just before its own market's close and those are all inside it (D530: grains 14:20, livestock
14:05, metals 13:30, energy 14:30, equity index 16:00). What falls outside is the **post-window flank
of ES and NQ**: their window is bar 419, the last bar, so the five minutes after it do not exist and
`in_vs_post5` is `null` rather than a number — the meta says so in `flank_truncated`. Two windows
(GC 13:29–13:30 ET and HG 12:59–13:00 ET) sit inside the hour D530 measured at 5.4% and 2.6% of
session volume for those roots; **the window is a spike inside a dead hour, which is exactly the
D530 trap in miniature** — a study that averaged over that hour would dilute a 6× minute into 60.

**Cross-engine check.** The measurement was run twice, once under the system interpreter and once
under `uv run --with pyarrow`, and every published figure is identical.

## Files

`data/settlement_windows.csv` (24 rows, 14 columns, every row carrying `source_url` and
`accessed_utc`) · `data/settlement_windows.meta.json` (products, unmapped, micro map, history,
`not_fetched`, the six gates with their raise-proofs, the DST audit, the measurement, timings) ·
`data/settlement_flow/SOURCES.md` (one entry per fact: URL, access date, and CME's own sentence) ·
`scripts/settlement_windows.py` (`window_for`, `--selftest`, `--measure`, `REQUIRED_OUTPUTS`) ·
`tests/unit/test_settlement_windows.py` (48 tests, offline, `ruff` clean) ·
`data/raw/cme_settlement/` (gitignored: 14 Confluence page bodies and 3 PDFs, unmodified, each
named with its `fetched_at`; a clone receives none of it) ·
`temp/d586_volume_measurement.json` (the measurement cache, keyed on the fixture's mtime).

**How it was fetched, since the route is itself a finding.** `curl` to `cmegroup.com` from this
machine returns **HTTP 403** with the body *"This IP address is blocked due to suspected web scraping
activity"*, and `WebFetch` times out — the same block `data/futures_contract_specs.json`'s
`_provenance` records. Two routes work and both are public: the **CME Group Client Systems Wiki**
(Confluence space `EPICSANDBOX` on `cmegroupclientsite.atlassian.net`), which is where CME's own
`cme-group-settlement-procedures.pdf` points for every asset class and which serves anonymously over
its REST API; and the **browser pane** for the SER HTML pages. Two SER PDFs came from `web.archive.org`
captures. **No summariser is in this path** (D445): every quoted sentence was read out of raw bytes
or rendered page text, and after the table was written the 14 cached page bodies were re-grepped for
the window strings independently of what the browser had shown — **17 of 17 products matched**.

---

## Proposed paragraph for `docs/data-available.md` (NOT added here)

> **The CME settlement-window table (D586, 2026-09-21).** `data/settlement_windows.csv` — 24 rows,
> one per (root, effective period), for 17 products across NYMEX, COMEX, CBOT and CME: window start
> and end in **both** CT and ET, the basis quoted from CME's own procedure page, `effective_from` /
> `effective_to`, `history_status`, `source_url` and `accessed_utc`. Read it through
> `scripts/settlement_windows.py:window_for(root, date)`, which **RAISES** for an unmapped product
> and for any date before that product's earliest *sourced* effective date; micros inherit their
> parent's row through `MICRO_PARENT`, never a duplicate row. **What bites:** *(i)* **CME publishes
> only half of these in Chicago time** — CME and CBOT products (livestock, grains, equity index) in
> CT, NYMEX and COMEX products (energy, metals) in ET, and silver appears in both zones on two CME
> pages; read the wrong one and you are an hour out. *(ii)* **Only energy (2009-06-01, SER-4867) and
> equity index (2020-10-26, SER-8591) have a sourced history**; the eleven metals, grain and
> livestock rows are `current_only`, so `window_for("GC", "2023-06-01")` **raises** by design —
> source the history before a study reads it, do not assume it. *(iii)* **Two windows are thirty
> seconds long** (livestock 12:59:30–13:00:00 CT, equity index 14:59:30–15:00:00 CT) and cannot be
> resolved on a one-minute bar. *(iv)* The energy window is the **active month's**; the expiring
> month on its last day uses 14:00:00–14:30:00 ET instead. *(v)* **KE is in the table but not in
> `fut_day1m.parquet`**, so it carries no volume measurement. The measurement that is there, in the
> meta: **in-window volume per minute is 2.53×–16.9× the five minutes before it on all 16 measurable
> roots in all 8 years 2016–2023, 128 of 128** (HE 13.5–16.9×, LE 11.2–14.6×, ES 6.0–8.2×, CL
> 2.5–3.9× the weakest), and 3.5×–40.7× each root's own session mean minute — the window carries
> 0.83% (GC) to 9.7% (HE) of the whole session's volume in one or two minutes. Every window sits inside the fixture's
> 09:00–15:59 ET band; **the ES and NQ post-window flank does not exist** (their window is bar 419).
> Sources sentence by sentence in `data/settlement_flow/SOURCES.md`; raw pages cached, gitignored,
> under `data/raw/cme_settlement/`.
