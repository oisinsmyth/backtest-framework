# AGREED leads — Opus pair (conservative writes; each lead accepted explicitly by both)

All figures in-sample (sessions 2016-01 → 2023-12), gross dollars per ONE micro unless marked net. Micro round trips
(data/futures_costs.json default lines): MNQ $4.07, MES $4.42, MYM $3.80, M2K $3.76, MGC $5.93, MCL $5.03,
MNG $4.00 (one-tick convention), SIL $8.00. Scripts and outputs live in `opus_pair/scripts/` and `opus_pair/out/`.

---

LEAD 1: The cash open reprices a tier-1 release: fade the CPI / NFP 08:30 impulse on MNQ (MES secondary)
- Mechanism (who is forced/mistaken; source): at 08:30 the headline number is priced in seconds by headline-reading
  algorithms in a futures-only, pre-cash book. The composition (core vs headline, revisions, wages, participation)
  and the 09:30 cash-equity open, which brings full liquidity and the cash/ETF arbitrage, re-price it. The headline
  overshoot gives back, and most of the give-back happens AFTER 09:30. The evidence that this is specific: large
  08:30 moves on non-CPI/NFP days CONTINUE. Gold does not transfer (GC CPI reverts, GC NFP continues −$17.49),
  consistent with an equity-cash-open mechanism. The ISM release at 10:00 (after the open) does not revert.
  Literature on fast announcement pricing: Andersen, Bollerslev, Diebold & Vega (2003). The overshoot-and-cash-open
  reading is ours and is the thing the pre-registration tests.
- New because (nearest prior D-number and the difference): the unconditional opening gap fade (D644–D660, +0.40
  bp/session, 2022-carried) and D487 (ES first half-hour reverses into the last, 2020–22). The difference is
  conditioning on a scheduled tier-1 release. The placebo says gaps without such a release do not revert:
  non-event days 08:34→11:00 NQ −$3.32, and −$8.63 on their top third by impulse. No record tests a
  release-conditioned fade on the index micros. D743 used CPI only as a skip/veto on another construction.
- Instrument / clock / trigger / entry / exit: MNQ (MES, MYM and M2K as declared transfers). Trigger: CPI or
  Employment Situation day with a release at 08:30 ET (data/calendar/events.csv). Impulse = close of the 08:33 bar −
  close of the 08:29 bar (bar-start stamps, i.e. the 08:34 and 08:30 prints). Entry against the impulse at the 08:34
  print. Exit at the 11:00 bar close. Declared secondary: same sign, entry at the 09:29 bar close (the 09:30 print),
  exit 11:00. K must be ≥ 3 minutes: the first 1–2 minutes of CPI continue.
- Predictor (pre-entry only): the sign of the 08:29→08:34 move on a scheduled release day. The calendar is a
  published schedule, known in advance.
- Premise test: `scripts/cons_macro830_fade.py`, `cons_macro830_robust.py`, `cons_macro830_grid.py`,
  `cons_macro830_null.py`, `cons_macro830_fade_ymrty.py`; outputs `out/cons_macro830_*`.
  - Data: fut_opening_globex_1m (ES/NQ) and fut_opening_globex_1m_ym_rty, sessions 2016–2023.
  - MNQ, n 186: mean +$34.88 gross, net +$30.81, median +$12.75, t 2.73, win 56%.
    - Trimmed 1%/1% +$33.87; ex-top-1% +$27.57; ex-bottom-1% +$41.19.
    - CPI +$33.6, NFP +$36.2. 2016–19 +$8.20 (2× cost) vs 2020–23 +$61.56.
    - Ex-2022 +$34.73. 7/8 years > 0.
    - Top trade 2021-12-03 +$735; bottom 2022-09-13 −$584.
  - Transfers: MES +$16.69 (t 2.18, 7/8 yrs); MYM +$10.07 (t 1.73, 7/8 yrs); M2K +$8.36 (t 1.15).
    ES has the same shape at about half the dollars.
  - Grid (K × exit, CPI and NFP separately), NQ:
    - CPI K=1 continues to 09:29 (−$28.2, t −2.75).
    - For K ≥ 3, exits 10:30–12:00 are a plateau of +$18.9 to +$40.5 (t 1.2–2.4).
    - NFP is positive in all 36 cells, peaking at K3–5 / 10:30 (+$41, t 2.5).
  - Decomposition, signed by the impulse: NQ 08:34→09:29 +$5.33 (t 0.83); 09:29→11:00 +$29.55 (t 2.47).
    Non-event days −$1.01 / −$2.31.
  - Nulls: random non-event weekdays (4,000 draws of 186): NQ p50 −$3.26, p95 +$13.41 (bootstrap SE 0.35),
    rank 1.000; ES p50 −$0.83, p95 +$8.82, rank 0.9985. Matched-|impulse|-decile null: NQ p50 −$11.79, p95 +$11.65,
    rank 0.9995; ES rank 0.996.
  - Cells looked at: about 15 per root across 6 roots, plus the 36-cell grid. K=5/11:00 sits inside a plateau,
    not on a peak.
- Frequency per year; stability: 24 events/yr (12 CPI + 12 NFP). Positive in 7/8 years on NQ, ES and YM. The dollars
  grow 2020–23 with price × vol, while 2016–19 is still about 2× cost on MNQ.
- Kill criterion for a pre-registration: on a window none of this has read (the principal's vault), MNQ primary
  (K=5, 08:34→11:00) mean gross ≤ $4.07 OR one-sided t < 1.28. Also killed if, on the in-sample re-run, the
  random-non-event-day null rank < 0.95, or ex-2022 mean < 2× cost. Report the secondary (09:29→11:00) and the MES
  transfer beside it. A pass on the secondary alone is not a pass.
- Prior (honest probability it survives a full Stage 0): 25–30%.
- Conservative's verdict / creative's rebuttal: CONSERVATIVE accepts with three reservations.
  - (i) 24 events/yr is under my own ~25/yr floor; it is not padded with FOMC, which is 2022-carried (t < 1.7).
  - (ii) K ≥ 3 only: the first 1–2 minutes of CPI continue.
  - (iii) The dollars scale with 2020–23 price × vol.
  CREATIVE attacked K-sensitivity on CPI (K1→09:29 −$29.41, n 92). The grid answered it: the plateau holds for
  K ≥ 3 and exits ≥ 10:30. The creative accepted on these terms, asking that the record carry the primary
  (08:34→11:00) and the declared secondary (09:29→11:00), the ES transfer at half the dollars, and gold's
  non-transfer. ACCEPTED by both, 2026-10-02.
- Addendum (creative, `scripts/crea_rates_tier1.py`): supporting evidence for the cash-closed mechanism.
  - The same CPI/NFP fade on Treasury futures (ZT/ZF/ZN/ZB, scaled to micro-yield dollars at about $10/bp)
    CONTINUES on every tenor:
    - ZN CPI K1 → 10:00: −$7.82 (t −2.30);
    - pooled K5 → 11:00: ZN −$1.60, ZT −$3.11, ZF −$2.75, ZB −$2.08;
    - non-event days at the same clock: about 0.
  - Where the cash venue is OPEN at 08:30 (Treasuries trade cash worldwide), the tier-1 move does not revert. Where it
    is SHUT (US equities before 09:30), it does.
  - The opening-auction mirror (09:27→09:32, faded to 11:00, `crea_open_auction.py`) does not revert either:
    ranks 0.13–0.66.
- Addendum (creative, `scripts/crea_ecb_fade.py`): the ECB decision impulse (07:45 ET, 08:15 after 2022-07; K=5;
  exit 11:00; CPI/NFP-coincident days dropped) CONTINUES on every root:
  - NQ −$16.28 (n 56, 2/8 years > 0);
  - ES −$14.29;
  - RTY −$20.48.
  Lead 1 is therefore "a US tier-1 headline in the shut cash-equity window", not "any tier-1 in that window". The
  24/yr reservation stands unrepaired.

---

LEAD 2: Post-cash-close transience: fade the 16:00–17:00 index-futures move from the 18:05 reopen to 10:00
- Mechanism (who is forced/mistaken; source): at 16:00 the constituent stocks stop trading. From then on the index
  future is the only liquid instrument for index risk, with no cash or ETF arbitrage behind it and a thin book.
  Post-close flow lands there: after-hours news, the residue of the closing auction, hedges of late fills, and
  after-hours earnings hedges. The price it sets is transient and is corrected overnight and at the next cash open.
  The same structure as Lead 1: the price is made while the cash venue is shut.
- New because (nearest prior D-number and the difference):
  - D499: off-hours big hours revert over one hour; ES +$2.12/MES, sub-cost.
  - D622: ES last-hour decline overnight, UNRESOLVED on five COVID days.
  - D762: the cash close barely reverses.
  - K7 (D470–D473) and K8 (D495–D503): the daily and overnight reversal; forward failed.
  - Difference: the trigger is the move made AFTER the cash close (16:00–17:00), held from the 18:05 reopen to
    10:00. OLS with the day return (09:30–16:00) and the afternoon move (13:00–16:00) as controls: NQ b_m −0.39
    (t −3.30), b_day +0.04 (t +1.39), b_afternoon −0.13 (t −2.24); on the q80 subset, my run gives m t 4.72 on
    the faded P&L.
  - A post-close point gives back about 3× what an afternoon point does, and the day return does not revert, so
    this is not K8.
  - The mega-cap-earnings reading was tested and REJECTED: in-season vs off-season difference t −0.05 to +1.35, and
    the beta-adjusted NQ−ES residual is weaker than the raw move.
- Instrument / clock / trigger / entry / exit: MNQ primary, MES and M2K transfers.
  - m = price at 16:59 (the 17:00 print) − price at the 16:00 print, on session S.
  - Gate: |m| ≥ trailing-250-session q80 of |m|, shifted one session.
  - Entry against m at the 18:05 print, which opens session S+1, a new trading day.
  - Exit at 10:00 of S+1, flat by 16:10.
  - Declared secondary: the same sign, 09:30→11:00 of S+1 (leg B).
  - Declared candidate second input, not primary: the closing-auction window c = 15:50→16:00.
- Predictor (pre-entry only): m and the gate threshold, both known by 17:00 of S. Entry is 18:05.
- Premise test:
  - Creative: `scripts/crea_postclose_fade.py`, `crea_postclose_season.py`, `crea_postclose_vs_day.py`,
    `crea_ah_shock.py`, `crea_postclose_legB.py`, `crea_postsettle.py`, `crea_moc_overnight.py`.
  - Conservative: `scripts/cons_postclose_check.py`. Outputs in `out/`. Data: fut_opening_globex_1m (all four
    index roots), sessions 2016–2023.
  - Leg A, exact enumerated circular time-rotation null (~1,780 offsets, SE 0):
    - NQ q80: +$24.62/MNQ, median +$8.25, t 2.31, trimmed +$24.24, ex-2022 +$13.37, ex-2020-and-2022 +$17.11;
      null p50 −$1.74, p95 +$14.12, rank 0.997.
    - NQ q90: +$44.34, rank 1.000.
    - ES q80: +$12.63/MES, ex-2020-and-2022 +$11.48, rank 0.985.
    - RTY q80: +$11.07/M2K, ex-2020-and-2022 +$10.70, rank 0.992.
    - YM q80: +$9.07/MYM, rank 0.979, but ex-2022 only +$2.37.
  - Conservative's independent run, NQ A q80, n 397 (~50/yr): +$29.36, median +$10.00, t 2.83.
    - 2017–19 +$7.55 vs 2020–23 +$49.18; ex-2020-and-2022 +$12.45.
    - Hold split: overnight 18:05→09:29 +$22.56 (ex-crisis +$3.34); 09:29→11:00 +$11.60 (ex-crisis +$13.80).
      In calm years the give-back happens at the cash open; in 2020/2022 it happens overnight.
    - ES A: +$16.92 (t 2.52), 2017–19 +$11.58, ex-2022 +$9.46.
  - Top NQ trades: 2022-01-25 +$896, 2020-03-20 +$804, 2022-03-08 +$701. Bottom: 2021-03-08 −$702,
    2022-05-04 −$681. Ex-top-1% +$15.33; trimmed +$21.59.
  - Leg B alone does not clear: NQ q80 rank 0.878; q90 rank 0.956 on a one-cell pick.
  - Placebo across cash-shut clocks (`cons_index_overnight_windows.py`): the q80 moves of 18:05–19:59,
    19:59–21:59, 21:59–02:59, 02:59–03:59, 03:59–08:29 and the whole night, faded to 10:59 with CPI/NFP days
    excluded, do not revert cleanly on any index root (t −1.03 to +1.95). The post-close hour is special.
  - COUNTER-EVIDENCE, the commodity family test, which FAILED:
    - After each commodity root's own settlement, the 16:59 − settle move CONTINUES: b_m GC +0.11, SI +0.15,
      CL +0.23, NG +0.19.
    - q80 fades lose: CL −$14.61, NG −$13.77, SI −$17.32.
    - The effect is equity-index-specific.
- Frequency per year; stability: about 50 per year per root at q80. NQ is positive in 6–7 of 7 full years; about
  half of NQ P&L is 2022; 2017–19 is 1.9× cost on MNQ and 2.6× on MES.
- Kill criterion for a pre-registration: on a slice none of this has read:
  - leg-A rotation rank < 0.95 on MNQ; OR
  - the ex-2022 mean, or the trimmed mean, < 2× round trip; OR
  - b_m (with day and afternoon controls) not negative at 2 SE.
  The decision statistic is the exact rotation rank, not the t (per-trade sd ≈ $200/MNQ).
- Prior (honest probability it survives a full Stage 0): 20%.
- Conservative's verdict / creative's rebuttal:
  - CONSERVATIVE first read C5 as the daily reversal (K8). The creative's regression refuted that: b_day ≥ 0, and an
    afternoon point gives back a third as much.
  - The mega-cap-earnings mechanism failed the conservative's residual and season tests and was WITHDRAWN by the
    creative.
  - BOTH of the conservative's stated acceptance conditions FAILED: leg B rank 0.878, and the family test failed and
    was not pre-declared. Acceptance therefore rests on leg A's exact rotation null on four roots and the per-point
    regression.
  - Riders:
    - (i) commodity family failed: the effect is equity-index-specific;
    - (ii) crisis-night tails: kill on the ex-crisis and trimmed means;
    - (iii) decide on the rotation rank, not the t;
    - (iv) nearest priors D499, D622, D762, K7, K8;
    - (v) the equity-only narrowing is post hoc, coherent with Lead 1 but not independently confirmed;
    - (vi) 2017–19 is thin on MNQ (1.9× cost);
    - (vii) overlaps Lead 1's 09:30–11:00 window on the nights before CPI/NFP. Same mechanism, different trigger:
      report ρ, do not exclude.
  - ACCEPTED by both, 2026-10-02.
  - Addendum (creative, `crea_postclose_expiry.py`, `crea_postclose_weekday.py`): the give-back is concentrated on
    NON-expiry nights.
    - Before 2022-05 the PM ES weeklies expired Mon/Wed/Fri only. NQ b_m on Tue/Thu nights −0.663 (t −4.04), against
      +0.076 on Mon/Wed/Fri.
    - By weekday, NQ: Tue −0.81, Thu −0.51; Fri +0.11, which carries a weekend hold.
    - Five weekdays and three open-interest terciles were inspected, so this is a declared candidate conditioner,
      not a finding.
  - A second failed transfer: FX after the London close (6E, 6A, 6B; 12:00→17:00 faded to the London morning),
    b_m −0.05 to +0.03 (`crea_fx_postlondon.py`).
  - Addendum (conservative), PRINCIPAL'S CLOSURE: `docs/BOOK_PROP.md` records "THE OVERNIGHT LINE CLOSED FOR THE
    PROP BOOK BY THE PRINCIPAL, 2026-09-12": "Closed for the prop book: any gate, window or size on the index
    overnight leg at micro cost."
    - (viii) Leg A holds MNQ/MES over that leg. Our defence: leg A is a SIGNED fade of the post-close move, P&L =
      −sign(m) × the overnight return, so it does not collect the long drift. Whether it falls outside the closure
      is the PRINCIPAL's decision, and the pre-registration must ask it first.
    - (ix) "Spent by this line: the 2024+ futures slice for the 18:00 → 09:00 leg on NQ and ES (both sides)."
      Amended kill:
      - confirm leg A on M2K and MYM 2024+ (unread, "every other root");
      - confirm leg B (09:30→11:00) on MNQ/MES 2024+ (the day leg, unread);
      - MNQ/MES leg A on 2024+ is reported, not decisive.
    - Mechanism source and tension: Boyarchenko, Larsen & Whelan (RFS 2023), cited in BOOK_PROP: the index overnight
      drift is compensation for closing order imbalances, concentrated at 02:00–03:00 ET, and about zero since
      2021. Lead 2's 2020–23 strength sits against their "zero since 2021" for the unconditional drift.
  - Riders (viii)–(ix) and the amended kill were AGREED by the creative.
  - Addendum (creative, mechanism evidence only, 32+ coefficients inspected): `crea_postclose_subwin.py`,
    `crea_postclose_regimes.py`, `crea_es_halt_dates.py`. The exchange moved the post-close clock twice, which is a
    natural experiment the pre-registration can declare:
    - the status schema shows ES had a daily 16:15–16:30 halt until 2021-06-25;
    - settlement moved 16:15 → 16:00 on 2020-10-26.
    The post-close hour was split into sub-windows w1 16:00–16:10, w2 16:10–16:15, w3 16:15–16:40, w4 16:40–17:00:
    - Before 2020-10-23 (settle at 16:15, with the halt), the give-back loads on the halt-reopen window w3 (NQ −1.16,
      t −2.7; RTY −1.37, t −2.4), and w1 is about 0.
    - From 2021-06-28 (settle at 16:00, no halt), w1 loads as well (NQ −0.44, t −2.1; ES −0.52, t −1.9).
    - So the transient part of the move moved when the exchange moved the settlement and the halt.
  - Amendment to rider (v) (creative, `crea_post_equity_close_cmdty.py`, `crea_post16_cmdty_null.py`). The
    commodity counter-evidence concerns the post-SETTLEMENT window (13:30 or 14:30 → 17:00), which continues. The
    16:00→17:00 hour itself, after the US EQUITY close, gives back on three of five commodity roots:
    - SIL q80 → 08:30: +$34.11, rank 0.993, but carried by 2020–22;
    - MNG q90 → 09:30: +$15.71, rank 0.985;
    - GC: weak;
    - HG: nil;
    - CL: continues (rank 0.05).
    So Lead 2's mechanism may be "the CME day's last hour after the US equity close" rather than the equity
    constituents. This was inspected across five roots and several cells; it is evidence, not a finding.

---

LEAD 3: Gold's weekend reopen: fade the Friday-close → Sunday-first-hour move on MGC into the Monday US morning
- Mechanism (who is forced/mistaken; source): gold's reference venues (LBMA London, the Shanghai Gold Exchange,
  COMEX's day session) are all shut over the weekend. The Sunday 18:00 ET reopen prices the weekend's news in the
  thinnest book of the week, during the Asian pre-open before Tokyo and Shanghai bring depth. London and New York
  re-price it by the US morning.
  - It is the weekend form of Leads 1 and 2: the price is made while the reference venues are shut.
  - It is GOLD-ONLY: no other root shows it (family test below). That weakens the general story; a gold-specific
    reason (the weekend physical/Asian bid) is plausible but unshown.
- New because (nearest prior D-number and the difference):
  - D765/D767/D770, gold's China-open fade: a later clock (21:00 ET on), first half hour only, +$3–4/MGC.
  - D758: weekend bitcoin gaps, not supported, a different market.
  - D644–D660: the gap fade on index roots.
  - Difference: the trigger is the weekend reopen (Friday 16:59 → Sunday 18:59) on gold, held to the US
    morning. The pre-registration must split the hold at 21:00 ET to separate it from D765.
- Instrument / clock / trigger / entry / exit: MGC.
  - m = close of the Sunday 18:59 bar (the 19:00 print) − close of Friday's 16:59 bar.
  - Entry against m at the 19:00 print; this is the Monday trade date, so the flat-by-16:10 rule is met.
  - Exit at the close of the Monday 10:59 bar (09:29 declared secondary).
  - Declared gated variant: |m| ≥ trailing q80, shifted.
- Predictor (pre-entry only): m, known at 19:00 Sunday.
- Premise test:
  - Conservative: `scripts/cons_reopen_gap.py`, `cons_gc_offhours.py`, `cons_weekend_reopen_scan.py`.
  - Creative: `scripts/crea_k6_attack.py`, `crea_k6_spread.py`. Outputs in `out/`.
  - Data: fut_opening_globex_1m_cl_ng_gc_si (GC 1-minute) and fut_breadth_hourly; the paid china-window bbo-1m,
    read-only, for the spread check. In-sample 2016–2023.
  - All Mondays, fade to 10:59: n 390, +$15.93/MGC, median +$8.00, t 2.31, 8/8 years > 0. Ex-2022 +$17.23;
    2016–19 +$8.01; 2020–23 +$23.61. To 09:29: +$12.88 (t 2.13, 8/8).
  - Creative's version: +$17.80. Ex-2020 +$11.56 = 1.95× RT. Year means 9.0 / 2.5 / 9.1 / 16.4 / 61.6 / 22.1 /
    8.2 / 13.2: 7/8 above cost.
  - Distribution: skew +1.97, median +$6.00, win 53.5%; ex-top-1% +$10.24, ex-bottom-1% +$22.14, trimmed +$14.55.
    Top trades: 2020-11-09 +$1,007 (the Pfizer-vaccine Monday, news), 2023-12-04 +$953 (the Sunday spike to $2,150
    and collapse), 2022-06-13 +$509.
  - Gated: q80 Mondays +$35.15 (t 2.59).
  - Exact circular rotation null (384 Monday offsets): all Mondays p50 +$0.02, p95 +$11.18, rank 1.000; q80 (prior-50-
    Monday gate) obs +$47.64, n 75, p95 +$29.26, rank 1.000.
  - Built-in placebo across clocks: of seven GC off-hours windows, only the reopen window reverts (22:59→01:59
    CONTINUES, t −2.05). Tue–Fri reopens: +$1.68 (all), +$14.00 (q80, t 1.48).
  - Entry delay does not kill it: 19:29 → +$15.82; 19:59 → +$15.62. Both halves of m carry it: the gap alone
    +$10.45, the first hour alone +$13.35.
  - Spread at the entry clock (paid bbo-1m): MGC median 2.0 ticks on Sunday 18:55–19:00 (n 99), the same as Tue–Fri
    at the same clock; touch depth 7 against 7 lots. The Sunday entry is not dearer.
  - FAMILY TEST, FAILED: on the hourly fixture across 19 roots with micros, Monday reopen → 10:00:
    - GC +$17.20 (ex-2020 +$8.41 = 1.4× RT at hourly resolution);
    - SIL −$6.19, MNG −$12.57 (t −2.47), MHG +$0.87, MCL +$5.86 (t 0.85);
    - FX, ZN and ZB about 0; MBT negative; index → 10:00 about 0.
- Frequency per year; stability: about 49 Mondays a year. All 8 years positive. 2020 is 43% of P&L, a breach of the
  conservative's 40% rule. 2017 is +$2.54, below cost.
- Kill criterion for a pre-registration: on the 2024+ GC/MGC slice (unread for this line):
  - rotation rank < 0.95; OR
  - ex-top-1% mean < 1.5× RT; OR
  - ex-2020-type crisis-Monday mean < 1.5× RT; OR
  - the 18:59 → 21:00 ET part of the hold ≤ 0 (which would make it D765's China-open reversal).
- Prior (honest probability it survives a full Stage 0): 15%.
- Conservative's verdict / creative's rebuttal:
  - Proposed by the CONSERVATIVE. The CREATIVE attacked: the A3 breach (2020 = 43%), right-tail carried, gold-only,
    the overlap with D765, multiple testing (6 roots × 8 cells, then 7 windows × 12 cells on GC). The creative
    supplied the exact rotation null, the entry-delay test and the spread check (all favourable), and accepted.
  - The CONSERVATIVE then ran the family test, which FAILED (gold-only), lowered the prior to 15%, and added the
    ex-2020 kill.
  - Reservations:
    - (a) 2020 = 43% of P&L;
    - (b) the right tail carries the mean; trimmed +$14.55;
    - (c) gold-specific; no other root transfers;
    - (d) split the hold at 21:00 ET against D765;
    - (e) multiple testing;
    - (f) the hourly ex-2020 figure is only 1.4× RT.
  - ACCEPTED by both, 2026-10-02.

---

LEAD 4: Closing-auction pressure on the Russell micro: fade the 15:50→16:00 move from the 18:05 reopen to 10:00
- Mechanism (who is forced/mistaken; source): market-on-close orders (index funds, rebalancers, benchmarked
  managers) must trade at the closing auction regardless of price. The NYSE/Nasdaq imbalance publications from
  15:50 move the futures as hedgers pre-position. That price pressure is liquidity demand, not information, and it
  reverts once liquidity returns overnight and at the next open.
  - Source: Bogousslavsky & Muravyev, "Who Trades at the Close? Implications for Price Discovery and Liquidity"
    (AEA 2021 conference paper, https://aeaweb.org/conference/2021/preliminary/paper/H9T4hef7):
    - the closing auction was 7.5% of US daily volume in 2018, against 3.1% in 2010, driven by indexing and ETFs;
    - closing prices deviate from the closing quote midpoints, and the deviations revert by half shortly after the
      close and fully overnight.
  - Capture ratio, as a sanity check (`cons_moc_capture.py`): the fade to 10:00 recovers 30% of |c| on RTY, but
    only 15–16% on ES and NQ and 10% on YM.
  - Dose: the closing auction's share of daily volume, and its impact, are largest in small caps. So the Russell
    future should give back most, and it does: rotation rank at 10:00 is RTY 0.999, NQ 0.971, ES 0.951, YM 0.867.
    The dose argument was made AFTER the four roots were seen.
- New because (nearest prior D-number and the difference):
  - D762, the cash close at 15:50→16:00 faded to 16:10: NO REVERSAL. Its top-third fade grossed RTY +$0.97,
    ES +$0.54.
  - The difference here is the horizon: hold from the 18:05 reopen to the next morning. At ten minutes there is
    nothing; overnight the auction pressure gives back.
  - Also D688 (dealer hedge flow at the close, NOT SUPPORTED), D640 (LETF close flow, killed by placebo), D685
    (month-end).
  - Distinct from Lead 2: c and m are both gated on only about a third of nights, they share a sign on 52–62% of
    those, and ρ of the daily dollar series with Lead 2 is −0.01 on RTY (−0.04 on the overlap) and 0.00–0.14 on
    ES, YM and NQ. They share a clock but diversify.
- Instrument / clock / trigger / entry / exit: M2K primary; MES and MYM declared secondary roots.
  - c = the 16:00 print − the 15:50 print (closes of the 15:59 and 15:49 bars) on session S.
  - Gate: |c| ≥ trailing-250 q80, shifted one session.
  - Entry against c at the 18:05 print (session S+1, a new trading day).
  - Exit at 10:00 of S+1 (primary); 08:29 declared secondary.
- Predictor (pre-entry only): c and its gate, known at 16:00 of S.
- Premise test:
  - Conservative: `scripts/cons_moc_standalone.py`. Creative: `crea_moc_standalone.py`, `crea_moc_overnight.py`.
    Outputs in `out/`.
  - Exact circular rotation null, about 1,780 offsets. Data: fut_opening_globex_1m_ym_rty and fut_opening_globex_1m;
    RTY from 2017-07.
  - RTY exit 10:00 (creative): n 312, +$14.75/M2K, median +$11.75, t 2.48, trimmed +$14.60, ex-top-1% +$11.39,
    ex-2022 +$19.49 (5.2× RT); rank 0.999 (p95 +$8.32).
    - Conservative's run: rank 0.991; ex-2020-and-2022 +$14.48 (3.9× RT).
    - Years: 2018 +11.0, 2019 +4.8, 2020 +27.7, 2021 +28.6, 2022 −13.3, 2023 +21.2. 5/6 positive and not
      2020-carried.
  - RTY exit 08:29: +$11.40 to +$11.43, rank 0.999 to 1.000.
  - ES exit 08:29: +$13.85/MES, t 2.04, rank 0.997, ex-2022 3.5× RT, ex-2020-and-2022 1.6×. Years 5.8 / 5.5 / 13.4 /
    −4.4 / 42.1 / −17.3 / 5.6 / 43.4.
  - YM exit 08:29: +$9.51/MYM, rank 0.991, ex-2020-and-2022 1.0×.
  - NQ fails: rank 0.918–0.920. ES, YM and NQ are carried by 2020 and 2023, with 2019 and 2021 negative.
- Frequency per year; stability: about 52 nights a year on RTY. 5 of 6 full years positive; 2022 negative.
- Kill criterion for a pre-registration: on RTY 2024+ (unread; "every other root" under the overnight-leg closure):
  - M2K rotation rank < 0.95; OR
  - ex-2022 mean < 2× RT; OR
  - the 2024+ mean ≤ 0.
  The ES and YM legs are reported, not decisive.
- Prior (honest probability it survives a full Stage 0): 15% on RTY.
- Conservative's verdict / creative's rebuttal:
  - CONSERVATIVE proposed it as a standalone fade of the creative's MOC input, with a pre-stated bar: rank ≥ 0.95 on
    two roots, ex-2022 ≥ 2× RT, ρ with Lead 2 < 0.5. All three passed, but ex-2020-and-2022 was only 1.0–1.6× RT on
    ES and YM, and the conservative called it weak (prior 12%).
  - CREATIVE repaired it around RTY, the one root not carried by 2020/2023, with the small-cap dose argument.
  - Reservations:
    - (a) RTY was chosen as primary after seeing four roots; the dose argument is post hoc;
    - (b) ES and YM are 2020/2023-carried, with 2019 and 2021 negative;
    - (c) it sits on the index overnight leg the principal closed for the prop book (2026-09-12). Lead 2's riders
      (viii)–(ix) apply: the principal must rule whether a signed fade is outside the closure. NQ/ES 2024+
      18:00→09:00 is spent, which is why RTY is the confirmation root;
    - (d) RTY data start 2017-07, so there are six years.
  - ACCEPTED by both, 2026-10-02.

---

LEAD 5 (DATA-MISSING): The measured Nasdaq closing-cross imbalance as the predictor of the MNQ overnight give-back
- **Read this first.** This lead shares Lead 4's MECHANISM; its novelty is the PREDICTOR. The pair did NOT find a fifth
  independent mechanism that meets the bar. This is the best fifth the evidence supports, accepted under the brief's
  data-missing clause (a sourced size estimate plus a free quote).
- Mechanism (who is forced/mistaken; source): market-on-close and limit-on-close orders (index funds, ETF creations,
  rebalancers) must trade in the closing cross. From 15:50 the exchange publishes the imbalance those forced orders
  create. The price pressure is liquidity demand, and it reverts.
  - Source: Bogousslavsky & Muravyev, "Who Trades at the Close?" (AEA 2021): closing-price deviations from the quote
    midpoint revert half shortly after the close and fully overnight; the closing auction was 7.5% of daily volume
    in 2018.
- New because (nearest prior D-number and the difference):
  - The nearest records are D762 (the cash close, 10-minute horizon, no reversal), D688 (dealer-hedge flow at the
    close, not supported), D640 (LETF close flow) and our own Lead 4. No repository record uses an exchange's
    published closing-cross imbalance.
  - The difference from Lead 4: Lead 4's predictor, the 15:50→16:00 futures move, mixes forced flow with information,
    and on NQ it fails (rank 0.918–0.920; capture 16%). The measured imbalance isolates the forced part, so the
    mechanism predicts a higher capture on imbalance-selected nights.
- Instrument / clock / trigger / entry / exit: MNQ primary.
  - Imbalance I = the signed dollar imbalance summed over Nasdaq-100 constituents, from the Nasdaq Net Order Imbalance
    messages; the last message at or before 15:55 ET, normalised by its trailing 60-day sd.
  - Trigger: top quintile of |I| (trailing, shifted).
  - Entry against the imbalance's direction at the 18:05 print (session S+1). Exit at 10:00 of S+1.
  - Declared transfers:
    - MES, with S&P constituents on the NYSE + Nasdaq imbalance feeds;
    - MYM, with the 30 Dow names;
    - M2K, if Russell coverage is priced.
- Predictor (pre-entry only): I at 15:55, published by the exchange in real time, so it is known before 16:00. Entry
  is at 18:05.
- Premise test: NOT run on its own data, which is not on disk.
  - Sourced size estimate (`scripts/cons_moc_capture.py`):
    - on NQ q80-|c| nights, the mean |c| (15:50→16:00) is $73.04/MNQ;
    - Lead 4's price proxy recaptures 16% on NQ ($11.7, the failed number), 30% on RTY, 15% on ES, 10% on YM;
    - if imbalance selection lifts NQ capture to 20–30%, gross ≈ $14.6–21.9/MNQ = 3.6–5.4× the $4.07 RT;
    - arithmetic audited by the creative.
  - On-disk proxy of the key assumption (creative, `scripts/crea_imb_proxy.py`, declared before running; re-run and
    VERIFIED by the conservative). Nights with calendar-known huge closing auctions (month-end, quarter-end, quad
    witching) against ordinary nights; capture = Σ fade / Σ|c|, fade 18:04→10:00:
    - all nights: NQ +0.49 (n 107, +$24.62, t 1.46) vs −0.03; RTY +0.66 vs +0.17; ES +0.18 vs +0.06; YM +0.05 vs +0.10;
    - BUT on the q80-|c| subset: NQ big 0.17 (n 39) vs ordinary 0.24 (the wrong way); RTY 0.63 vs 0.40;
      ES 0.23 vs 0.17;
    - NQ capture by |c| quintile is ≤ 0 in Q0–Q3 and +0.27 in Q4;
    - supportive on 3 of 4 roots over all nights; not established (t < 1.6, n about 100 a root).
  - Data cost, FREE metadata quotes only, nothing downloaded (`scripts/cons_imbalance_quote.py`,
    `cons_imbalance_quote2.py`):
    - Databento XNAS.ITCH `imbalance` schema, 104 approximate Nasdaq-100 names, 2018-05-01 → 2023-12-31:
      USD 105.69 (7.1 GB);
    - 2024: USD 22.73;
    - full XNAS.ITCH universe USD 10,751; full XNYS.PILLAR universe USD 1,073;
    - the history starts 2018-05.
    - The purchase needs the principal's explicit permission.
- Frequency per year; stability: about 50 nights a year at the top quintile. In-sample would be 2018-05 → 2023
  (5.7 years). Stability unknown until bought; Lead 4's NQ proxy was 2020/2023-carried.
- Kill criterion for a pre-registration, on the bought 2018-05 → 2023 data, before any 2024 read:
  - the MNQ imbalance-fade exact rotation rank < 0.95; OR
  - capture ≤ Lead 4's NQ price-proxy capture (16%) on the same nights; OR
  - ex-2020-and-2022 gross < 2× RT.
- Prior (honest probability it survives a full Stage 0): 8–10%.
- Conservative's verdict / creative's rebuttal:
  - Proposed by the CONSERVATIVE after the creative's on-disk list was exhausted.
  - The CREATIVE audited the arithmetic (correct) and ran an on-disk proxy of the key assumption (mixed, as above),
    then ACCEPTED it with riders:
    - (1) same mechanism as Lead 4; the novelty is the predictor; FINAL.md must say in its first paragraph that no
      fifth independent mechanism was found at the bar;
    - (2) not premise-tested on its own data;
    - (3) purchase needs the principal: USD 105.69 + 22.73; 5.7 years in-sample;
    - (4) the overnight-leg closure rider as for Leads 2 and 4. MNQ 2024+ overnight is spent, so the 2024 purchase
      only reports; confirmation must come from the declared M2K/MYM legs or a day-leg exit;
    - (5) report ρ with Leads 2 and 4 (shared clock).
  - The CONSERVATIVE re-ran the proxy (numbers verified) and ACCEPTS it with those riders. It is not padding only
    because it is a pre-registrable, falsifiable, priced test whose own kill clause ("capture ≤ 16%") rejects it if it
    is merely Lead 4.
  - ACCEPTED by both, 2026-10-02.
