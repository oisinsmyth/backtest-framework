# D726 STAGE 0 PRE-REGISTRATION — did daily 0DTE options end the last-half-hour continuation? Three cheap premise checks: the era, the weekday natural experiment, and the day's 0DTE dose

*2026-10-01.*
- *The principal: "OK I like #1, pre-reg the cheap premise checks, build and run please", after the menu that followed
  [D722](D722-DIAG-RESULT-no-variable-explains-2022.md).*
- *Numbered D726 after telling the other session (it holds D725).*
- ***Committed alone, before its runner exists.** In-sample only: 2018-05-14 → 2023-12-29. Nothing dated 2024-01-01 or
  later is read on any root. No programme slot, no vault look, and D716 (NQ F2, slot 7) is untouched.*

## 0. Why, and what is already known

**The question:**
- D722 found that the unfiltered last half-hour (sign of 14:30 → 15:30, held 15:30 → 16:00) earned all of its 2022
  before **2022-05-16**, the first session from which every weekday carries a same-day SPX expiry (OA-A12), and lost
  after it (ES −$414, NQ −$213).
- The vault (2025-03 → 2026-09) lies wholly in the daily-0DTE era.
- **If daily 0DTE ended the continuation, that bears directly on NQ F2's vault look.**

**Known before this record (disclosed):**
- **D722's per-year direction efficiencies** of the unfiltered half-hour (Σg/Σ\|g\|):

  | root | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 |
  |---|---:|---:|---:|---:|---:|---:|
  | ES | 0.13 | −0.00 | 0.08 | 0.17 | 0.18 | 0.03 |
  | NQ | 0.11 | −0.03 | 0.07 | 0.11 | 0.23 | 0.04 |

- **The ES option expiry calendar**, counted from `fut_es_options_eod` to write this record. It is a calendar fact, not
  an outcome. Sessions with a same-day PM-settled ES option expiry:

  | era | Mon | Tue | Wed | Thu | Fri |
  |---|---:|---:|---:|---:|---:|
  | before 2022-05-16 | 225 | 36 | 288 | 24 | 290 |
  | from 2022-05-16 | 69 | 84 | 85 | 83 | 79 |

  - So before the date, **Tuesdays and Thursdays almost never had a same-day expiry** (their 36 and 24 are month-end
    days). After it, every weekday did.
  - **The median same-day option volume to 15:29** was 60,828 contracts on expiry sessions before the date and 186,573
    after.

**A proxy.** ES futures options stand in for the whole 0DTE complex. The dominant venue is Cboe's SPX, whose weekday
expiries were added on the same calendar (Monday and Wednesday from 2016–17, Tuesday and Thursday from 2022-04/05). No
SPX volume is on disk.

## 1. The object

**K2 (D722 §1):** take-everything 15:30 → 16:00 on the sign of 14:30 → 15:30, every in-window session.
- ES at one MES, $4.42; NQ at one MNQ, $4.067121.
- 2018-05-14 → 2023-12-29: ES 1,360 sessions, NQ 1,389.
- Read through `scripts/diag_d722_lines.py` `load_lines()`, which re-validates D711's known answers on every load.
- **ES is primary; NQ is reported beside it with the same calendar,** since NDX's dailies are not separately measured
  here.

**The outcomes:**
- **Direction efficiency** e = Σg / Σ\|g\| on gross dollars (D711-A1's statistic);
- **u**, the volatility-normalised gross of D722 §2 (sig20 from `diag_d722_conditioners`), beside it.

## 2. The three premise checks

**S1 — the era.**
- **Compared:** e after the date (2022-05-16 → 2023-12-29) against e **before it excluding 2022** (2018-05-14 →
  2021-12-31).
  - January → mid-May 2022, the bulge D722 found, is excluded from the primary comparison because it would decide any
    before/after test by itself.
  - The comparison with the bulge included (2018-05-14 → 2022-05-13) is reported beside it.
- **The test:** Δe = e_after − e_before, with SE from a block bootstrap over ISO weeks (each era resampled by its own
  weeks), 10,000 draws, seed 726.
- **Supports the premise if Δe < 0 and Δe / SE ≤ −2.**
- A placebo-date profile (Δe at every split date with ≥ 250 sessions each side, contiguous) is reported only. The
  bulge sits just before the declared date, which makes any such ranking self-fulfilling.

**S2 — the weekday natural experiment (a difference in differences).**
- **Before the date** (2018-05-14 → 2022-05-13): Δ_pre = e(sessions **without** a same-day PM expiry) − e(sessions
  **with** one).
- **After the date** (2022-05-16 → 2023-12-29), where every day has one: Δ_post = e(Tue, Thu) − e(Mon, Wed, Fri). This
  is the weekday control.
- **DiD = Δ_pre − Δ_post.**
- **Under the hypothesis:** no-expiry days continue more before the date (Δ_pre > 0), and the weekday difference
  vanishes after it, so DiD > 0.
- **The SE:** week-block bootstrap over both eras, 10,000 draws, seed 726.
- **Supports the premise if DiD / SE ≥ 2.**
- Δ_pre and Δ_post with their SEs are reported beside it.

**S3 — the day's 0DTE dose (after the date).**
- **The variable:**
  - V0 = Σ `vol_to_1530` over ES options whose `expiry_date` equals the session and whose `expiry_hhmm` ≥ "15:30"
    (PM-settled; D613 (vi)).
  - F = ES futures volume 09:30–15:29 (`fut_ES_rth_1m`, bars 09:30 … 15:29).
  - Z = ln(V0 / F) minus its median over the prior 20 sessions on which it is defined, so the secular rise is removed.
  - Z is known at 15:30. It uses nothing from the scored window: D613 says `vol_to_1530` is midnight to 15:29.
- **The test:**
  - Spearman ρ(Z, u) over the era's sessions;
  - an exact enumerated circular-shift null, shifting Z's series against u by every lag 1 … N−1.
- **Supports the premise if ρ is at or below the null's 5th percentile** (one-sided: more 0DTE, less continuation).
- **Reported beside:** the same ρ before the date on expiry sessions only, with its own rotation.

**The Stage 0 reading (ES; NQ beside, not read):**

| reading | when |
|---|---|
| **SUPPORTED** | S2 supports **and** at least one of S1 and S3 supports |
| **PARTIAL** | exactly one of S1, S2, S3 supports, or S1 and S3 support without S2 |
| **NOT SUPPORTED** | none supports |

**What each means:**
- **SUPPORTED:**
  - The continuation looks like a no-0DTE-day phenomenon.
  - D716's vault look (all daily-0DTE era) is then a bet against its own premise, and that is recorded beside D716,
    which stays unchanged.
  - A 0DTE-conditioned design would be the principal's call, for unseen data only.
- **NOT SUPPORTED:** the post-May loss is not 0DTE by these measures, and the line stays as D722 left it (UNEXPLAINED).

## 3. The runner's assertions (each shown to raise in `--selftest`)

1. **The seal.** Every input is filtered below 2024-01-01 as it is read, and asserted. A planted 2024 row raises.
2. **Known answers.** K2's D711 per-year n and mean net, through `load_lines`.
3. **The expiry calendar.**
   - It reproduces the §0 counts per weekday and era exactly.
   - **Right-quantity:** including AM-settled expiries must change the counts (canary).
4. **The variable is lagged.**
   - Z at session t uses only V0 and F of t (to 15:29) and the prior 20 sessions' values.
   - A second implementation by loop must agree.
   - A version using `v_1530_1600`-like same-window volume (simulated by adding the next session's value) must be
     caught.
5. **The statistics:**
   - The DiD identity is checked.
   - The bootstrap is checked: chunk == whole bit-identically, and the SE is non-degenerate.
   - The rotation is checked: shift 0 equals the reported ρ, and a planted negative dose is detected.
   - The reading logic is checked on synthetic inputs giving each reading.

## 4. Predictions (mine, before the runner exists)

| # | prediction |
|---|---|
| 1 | S1 does **not** support on ES: Δe is negative but z > −2 (D722's years suggest about −0.06 against an SE of about 0.06) |
| 2 | S2 does **not** support on ES: DiD / SE < 2 |
| 3 | S3 does **not** support on ES: ρ above the rotation's 5th percentile |
| 4 | the reading is **NOT SUPPORTED** |
| 5 | NQ reads the same as ES |

**Power, stated now:**
- About 400 sessions after the date and about 900 before it (ex-2022). An efficiency difference of about 0.1 is
  roughly 1.5–2 SE.
- **These checks can find a large effect, not rule out a small one.** A NOT SUPPORTED is weak evidence against 0DTE,
  and will be recorded as such.
