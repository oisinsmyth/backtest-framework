# D578 — PRE-REGISTRATION: **the corrected hedging-flow mapping — the swap-dealer NET short of CL against the 12–24-month strip at eight weeks, with the ratchet and the calendar as declared clauses — tested once on the 2024-01 → 2026-08 disaggregated reports**, on the principal's word

**Pre-registration. Committed before the runner exists and before any 2024+ report or session is
read for this line (R8).** Result in a separate file. **This record spends the CL disaggregated
2024+ reports for the hedging-flow line, and it reads the CL 12–24-month settlements
2024-01 → 2026-09 as a regressor: after it, the CL deferred curve's forward path is seen, and
any later CL curve study on those tenors must say so.** No return is computed. Nothing is
admitted (R15).

*2026-09-20, on the principal's word after D577. P9 failed on its declared statistic — the
gross short of neither category responds to the strip over four weeks — and the statistics
declared beside it pointed to a different instrument: the swap-dealer **net** short, which
responded at t 2.7 over four weeks and 3.7 over eight on 2010–2023, with the producer/merchant
net short moving the other way, and whose yearly levels tracked the derivation's three natural
experiments. That mapping was chosen after reading 708 reports, so it cannot be tested on
them. It can be tested on the 139 weekly reports from 2024-01-02 to 2026-08-25, which nothing
in this programme has read. This record writes the corrected mapping down with its predictions
before those reports are opened. The scale gap D577 found — a measured response two orders of
magnitude below the derivation's population arithmetic — is carried as a question the read must
answer, not a claim it can settle.*

**What was seen (D577, 2010–2023).** SD net short on the strip: β +28.0k / +44.1k / +70.9k
contracts a log-point at 2 / 4 / 8 weeks, NW t 2.46 / 2.69 / 3.71; PM net short −16.6k / −39.5k
/ −74.1k, t −1.10 / −2.02 / −3.58; SD gross short +37.0k at eight weeks (t 2.13, rank 0.982);
PM+SD net ≈ 0. The split-by-sign and calendar tests were run on the **gross** line only; on the
net line they are **unseen** and are the derivation's own predictions. **Not seen:** any 2024+
report; any 2024+ settlement of CL.

---

## 1. The construction

- **Reports.** CFTC disaggregated futures-only, CL (`067411`), report dates 2024-01-02 →
  2026-08-25 (the fixture's last for this symbol), **139 weekly reports**. Positions keyed on
  the report date (the question is what positions did; nothing here is a trading signal).
- **Prices.** The CL settlement strip at each report date (last session on or before it),
  D562's forward session calendar; `logF_strip` = mean log settlement of delivery months
  *m*+12 … *m*+24, as D577 built it; `logF_1` beside.
- **The instrument.** `NS_SD` = swap-dealer short − swap-dealer long, in contracts; `NS_PM`
  likewise; `GS_SD` the gross short, beside.
- **Horizon.** **h = 8 reports (primary)**; h = 4 secondary; changes `Δ(8) = x(t) − x(t−8)`
  overlapping weekly, Newey–West lag 8; the non-overlapping version (every eighth report,
  ~16 observations) beside, sign only.

## 2. The statistic and the null

> **PRIMARY: β in `ΔNS_SD(8) = a + β · ΔlogF_strip(8)` on the forward reports**, with its
> Newey–West t and its rank in the **exact circular-shift null** (the regressor shifted against
> the outcome by every offset in [8, N−8], ~115 offsets), the non-overlapping β's sign beside.

**Harness before any forward number:** the runner recomputes the in-sample β on 2010–2023 by
the same code and asserts it equals D577's artifact (+70,910 at eight weeks, +44,057 at four)
to 1e-6.

## 3. Predictions — in the runner's quantities

| # | prediction | declared value | source |
|---|---|---|---|
| **C-1** (primary) | β_SD(8) **> 0**, NW t **≥ 2**, **above the shift null's p95**; point **30k – 110k** contracts a log-point | | in sample +70.9k; a forward number between half and one and a half times it |
| **C-2** | β_SD(4) > 0 | | in sample +44.1k |
| **C-3** (the other side) | β_PM(8) **< 0** (producer/merchant net short falls on strip rallies) | | in sample −74.1k; the netting D577 found |
| **C-4** (the ratchet, unseen on this line) | β_SD(8) on rallies (ΔF > 0) **> β_SD(8) on declines**; the declines' β **inside its own shift null's p05–p95** | | the derivation's §2.4: selling arrives on rallies; nothing arrives on declines |
| **C-5** (the calendar, unseen on this line) | mean `ΔNS_SD(1)` on reports dated Feb–Mar and Aug–Sep **> 0 and > the other weeks'** | | the derivation's §4.3; low confidence, stated: D577 saw nothing on the gross line |
| **C-6** (scale) | β_SD(8) ÷ mean strip price within **a factor of three of +1,060 contracts per $1** (the in-sample figure); **and** the derivation's prior of 18–37k per $1 remains **≥ 10× above** the measured response | | the scale gap is expected to persist; if it closes, the record says the flow arrived in futures at the tenors after 2023 |
| **C-7** (gross beside net) | β on `GS_SD`(8) > 0 and **smaller than** β on `NS_SD`(8) | | in sample +37.0k vs +70.9k |
| **C-8** (the two forward episodes the derivation names, §11) | the eight-report change in `NS_SD` starting from the first report after **2025-06-13** (the June 2025 rally, "record hedging") and from the first report after **2026-03-01** (the March 2026 spike, "heavy hedging") are each **positive and in the top quartile** of all eight-report changes on the forward sample | | qualitative in the derivation; made quantitative here before reading |
| **C-9** (falsifiers) | β_SD(8) ≤ 0 or inside the null → **the corrected mapping does not transfer** and the derivation has no weekly instrument on this report; β_PM(8) ≥ 0 → the netting story fails; C-4 failing while C-1 holds → the response is symmetric and the ratchet is not in the data | | |

**Verdict rule.** **TRANSFERS**: C-1 and C-3 hold. **PARTIAL**: C-1 holds and C-3 does not.
**DOES NOT TRANSFER**: C-1 fails. C-4 to C-8 qualify the verdict and do not change it.

## 4. What follows, declared

- **TRANSFERS**: the hedging-flow line has a measured weekly instrument — SD net short at eight
  weeks — and the derivation's P1–P3 (response, ratchet, breakeven regime) are pre-registered
  on it next, on the full 2010–2026 span with the forward sample's role stated; P7 needs the
  Dallas Fed series and is a fetch. P8, the only prediction that touches a return, stays
  unread.
- **PARTIAL**: as above for P1–P3; the two-category netting is dropped from the derivation's
  measurement mapping in writing.
- **DOES NOT TRANSFER**: the derivation's flow model has no weekly instrument in the COT as the
  report is built, and the line stops at the measurement, as the deposit's §12 says; the
  scale gap stands as the reason.

## 5. Runner assertions

The harness equality of §2 at 1e-6 before any forward read. D577's audits on the forward
objects: the tenor by a second strip path (raises on a shift); the OLS by statsmodels HAC and
the hand-rolled Newey–West (raises on a negated regressor); the synthetic-flow check of the
sign convention on the forward regressor; the shift null's zero offset reproducing the
observed β. **The runner refuses without `--principals-word`** and records the instruction it
ran under. `encoding="utf-8"` everywhere.

## 6. What is read, and what is not

The COT fixture, disaggregated, CL, reports 2010-06-08 → 2026-08-25 (the in-sample part for
the harness only); the CL settlement strip 2010-06-04 → 2026-09-10 at the report dates; the
forward session calendar. **No return is computed on any instrument. Nothing else's slice is
touched.** After this run the CL disaggregated 2024+ reports are spent for the hedging-flow
line and the CL 12–24-month settlement path 2024–2026 is seen.
