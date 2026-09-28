# D651 PRE-REGISTRATION — the time-of-day liquidity map on `bbo-1m` (41 roots, 15-minute ET buckets), the session-handoff study's kill 1, and whether a pre-vault quote pull is worth asking for before the subscription lapses

*Drafted 2026-09-28, on the principal's word: "tackle the liquidity map in a worktree", after the recommendation
that listed the map as the one item from the 2026-09-19 deposit with a deadline. It is committed alone, before its
builder exists (R8). **No return is computed by anything this record declares.***

## 0. Why, and what reopens

`SESSION_HANDOFF_LIQUIDITY.md` (deposit of 2026-09-19) was closed in
[D582](D582-CLOSED-the-deposit-and-the-mechanism-programme-synthesis.md) §1 as "never designed here — two-sided
passive quoting, not prop-compliant, and a simulated fill engine flatters it". Every one of those reasons is about
the **prop** account, and the document itself calls the study **personal-capital only** (its §10). Rejecting a
personal-book candidate on prop grounds is the error the standing rule forbids (a prop-ineligible construction is
still worth keeping for the personal book). The principal's instruction reopens the document **for the personal
book, and for two of its items only**:

1. **its step 1, the time-of-day liquidity map** — "useful to every other event study … build step 1 regardless of
   whether the strategy proceeds" (its §11, §13; `EVENT_PORTFOLIO.md` §4 lists it as shared cost infrastructure);
2. **its kill 1** — "commission ≥ ½ spread captured on all instruments. Terminal." — which needs quotes and a
   commission and nothing else, so it can be scored without a return.

**Its kill 2 — realised spread inside the handoff windows against normal hours — is NOT scored here.** Realised
spread needs the mid after each fill, i.e. a signed price move, and every quote on disk is inside the programme's
vault (§2). What this record decides instead is whether kill 2's data — a **pre-vault** `tbbo` + `bbo-1m` pull —
is worth putting to the principal before the Databento CME subscription lapses (~2026-10-11; the quotes are USD 0.00
until then and billable after).

## 1. What is built

**The fixture** `data/fixtures/fut_liquidity_15m.csv.gz` (gitignored like every panel; `.meta.json` tracked; entered
in `data/data_manifest.json` and in `panel_catalogue.py` with date column `day`, as `fut_spread_all_1m` is), one row
per **(root, session day, bucket, spread in ticks)**:

| column | meaning |
|---|---|
| `root` | one of the 41 `bbo-1m` roots of [D507](D507-the-spread-census-on-all-41-roots-micros-quote-tighter-than.md) |
| `day` | the CME session day: a timestamp at or after 18:00 ET belongs to the next calendar day (D507's rule) |
| `bucket` | the 15-minute ET bucket, `HH:MM` of its start, on `ts_recv` converted with `US/Eastern` (DST handled by the conversion; 96 buckets) |
| `spread_ticks` | `(ask_px_00 − bid_px_00) / tick_points`, asserted a whole number |
| `n` | quoted minutes in that cell |
| `q_lots` | Σ over those minutes of `bid_sz_00 + ask_sz_00` (touch depth, contracts, D507's convention) |
| `q_orders` | Σ of `bid_ct_00 + ask_ct_00` |

**Front contract only**, from the breadth fixture's volume rule; the five micros (MES MNQ M2K MYM MBT) inherit their
parent's expiry, exactly as D507's `front_map`. A minute is kept only if both sides are defined (the INT64_MAX
sentinel is removed explicitly — D507's grounding) and `ask > bid`. Session days **2025-09-11 → 2026-09-10**.

**The no-return guard, in code:** the fixture's columns are asserted to be exactly the seven above; no price level,
mid, or signed quantity is ever written; the only arithmetic on a price is `ask − bid` in ticks. `--selftest` must
show that adding a price column raises.

**Measured semantics, before the build:** `bbo-1m` prints a row for every minute the front book is two-sided — ES,
ZN, CL, 6J, PA and MBT show 60 rows an hour in every hour except the 17:00 halt (read from D507's fixture). So `n / 15`
per bucket is the share of minutes with a two-sided book, and is reported as **coverage**.

## 2. Seals, listed before any byte is read

- **The programme vault, 2025-03-01 → 2026-09-18.** Every session this record reads is inside it. The read is the
  class [D507](D507-the-spread-census-on-all-41-roots-micros-quote-tighter-than.md), D510, D604 and
  [D623](D623-RESULT-the-close-is-heavier-and-smaller-lotted-but-BALANCED.md) made of the same year: quoted spread
  and touch size only, nothing signed, no price level, no return. The vault protects the scoring of frozen models;
  none of the four frozen or waiting lines (NG Stage A, D649's projected-profit line, and the models A10 will add)
  reads a spread or a touch size. **The seal-date reconciliation stays the principal's** (D609); this record does
  not make it.
- **D626's sample, CL NG HO RB 2026-09-21 → 25.** After the `bbo-1m` span; the builder **raises** if any session at
  or after 2026-09-11 is selected.
- **Scheduled one-shot reads** (the joint vault run): unaffected; they read returns this record never computes.

## 3. The windows, as the deposit wrote them

| window | ET | the hour before | the hour after |
|---|---|---|---|
| **W1** Asia → Europe | 02:00–03:30 | 01:00–02:00 | 03:30–04:30 |
| **W2** Europe → US pre-market | 07:30–08:30 | 06:30–07:30 | 08:30–09:30 |
| **W3** US close → Asia (across the 17:00 halt) | 16:00–17:00 **and** 18:00–19:00 | 15:00–16:00 | 19:00–20:00 |
| **core** (reference, not a window) | 10:00–15:00 | — | — |

A session counts for (root, window) only if the window **and** both neighbours each have a two-sided book on at
least 90 % of their minutes. A (root, window) with fewer than 100 such sessions is reported as **not in session**
and scored on nothing (the grains and livestock will fall out of some windows by their own trading hours).

## 4. The statistics

**T — is the window a trough?** For each counted session s: `x(s) = ln D_W(s) − ln min(D_before(s), D_after(s))`,
where D is the mean touch depth (`q_lots / n`) over the span's minutes. `x < 0` means the window is thinner than
BOTH neighbours, which is the handoff claim — an outgoing desk gone, an incoming one not yet there — as distinct
from "the night is thin". The median of `x` over sessions, with a **moving-block bootstrap** 95 % interval (blocks of
5 sessions, 2,000 draws, seed 651):

- interval wholly below 0 → **TROUGH**; wholly above 0 → **NOT A TROUGH**; otherwise **UNRESOLVED** (D373's rule
  in its interval form).

Reported beside it, not gating: the share of sessions with `x < 0`; the spread analogue `y(s) = S_W(s) −
max(S_before(s), S_after(s))` in ticks (a tick-pinned book cannot widen, so it cannot gate); and the levels against
the core — `median D_W / median D_core`, `mean S_W / mean S_core`, and coverage.

**H0 — the deposit's kill 1.** For each (root, window) and for the core: `half = S̄ × tick_usd / 2`, with `S̄` the
minute-weighted mean quoted spread over every counted minute, and `side = commission_rt_usd / 2`, both
`tick_usd` and `commission_rt_usd` read from `data/futures_costs.json`
([D591](D591-futures-cost-bricks-and-the-reconciled-cost-table.md): the declared $6.00 full-size / $3.00 micro
round trip; never measured). `R = half / side`:

- **PASS** R ≥ 2 (the deposit's "well below"); **MARGINAL** 1 ≤ R < 2; **FAIL** R < 1.
- **Kill 1 fires** if no (root, window) reaches R ≥ 1 — "commission ≥ ½ spread captured on all instruments".

`R` is a **ceiling**: it is the spread a quoter would capture if the mid never moved against the fill. Adverse
selection, queue position and fill rate — the terms the deposit says decide the study — are all outside it.

## 5. The decision this record exists to make

- **(a) Kill 1 fires** → `SESSION_HANDOFF_LIQUIDITY.md` closes at its own kill 1; nothing is quoted.
- **(b) Otherwise, the candidate set** is the roots with at least one window that is both **TROUGH** and **H0 PASS**.
  If it is non-empty, Claude **quotes** (metadata only, no submission) a pre-vault `tbbo` + `bbo-1m` pull for those
  roots' parent symbols over **2017-05-22 → 2025-02-28** (MDP 3.0 onward, per `DATA_EXPANSION_PLAN.md` §2.1, to the
  vault's start) and puts the quote to the principal before the 2026-10-09 top-up. **Nothing is submitted without
  the principal's word.**
- **(c) Kill 1 does not fire but the candidate set is empty** → the thin window the mechanism needs is not seen
  where it would be affordable; the recommendation is no pull, and the principal decides.

## 6. Predictions, written before the build

1. **Kill 1 does not fire.** A full-size root quoting one tick has `R = tick_usd / 6` — ES 2.08, ZN 2.60, CL 1.67,
   6E and 6B 1.04, NQ 0.83 — so ES and ZN PASS at one tick, CL and the FX roots are MARGINAL unless the window
   quotes wider, and NQ needs a spread above 2.4 ticks to PASS (it quotes wider than one tick on most minutes,
   D507); the micro index roots FAIL (MES 0.42). This is the deposit's own §7 foreseen: the commission kills it on
   MES, not on ES.
2. **W3 is a TROUGH on ES, NQ, ZN and CL** (the post-close wind-down and the thin reopen, against a deep 15:00 hour
   and a recovering 19:00).
3. **W2 is a TROUGH on ZN, ZB and ES**: liquidity is pulled ahead of the 08:30 releases while 06:30 and 09:30 are
   deeper.
4. **W1 is a TROUGH on 6E and 6B** (the European open is their handoff) and **UNRESOLVED or NOT A TROUGH on the index
   roots**, where 01:00–04:30 is uniformly thin rather than dipping.
5. **The windows are thinner than the core everywhere** (`median D_W / median D_core` < 0.5 on the index roots),
   which on its own is NOT the handoff claim — prediction 5 can hold while 2–4 fail.

A prediction that fails is recorded as failed; none is a gate except as §5 uses T and H0.

## 7. What this record does not do

It computes no return, no realised spread, no fill, no P&L, and spends no trial of the deposit's seven. It does not
test the one-sided variant (deposit §10), queue position, or the 08:30 exclusion question (its open question 1),
and it does not register a family in the programme registry, because it tests nothing that could be promoted. The
time-of-day map is a cost instrument; its numbers are quoted spreads, a floor on what an aggressor pays
([D507](D507-the-spread-census-on-all-41-roots-micros-quote-tighter-than.md) §8).

## 8. Outputs and cost

`scripts/build_fut_liquidity_map.py` (`--build`, `--report`, `--selftest`), the fixture and its meta,
`data/d651_liquidity_map.json` (every statistic above, per root and window), and `docs/results/LIQUIDITY_MAP.md`
rendered from it. **Runtime:** measured on one monthly file before the full build; 13 files of 0.2–0.8 GB,
processed in strided worker processes, with a chunk-equals-whole equality check before the parallel build is
trusted.
