# FINAL — Opus pair (conservative + creative): leads for a new reversion effect at micro size

**Result: 5 leads, each accepted explicitly by both agents. They do not rest on five independent mechanisms.**
- **AGREED Leads 1–4 rest on two mechanisms:**
  - a price set in a futures-only book, while the reference venue is shut, is repriced when the venue reopens
    (AGREED Leads 1, 2, 3);
  - forced closing-auction flow reverts overnight (AGREED Lead 4).
- **AGREED Lead 5 is not new in mechanism.** It is AGREED Lead 4's mechanism with a new, directly measured predictor (the
  exchange's published closing-cross imbalance). It is a data-missing lead: no on-disk premise test, a sourced size
  estimate, and a USD 128 quote.
- **The pair did NOT find a fifth independent mechanism at the bar** after about 35 further constructions, all listed
  below. The bar was not lowered and no lead was padded. Lead 5 was accepted because it is a falsifiable, priced test
  whose own kill clause rejects it if it is merely Lead 4.

Full records in the brief's format are in `AGREED.md`. Scripts and outputs are in `opus_pair/scripts/` and
`opus_pair/out/` (`cons_*` = conservative, `crea_*` = creative). All figures are in-sample 2016–2023, gross dollars
per ONE micro, beside the micro round trip (RT). Nothing dated 2024-01-01 or later was read.

**Why we believe the shared mechanism.** It survived falsification tests that could have killed it:
- Treasuries, whose cash market is OPEN at 08:30, continue after CPI/NFP; they do not revert.
- An ECB decision in the same cash-shut window continues.
- Commodities after their own settlement continue, because Globex is their venue: CL, NG, SI, GC, API crude, LME
  copper, and the grains overnight.
- The opening auction is not reversed.
- Other cash-shut hours on the index roots do not revert.
- Pre-open moves on non-release days do not revert.

## The five leads, ranked

| rank | lead | instrument / clock | gross per micro (RT) | key evidence | main reservation | prior |
|---|---|---|---|---|---|---|
| 1 (AGREED L1) | **Fade the CPI/NFP 08:30 impulse: the cash open reprices a US tier-1 release** | MNQ (MES, MYM, M2K transfers); impulse 08:29→08:34, fade 08:34→11:00 (09:29→11:00 declared) | +$34.88 (RT $4.07), median +$12.75, t 2.73, n 186; MES +$16.69 | random-day null rank 1.000; matched-impulse null 0.9995; plateau for K ≥ 3, exits 10:30–12:00; the give-back is 09:30–11:00; large non-release 08:30 moves, the ECB and Treasuries all CONTINUE | 24 events/yr; the first 1–2 min of CPI continue (K ≥ 3 only); $ scale with 2020–23 price × vol (2016–19 +$8.20 = 2× RT) | 25–30% |
| 2 (AGREED L2) | **Post-cash-close transience: fade the 16:00–17:00 move overnight** | MNQ, MES, M2K; m = 16:00→17:00, q80 gate; fade 18:05→10:00 next day | MNQ +$24.62 (ex-2020-and-2022 +$17.11); MES +$12.63; M2K +$11.07 | exact rotation rank 0.985–0.997 on three roots; with the day controlled, a post-close point gives back about 3× an afternoon point (not K8); other cash-shut hours do not revert; the transient window moved when CME moved settlement and the halt (2020-10, 2021-06) | **the principal closed "any gate … on the index overnight leg at micro cost" (BOOK_PROP, 2026-09-12): needs the principal's ruling first**; NQ/ES 2024+ overnight is spent, so confirm on M2K/MYM or the day leg; about half of NQ P&L is 2022; both of the conservative's original acceptance conditions failed | 20% |
| 3 (AGREED L4) | **Closing-auction pressure on the Russell micro: fade 15:50→16:00 overnight** | M2K (MES, MYM secondary); c q80; fade 18:05→10:00 | +$14.75 (RT $3.76), t 2.48, n 312; ex-2020-and-2022 +$14.48 (3.9×) | rotation rank 0.991–0.999; 5/6 years > 0; ρ with Lead 2 ≈ 0; Bogousslavsky & Muravyev (closing deviations revert overnight); D762 found no reversal at 10 minutes | RTY was chosen after seeing four roots (small-cap dose argument post hoc); ES/YM 2020/2023-carried; the same overnight closure; 6 years of RTY | 15% |
| 4 (AGREED L3) | **Gold's weekend reopen: fade Friday close → Sunday first hour into the Monday US morning** | MGC; m = Fri 16:59 → Sun 18:59; fade 19:00 Sun → 10:59 Mon | +$15.93 (RT $5.93), t 2.31, n 390, 8/8 years > 0 | exact rotation rank 1.000; only the reopen window reverts of seven GC off-hours windows; the Sunday spread equals the weekday spread (paid bbo-1m) | 2020 = 43% of P&L; right-tail carried (trimmed +$14.55); gold-only (no transfer to 18 roots); ex-2020 1.4–1.95× RT; split the hold at 21:00 ET against D765 | 15% |
| 5 (AGREED L5) | **(Data-missing) The measured Nasdaq closing-cross imbalance predicts the MNQ overnight give-back** | MNQ (MES/MYM declared); I = Nasdaq-100 signed $ imbalance at 15:55, top quintile; fade 18:05→10:00 | estimate +$14.6–21.9/MNQ (3.6–5.4×) if capture rises from 16% to 20–30% of the $73 mean closing move | the same source as AGREED Lead 4; an on-disk proxy (calendar-known big-MOC nights) lifts NQ capture to +0.49 vs −0.03 over all nights (n 107, t 1.46), but it is reversed on the q80 subset; quote USD 105.69 (2018-05→2023) + 22.73 (2024) | **same mechanism as AGREED Lead 4** (new predictor only); not premise-tested on its own data; the purchase needs the principal; 5.7 years in-sample; the overnight closure; report ρ with AGREED Leads 2 and 4 | 8–10% |

(The table's ranks differ from the lead numbers in `AGREED.md`: table 3 = AGREED Lead 4 (RTY auction); table 4 =
AGREED Lead 3 (gold); table 5 = AGREED Lead 5.)

**For the principal, before any pre-registration:**
1. AGREED Leads 2, 4 and 5 hold an index micro over the overnight leg you closed for the prop book on 2026-09-12. All three
   are SIGNED fades, with P&L = −sign(trigger) × the overnight return, so none collects the long drift. Whether they
   fall outside the closure is your call.
2. The NQ/ES 18:00 → 09:00 2024+ slice is spent. Confirmation is declared on M2K/MYM, or on the day leg.
3. Lead 5 needs a purchase of about USD 128 (Databento XNAS.ITCH imbalance; free metadata quote only).
4. Lead 1 is the only lead with neither a closure question nor a purchase. It is the one the conservative would spend
   research time on first.

## Strongest candidates dropped (one line each)

- **EIA petroleum / NG storage 10:30 fade:** NG storage CONTINUES; the CL best cell is t 2.07 of 45 cells. Noise.
- **API crude survey (Tue 16:30) fade:** continues; −$6.53/MCL, 0/8 years.
- **ISM 10:00 fade:** signs flip with K.
- **FOMC 14:00 knee-jerk:** t < 1.7, n 63, 2022-carried.
- **ECB decision fade (07:45 ET):** continues on every root; NQ −$16.28, 2/8 years.
- **Treasury CPI/NFP fade on micro yields:** continues on every tenor.
- **Post-close mega-cap earnings:** season split t −0.05; the NQ−ES residual is weaker than the raw move. Replaced by
  Lead 2.
- **Commodity post-settlement fades and the European close:** they continue, or rank 0.10–0.92.
- **The 16:00–17:00 hour on commodities:** CL continues; GC/NG/SI are not robust ex-2020–22. Kept as evidence for
  Lead 2 only.
- **Weekend reopen on 18 other roots:** no transfer.
- **Index weekend reopen to the European open:** NQ 2.5× RT, rank 0.961, but ES 1.5×; RTY/YM nil; unconfirmable on a
  spent slice.
- **Other index overnight windows; the pre-open on non-release days; the opening auction:** no reversion (ranks
  0.13–0.92).
- **Grains overnight gap fade:** big overnight moves continue (as D768 found).
- **Vol-targeting close pressure:** ES ex-2020 +$1.19. A 2020 artefact.
- **SqueezeMetrics DIX contradiction fade:** conservative rebuild rank 0.537 on NQ; 2020 = 50–90% of P&L; the bp edge
  collapses outside 2020–23; no plateau.
- **0DTE chase (call share of same-day volume):** chase ≈ counter days.
- **CL/NG option-expiry pin release:** no pin (settles closer to K* in 27–30%); repulsion, as D614/D618 found.
- **Micro (retail) share of volume, broker margin cut-off:** no interaction; ρ 0.5–0.6 with AGREED Lead 4.
- **CME velocity-logic pauses:** rare and lumpy.
- **CME bitcoin vs spot basis:** sub-cost.
- **CTA trend-flip:** mixed signs.
- **Cross-asset lone movers:** about $0.
- **SHFE breaks, LME close, WM/R daily fix, post-London FX:** nil or sub-cost.

## Dissent

- **Creative:** would rank Lead 2 level with or above Lead 1. Lead 2 has the most evidence: four-root exact rotation
  ranks, the per-point regression and the exchange natural experiment.
  - **Conservative's reply:** Lead 1 stays first, as the only lead free of the principal's overnight closure and of a
    spent confirmation slice.
- **Both:** AGREED Lead 5 is a predictor upgrade of AGREED Lead 4 (RTY auction), not a fifth mechanism. If the principal counts
  mechanisms rather than leads, the pair delivered four leads on two mechanisms plus one priced extension.
- **Conservative:**
  - My priors are low (8–30%) and I stand by them. Every lead carries a crisis-year or selection reservation.
  - Three of the five may be voided outright by the principal's 2026-09-12 closure.
