# D446 — net share issuance, stage 1: the slot book both sides on point-in-time EDGAR counts, with three controls declared

**Pre-registration. Committed before the runner exists (R8).** Result in a separate file. **The
first forward-return look at share supply in this repo.** In-sample on the mining fixture; **no
holdout is read** (both daily holdouts are unseen by this line; they also lack a CIK map and an
EDGAR pull, which would be a separate acquisition before any read). D446 taken after `ls
docs/decisions` and `git log --all` showed D445 taken by another session (the floor-lock measurement, a00dd94) and nothing above it.

## 0. What is being tested, in one sentence

That a name's **net share issuance over the past year — the literal supply of shares, first-filed
and filing-dated (D444)** — predicts its hedged forward return: issuers down, repurchasers up,
beyond what a random name in the same state, a time-rotated issuance panel, and a persistent
random selector would give. D443/D444 established the object is persistent (0.54 a year out),
90% orthogonal to the six tested axes, and orthogonal to momentum; this record reads the return.

## 1. The panel (D444's, frozen)

`data/d444_issuance_panel.csv.gz`: 49,421 first-filed share counts on 1,343 names, `avail_date`
= filing date, `t_av` = the first fixture bar strictly after it. **Guards applied before ranking,
declared here:** rows with the `[S]` flag dropped; rows with `|ln(SO / the name's median SO)| >
ln 50` dropped (D444's filer scale errors, 0.2%); a value is *fresh* for 200 calendar days from
its `fiscal_date`. **The 168 multi-class and foreign filers (11%) are absent** and are listed as
such in the universe count; the 43 unresolved CIKs likewise.

## 2. The construction

- **Score.** At bar t, for every eligible name (the kernel's `elig`, the price floor `keep_v2`,
  the F0 exclusion) with a fresh NS available (`t_av ≤ t`): `S_t` = the cross-sectional percentile
  rank of NS among those names, 0 (largest net repurchase) to 100 (largest net issuance).
  Computed once per bar; nothing is looked at beyond bar t.
- **Events.** A name enters the **short** side on the first bar its rank ≥ 90 (top decile, net
  issuers) and the **long** side on the first bar its rank ≤ 10 (bottom decile, repurchasers); a
  name still in its decile when its hold expires re-enters on the next bar (so a persistent state
  is held, not visited once). The event masks are shifted to the next bar and filled at the open,
  the D434 `[F]` alignment.
- **The kernel.** D345's, through `run_d359` as in D437–D440: `exit = "cap"`, **`cap = 126`
  bars (primary)**, `hedged_series = True`, **`n_max = 40` per side (the slot book: when more
  candidates than free slots, the kernel takes the most extreme ranks first — shorts by score
  descending, longs ascending, its own convention)**. Equal weight, the kernel's unit. **Reported
  beside, not gated:** `n_max = None` (every name in the decile), `cap = 63` and `cap = 252`.
- **The book.** Each side's hedged deployed series (`book_dep_x`, bp/bar); **the combined book =
  the long series + the short series** (each already market-hedged), the primary object. Sample:
  the first bar with a fresh NS (2010) to 2023-12-29; era 2 from the midpoint of the book's span.

## 3. The three controls, declared

Each preserves one thing the construction has and destroys the one thing it claims — the
alignment of *issuance* with the *name and the time*. Each runs through the same kernel with the
same cap and slots.

- **C1 — state-matched random names** (D437's `draw_state_matched`, per cell). On each entry day
  the entering names are replaced by the same number of random eligible names from the **same
  price × volatility × momentum tercile cell** (D392's `tercile_pools`) that are *not* in either
  decile. Destroys issuance; preserves count, day, and the state tilt D444 measured (small, cheap,
  volatile). 100 draws; p50, p95, and the p95's bootstrap SE (D373's rule).
- **C2 — the enumerated time rotation of the issuance panel.** The score panel `S` is rolled in
  time by a **common offset k for every name** (circular), the event masks rebuilt from the rolled
  scores, and the book re-run; **k enumerated over every multiple of 21 bars from 21 to T−21**
  (~160 offsets, exact within the grid, no sampling SE). Preserves every name's own persistence,
  the cross-sectional shape, the turnover, the slot pressure; destroys alignment with the return.
- **C3 — the persistent random selector.** Each name's NS rank is replaced by a random rank
  process with the **empirical quarter-to-quarter decile transition matrix** of the real panel
  (estimated from D444's usable rows, 10 × 10) and the real panel's availability dates, so the
  random selector has the same persistence (≈ 0.88 a quarter), the same refresh cadence and the
  same decile occupancy as the real one — a random subset that does not churn (the D291 lesson).
  100 draws. Destroys which name is an issuer; preserves everything about how a persistent
  selector trades.

The per-trade lens (every entry, pnl to exit, bp) is reported for each side against C1; the
book lens (bp/bar, monthly block-bootstrap SE) against C2 and C3. **Never compared across
lenses.**

## 4. Costs

Both lines on every table, as D440: **crossed** (the kernel's `two_c` under PUB + commission +
D337's `gc_htb` borrow on the short side) and **passive at the open** (D439's 0.34 of the modelled
half-spread per side + 9 bp chase, labelled an assumption). The names are small, cheap and
volatile (D444's tilt), where the modelled half-spread is closest to a quote, so the crossed line
is the one that decides.

## 5. The bar (one primary, R14)

Primary object: **the combined book, cap 126, n_max 40, crossed line.**

- **T1** combined gross per bar above C2's p95 (exact) **and** above C3's p95 by 2 SE.
- **T2** combined net per bar (crossed) > 0 by 2 SE (block bootstrap).
- **T3** per trade, **each** side's gross above its C1 p95 by 2 SE — reported per side; the
  candidate condition requires the **short** side (the literature's carrier) and reports the long.
- **T4** era-2 combined net (crossed) > 0 by 2 SE.
- **T5** concentration: names to half the P&L ≥ 20 on the combined book, and the top 1% of trades
  ≤ 50% of P&L (a supply effect should be broad; a lottery book is not the thesis).

**Candidate for the holdouts: T1 ∧ T2 ∧ T3(short) ∧ T4 ∧ T5.** Before any holdout read the
holdout names need their own CIK resolution and EDGAR pull under a separate record, and the
principal's explicit word for each file. Caps 63/252 and n_max None are robustness lines; if the
primary fails and a robustness line passes, that is reported as a failure with a note, not as a
pass.

## 6. Predictions (MODERATE; from the literature and D444's shape, none from a return)

- **X-a** per trade at cap 126: short side (issuers) gross **+40 to +120 bp** per 126-bar trade
  (the literature's 3–6%/yr underperformance, hedged, half a year); long side (repurchasers)
  **+20 to +60**; medians below the means on the short side (the collapses carry it).
- **X-b** the combined book: gross **+1.5 to +3.5 bp/bar**, SE ≈ 1.2–1.6 (two deciles of ~40
  names, hedged); crossed cost ≈ 0.4–0.8 bp/bar (turnover ~0.6%/bar at 50–70 bp round trips) plus
  borrow ≈ 0.3–0.8 on the short side → **net +0.5 to +2.5, T2 a coin at 2 SE**; the short leg
  contributes more than the long.
- **X-c** C1 p50 ≈ 0 per trade on both sides (state-matched names in these cells earn nothing
  hedged) — the increment over C1 ≈ the gross; C2 p50 ≈ 0, p95 ≈ +1.5 to +2.5 bp/bar (the persistent
  selector on rotated dates has real variance); C3 p95 within ±0.5 of C2's — if C3's p95 is far
  above C2's, the persistence itself is doing something and the record says so.
- **X-d** T1 passes on C2 and is a coin on C3; T3 passes on the short side, fails or is marginal
  on the long; T5 passes (≥ 30 names to half); era 2 weaker than era 1 (the buyback era compresses
  the long leg): T4 fails more likely than not.
- **X-e** cap 63 gross per bar within 30% of cap 126; cap 252 lower per bar; n_max None lowers
  gross per bar by 20–40% (dilution past the extremes).
- **X-f** the short side's HTB share > 20% of trades and its borrow > 5 bp per trade — the
  issuers are the hard-to-borrow names — and the short-side crossed 2c is 60–90 bp.

## 7. Not in scope

Any holdout; any sizing beyond equal weight; any second score (NIY, flows); any sweep of the
decile cut; the multi-class names. Forty-fourth look by object; look #1 of the issuance line's
forward-return ledger.

## 8. Files

This record · `scripts/run_d446_issuance_book.py` (`--run`, `--selftest`) ·
`data/d446_issuance_book.json` · RESULT.
