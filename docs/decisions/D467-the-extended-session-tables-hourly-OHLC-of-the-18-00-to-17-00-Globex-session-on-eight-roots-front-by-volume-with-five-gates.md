# D467 — the extended-session tables: hourly OHLC of the 18:00 → 17:00 Globex session on eight roots, front month by volume, from the CME archive, with five gates

**Pre-registration of a DATA-LAYER build. Committed before the builder exists (R8).** Result in a
separate file. **No study, no return, no candidate: tables and their gates only.** D467 taken after
`ls docs/decisions` and `git log --all` on both worktrees showed D466 as the highest number.
Declared in D466 §5 as the widening step the components ledger needs.

## 0. Why

D466 opened the ledger empty: the constructions that exist have gross Sharpe 0.6–0.7 at micro
size and the $3 round trip (~2 bp of a micro's notional) eats them. **A component is found where
the gross edge per round trip is large against the cost**, and the one construction here with
that shape — one round trip per night, the whole session held (C1) — has been measured on ES
only. The other seven liquid roots in the archive (NQ, YM, ZN, ZB, GC, CL, 6E) carry the same
session and have never been read. D449 built C1's table from the raw archive for one question;
this record builds the reusable session tables once, for every root, on an hourly grid, so that
any window that starts and ends on the hour — the overnight hold, the day session, the
overnight-only leg, and anything D468 declares — is scored from a committed fixture and not from
111 GB.

## 1. Source and scope, declared

- **Source:** `data/raw/databento/*/glbx-mdp3-*.ohlcv-1m.dbn.zst` — the same 26 files D462 read
  (2010-06-06 → 2026-09-09), read once with the system interpreter's `databento`, chunked as D462.
- **Roots:** **ES, NQ, YM, ZN, ZB, GC, CL, 6E** — outrights only, symbols matching
  `^(ES|NQ|YM|ZN|ZB|GC|CL|6E)[FGHJKMNQUVXZ]\d{1,2}$`; no spreads, no micros (the micro's price is
  the full contract's; the size unit is declared per root in §5 for the scorer, not built here).
  RTY stays held back (D462 G4).
- **Clock:** `ts_event` → US/Eastern with DST; a bar's timestamp is its start. **The session is
  18:00 on calendar day `a` through 16:59 on calendar day `b = a + 1`**, 23 hourly segments
  `h18 … h23, h00 … h16`; the 15:59 bar's close is the 16:00 print (D448's convention) and it
  is the close of segment `h15`. Nothing before 18:00 on `a` or after 16:59 on `b` is kept
  (the 17:00–18:00 halt holds nothing).
- **Front month per (root, calendar ET day) = the outright with the highest full-day volume**,
  D448's and D462's rule. **A session row carries the front of day `b`** and its evening
  segments are taken from that same contract's bars on day `a`; `front_prev` is the front of
  day `a`, and **`same_front` = (front_prev == contract)**. D449 dropped the roll nights; the
  table keeps them flagged so the scorer drops them and the count is visible. **No stitching,
  no back-adjustment.**
- **A session is PRESENT** when its bars in `h09 … h15` number at least 200 (D462's G5 rule,
  moved to the day-session hours). Absent sessions are not rows; G5 counts them.

## 2. Outputs

- `data/fixtures/fut_sessions_hourly.csv.gz`, one row per (root, day `b`): `root, day, prev_day,
  contract, front_prev, same_front, bars`, then for each of the 23 segments `hHH_o, hHH_h,
  hHH_l, hHH_c, hHH_v, hHH_n` (open, high, low, close, volume, one-minute bars; NaN and 0
  where the segment has no bar). Prices in points, `PX = 1e-9`. ≈ 8 × 4,100 rows; committed.
- `data/fixtures/fut_sessions_rolls.csv.gz`: every front-month change per root with the day, the
  two contracts and their volumes that day.
- `data/fixtures/fut_sessions_hourly.meta.json`: provenance, the gates, `usable_start` per root.

## 3. The five gates (mandatory before any study reads a root; a root that fails is held back)

- **G1 — no unexplained bar.** Every one-minute close-to-close move inside one session on one
  contract with |r| above the root's threshold is listed with day and minute: **ES/NQ/YM 1.0%,
  ZN 0.5%, ZB 0.75%, GC 1.5%, CL 3.0%, 6E 0.75%**; the list is at most **150 bars per root**
  over the span (the session is 3.5× the regular hours D462 gated at 40) and each bar on it
  must fall on a day the RESULT can name. **CL's negative print (2020-04-20, CLK0) is declared:**
  returns are computed only where both closes are positive, and the two CLK0 sessions are
  listed, not counted.
- **G2 — rolls forward, never reverting, at the expected cadence.** Per root every front change
  is forward in (year, month) order; reverting changes are **zero** on ES, NQ, YM, ZN, ZB, 6E and
  at most **2** on GC and CL (listed); the number of rolls per full year is within **[k−1, k+2]**
  of the product's cadence: **k = 4** (ES, NQ, YM, ZN, ZB, 6E), **k = 6** (GC: G, J, M, Q, V, Z),
  **k = 12** (CL). Days-before-expiry is not computed here (five expiry rules); the cadence test
  replaces it.
- **G3 — session coverage.** Bars per present session: **p50 ≥ 1,300** of 1,380 on ES, NQ, YM,
  ZN, ZB and **≥ 1,200** on GC, CL, 6E (empty minutes are absent from ohlcv-1m); sessions below
  900 bars are listed; the 16:00 print (`h15_c`) is present on ≥ 99% of present sessions.
- **G4 — independent cross-check.** Daily close-to-close returns of the 16:00 print on
  same-front session pairs against the ETF close in `etf_wide_daily_raw` on matched days:
  **ES/SPY, NQ/QQQ, YM/DIA ≥ 0.99** (D462 reproduced); **ZN/IEF ≥ 0.90; ZB/TLT ≥ 0.90; GC/GLD
  ≥ 0.95; CL/USO ≥ 0.85** (USO's roll structure and April 2020); **6E/FXE ≥ 0.90**.
- **G5 — presence against the equity calendar, per year**, as D462's ADDENDUM: `usable_start` per
  root is the first day of the first year from which every later year has ≥ 97% of SPY's trading
  days present; a root with no such year fails.

**A gate that fails holds that root back**; the table is still written with the root's rows so
the failure is inspectable, and the meta marks `passes: false`.

## 4. Predictions (LOW stakes — a data build — written so the build is checkable)

- **X-a** `usable_start` is **2016-01-04 for all eight roots** — the archive's missing day
  sessions before 2016 (D462) are a property of the archive, not of the index products
  (moderate confidence; the alternative is that ZN/ZB/GC/CL/6E are usable from 2010-06).
- **X-b** G1 counts: ES/NQ/YM **20–80**, ZN **< 20**, ZB **< 30**, GC **20–60**, CL **50–150**
  (2020-03/04 and the 2022-03 sessions), 6E **< 30**.
- **X-c** G4: ES/SPY ≥ 0.995; ZN/IEF **0.93–0.97**; ZB/TLT **0.95–0.98**; GC/GLD **0.97–0.99**;
  CL/USO **0.90–0.97**; 6E/FXE **0.95–0.98**.
- **X-d** rolls per year: 4 on the six quarterly roots, 6 on GC, 12 on CL; reverting rolls 0
  except **GC 0–2**.
- **X-e** bars per session p50: ES/NQ/YM **1,360–1,380**; ZN/ZB **1,300–1,370**; GC **1,250–1,350**;
  CL **1,320–1,375**; 6E **1,250–1,350**.
- **X-f** runtime **20–30 min** for the read (D462's read was 20), background, logged to
  `temp/d467_build.log`.

## 5. Declared for D468 (the scorer; not built here)

Minimum tradable size and the declared cost per round trip, so that D468's component lines are
computed under the cost the account pays (the D466 lesson): **MES $5/pt, MNQ $2/pt, MYM $0.50/pt,
MGC $10/oz, MCL $100/bbl, M6E $12,500 × Δprice — all at $3; ZN and ZB have no micro: one
contract, $1,000/pt, $6 a round trip** (range estimators, D439's caveat; the TWS quote pull
would settle them). Windows are declared in D468, from this table's hourly grid, and scored in
the ledger's order with the sign-randomisation null of the maximum across the declared set
reported beside the best (the multiplicity D466 §2 owes).

## 6. Files

This record · `scripts/build_fut_sessions_hourly.py` (`--build`, `--gates`, `--selftest`) ·
`data/fixtures/fut_sessions_hourly.csv.gz`, `fut_sessions_rolls.csv.gz`,
`fut_sessions_hourly.meta.json` · RESULT.
