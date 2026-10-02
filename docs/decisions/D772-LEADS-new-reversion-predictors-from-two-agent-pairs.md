# D772 LEADS — new reversion predictors at micro size: two debating agent pairs; five leads on two mechanisms (Opus), none at a stricter bar (Fable); the principal's three rulings

*2026-10-02. The principal:*
- *"What predicts reversion that we have already found?";*
- *"So what I read here is that if we want to predict a reversion, then we need a new type of effect? Have two
  independent fable 5.1 agents argue back and forth, I would like one to more conservative while the other is more
  creative. Allow them to do simple tests (premise tests), search the internet etc. but most of all tell them to not
  finish until they have 5 solid leads. I would like you to do the same with two opus 5.5 agents.";*
- *"No they should communicate directly not through you";*
- *"the next step is to record these leads".*

- **What this record is:** a LEADS record. **It closes nothing, admits nothing, and pre-registers nothing.**
  - Every lead below needs its own pre-registration, committed before its runner exists (R8).
  - Only the principal opens or closes an avenue (R15).
  - The numbers are the agents' quick premise tests, in-sample. Only Lead 1 was re-derived by the main session (§3).
- **The full debate records** are in [`docs/research/reversion-lead-hunt/`](../research/reversion-lead-hunt/00-index.md).
  The agents' scripts and small statistics outputs are archived in `data/lead_hunt_d772/` (§7).

## 0. The question and the method

- **The starting point.** [`docs/research/mean-reversion-inventory.md`](../research/mean-reversion-inventory.md)
  and D733–D771 show that reversion is real in many places here. What predicts it is the move's origin (forced flow),
  the market's state (quiet, long gamma), and the root and clock. But every reversal found grossed below a micro round
  trip (about \$3–6).
- **Two pairs, each one conservative and one creative agent:** Fable 5.1 and Opus 5.5.
  - The pairs worked independently and did not read each other's files.
  - Within a pair the two agents talked directly (SendMessage). The main session sent each agent only its partner's
    ID, and later a reminder of the principal's five-lead instruction.
  - The brief and protocol are in the research folder (`01-brief.md`, `02-protocol.md`).
- **Their limits:**
  - nothing dated on or after 2024-01-01 read (every script asserts it);
  - no repo writes;
  - no data purchases (free Databento metadata quotes only);
  - no reads of `data/forward/`.
- **Each pair set its own acceptance bar.**
  - Opus: the brief's bar (new, a mechanism, size above the micro cost, not rare or one-year, pre-registrable).
  - Fable: stricter. Gross at least 1.0× the cost with a reservation and still ≥ 0 at cost + 1 tick, or 1.5×
    without; **at least 50 events a year**; no year above 50% of net; trimmed mean positive; top-10 trades below 30%.

## 1. The principal's rulings (2026-10-02)

| asked | answer | effect |
|---|---|---|
| Do signed index overnight fades (Leads 2, 4, 5) fall under the 2026-09-12 closure of "any gate, window or size on the index overnight leg at micro cost"? | **"No"** | They are not closed by it. Appended to [`BOOK_PROP.md`](../BOOK_PROP.md). The spent NQ/ES 2024+ 18:00 → 09:00 slice still binds, so their confirmation must come from other roots or the day leg. |
| Buy the Nasdaq closing-cross imbalance (USD 128) for Lead 5? | **"Not now without a real pay-off"** | Lead 5 waits. A real pay-off first has to be shown, for example Lead 4 surviving its own Stage 0. |
| Is an ex-ante volatility-gated book exempt from the one-year rule? | **"It depends on how it performs the other years/does it keep a even win rate or a vol adjusted return"** | No blanket exemption. A gated book is judged on its other years: an even win rate, or a volatility-adjusted return that holds outside the high-volatility years. |
| Pre-register Lead 1 next? | **"No the next step is to record these leads."** | This record. |

## 2. The Opus pair: five leads, accepted by both agents, on two mechanisms

**Mechanism A: a price set in a futures-only book while the reference cash venue is shut is repriced when the venue
reopens** (Leads 1–3). **Mechanism B: forced closing-auction flow reverts overnight** (Leads 4–5).

**The falsifiers it passed (each could have killed it):**
- Treasuries, whose cash market is open at 08:30, continue after CPI and jobs reports.
- ECB decisions continue.
- Commodities after their own settlement continue (Globex is their main venue).
- The opening auction is not reversed.
- Other cash-shut index hours do not revert.

Lead numbers are `AGREED.md`'s. Gross dollars per ONE micro, in-sample 2016–2023, beside the micro round trip (RT).
The priors are the pair's own.

| lead | construction | gross (RT) | key evidence | main reservations | prior |
|---|---|---|---|---|---|
| **L1 — the cash open reprices a US tier-1 release** | MNQ (MES, MYM, M2K transfer). Impulse 08:29 → 08:34 on CPI and jobs-report days; fade 08:34 → 11:00 (09:29 → 11:00 declared secondary) | **+\$34.88** (\$4.07), median +\$12.75, t 2.73, n 186; MES +\$16.69, MYM +\$10.07 | random-day null rank 1.000; matched-impulse null 0.9995; plateau for entries ≥ 3 minutes after the release and exits 10:30–12:00; the give-back is 09:30–11:00; large non-release 08:30 moves continue | 24 events a year; the first 1–2 minutes of CPI continue; nothing in 2016–17 (§3); the dollars scale with 2020–23 price × volatility | 25–30% |
| **L2 — post-cash-close transience** | MNQ, MES, M2K. The 16:00 → 17:00 move in its trailing top fifth; fade from the 18:05 reopen to 10:00 | MNQ **+\$24.62** (ex-2020-and-2022 +\$17.11); MES +\$12.63; M2K +\$11.07 | exact rotation ranks 0.985–0.997; with the day controlled, a post-close point gives back about 3× an afternoon point (not K8); the window moved when CME moved its settlement time and halt (2020-10, 2021-06) | about half of NQ's profit is 2022; both of the conservative's acceptance conditions failed; NQ/ES 2024+ overnight is spent | 20% |
| **L3 — gold's weekend reopen** | MGC. Friday 16:59 → Sunday 18:59 move; fade 19:00 Sunday → 10:59 Monday | **+\$15.93** (\$5.93), t 2.31, n 390, 8 of 8 years positive | exact rotation rank 1.000; only the reopen reverts of seven gold off-hours windows; the Sunday spread equals the weekday spread (paid `bbo-1m`) | 2020 = 43% of profit; right-tail carried (trimmed +\$14.55); gold only (18 roots tried); ex-2020 only 1.4–1.95× RT; split the hold at 21:00 ET from D765 | 15% |
| **L4 — closing-auction pressure on the Russell** | M2K (MES, MYM secondary). The 15:50 → 16:00 move in its top fifth; fade 18:05 → 10:00 | **+\$14.75** (\$3.76), t 2.48, n 312; ex-2020-and-2022 +\$14.48 (3.9×) | rotation ranks 0.991–0.999; 5 of 6 years positive; ρ with L2 ≈ 0; Bogousslavsky and Muravyev (closing deviations revert overnight); D762 found nothing at 10 minutes, and the difference is the horizon | RTY chosen after seeing four roots; ES and YM 2020/2023-carried; 6 years of RTY | 15% |
| **L5 — the measured Nasdaq closing-cross imbalance (data-missing)** | MNQ. The signed dollar imbalance over Nasdaq-100 names at 15:55, top fifth; fade 18:05 → 10:00 | estimate +\$14.6–21.9 (3.6–5.4×) if capture rises from 16% to 20–30% of the \$73 closing move | an on-disk proxy (calendar-known heavy-close nights) lifts NQ capture to +0.49 against −0.03 (n 107, t 1.46), but reverses on the top-fifth subset | the same mechanism as L4 (a new predictor only); not premise-tested; **a USD 105.69 + 22.73 purchase, declined for now (§1)** | 8–10% |

- **The pair's own reading:** five leads, but two mechanisms plus one priced extension. About 35 further
  constructions were tested for a fifth mechanism and failed (§5).
- **Dissent:** the creative would rank L2 level with or above L1 (it has the most evidence). The conservative keeps
  L1 first because it was the only lead clear of the closure question and the spent slice. The closure ruling (§1)
  removes half of that argument; the spent slice remains.

## 3. The main session's check of Lead 1

`data/lead_hunt_d772/main/verify_lead1.py` (output `verify_lead1.txt`): an independent implementation from the
fixture, the event calendar and one contract per session.
- **It reproduces the pair exactly:** n 186, mean +\$34.88, median +\$12.75, t 2.73.
  - Placebo (non-release weekdays): −\$3.32 (t −0.97, n 1,824).
  - The 11:00 close agrees with the separate `fut_NQ_rth_1m` file on 186 of 186 days.
- **What the pair's summary under-weights:**
  - **By year:** 2016 −\$1.57, 2017 +\$0.35, 2018 +\$21.79, 2019 +\$11.08, 2020 +\$45.41, 2021 +\$42.91, 2022
    +\$35.85, 2023 +\$123.17. It earned nothing in 2016–17 and grows with price and volatility.
  - **Each half is borderline:** CPI t 1.94 (n 93), jobs reports t 1.91 (n 93).
  - **Lumpy:** the best trade is +\$735 (2021-12-03, about 11% of the total), the worst −\$583.50 (2022-09-13).
- **For its pre-registration:** the 2016–17 zero and the dependence on 2018+ volatility belong in the risks, and the
  principal's third ruling (judge a book on its other years, an even win rate or a volatility-adjusted return) is the
  natural test.

## 4. The Fable pair: no lead at its stricter bar

- **Both agents concur: 0 of 5 meet their bar after about 60 primary cells.** Neither padded the list.
- **The best constructions, all real in gross and all failing on year concentration at the account's cost:**

| construction | numbers | why it fails the bar | prior |
|---|---|---|---|
| **R1, the MNG post-settlement fade sized by the leveraged-fund flow (D630's own \|I\|)** | walk-forward top tercile, 60-minute hold, +\$6.05 (t 4.0), ex-2022 +\$2.55; volatility-gated (trailing-20 sd of the response ≥ \$30) +\$13.16 gross (t 4.1, n 259, median +\$14), net 2–3× the \$4 line, daily net Sharpe 1.38, max drawdown \$434 | **2022 = 74% of net; 9 of the top-10 trades are 2022**; 2023 has 2 trades | 20% as an explicitly gated book; < 5% under the one-year rule |
| **The LETF-signed post-close fade** (fade the day's direction 16:00 → 16:05) | **MES +\$3.41 (t 4.0), positive every year 2016–23**; MNQ +\$5.10 (t 3.3) | MES 0.77× cost; MNQ 2022 = 64% | 8–15% |
| **SIL post-settlement fade, volatility-gated (sd ≥ \$80)** | +\$15.51 gross (t 2.7, 47 a year), net +\$7.51 at \$8 | 2021 = 69% of net; 4 of the top-10 trades are the January 2021 silver squeeze | 10% |
| **MCL post-settlement fade signed by the trade-at-settlement (TAS) offset** | ρ −0.12/−0.16; top tercile +\$3.74 (t 2.7) against a rotation p95 of +\$1.65; the unsigned fade on the same days +\$0.09 | 0.74× cost; the proposed dealer-hedging chain is falsified | 8–10% |
| **The MNQ close fade signed by the Nasdaq closing imbalance (NOII)** | data-missing; a top-25-name quote of USD 25.97 | needs ρ ≥ 0.1 at a 10-minute horizon | ≤ 10% |

- **The pair's structural finding:**
  - Every price-path reversion they found is 0.1–0.3 sd a trade, decisive against rotation nulls and stable in ρ,
    and 2–4× too small for a \$4–8 fixed micro cost, except when the instrument's σ is 2–3× normal.
  - Every ex-ante gate that selects those days selects 2020–22. This confirms the memory that a dollar bar is a
    volatility-regime gate.

## 5. Killed, one line each (numbers in the research folder)

- **Opus pair:**
  - the EIA petroleum and gas releases, the API crude survey, ISM, FOMC alone, ECB, Treasuries after CPI/NFP;
  - post-close mega-cap earnings;
  - commodity post-settlement and the European close;
  - the 16:00–17:00 hour on commodities (kept as evidence for L2 only);
  - weekend reopens on 18 other roots; the index weekend reopen to the European open;
  - other index overnight windows, the pre-open on non-release days, the opening auction;
  - the grains overnight gap; vol-targeting close pressure;
  - the SqueezeMetrics DIX contradiction fade (rank 0.537; 2020 = 50–90%);
  - the 0DTE chase; the CL/NG option-expiry pin (prices settle nearest the open-interest strike in only 27–30%:
    repulsion, as D614/D618);
  - micro share of volume and the broker margin cut-off; CME velocity-logic pauses; the CME bitcoin basis; CTA
    trend flips; cross-asset lone movers; SHFE breaks, the LME close, the WM/R fix, post-London FX.
- **Fable pair:**
  - cross-market residuals (six pairs, ρ −0.00 to −0.04);
  - the CME-against-Binance bitcoin basis (real every year, but it lives inside the next minute: one bar of delay
    takes the top-1% fade from \$4.73 to \$0.87);
  - copper at the LME ring 2 (documented, sub-cost); index-roll days; the 6E WM/R fix (\$1.35); the EIA first
    minutes; the Tokyo fix;
  - open-interest reversal (it runs backwards); the London silver and gold auctions; **the GLD/IAU premium as the
    gold-fix flow signer (ρ 0.00)**;
  - cross-index residuals; the SHFE close; parent and micro stop-logic pauses; micro share of volume; BTIC- and
    TACO-signed close and open fades; COMEX TAS on gold and copper; the 1-second settlement overshoot; CL front
    against second month.

## 6. Data facts for the record

- **The `ohlcv-1m` archive is ALL_SYMBOLS.** It carries the TAS (CLT, NGT, GCT, SIT, HGT, PLT, BZT, HOT, RBT), BTIC
  (EST, NQT, YMT) and TACO (ESQ, NQQ) tapes for 2016–2023, which no record had read.
  - TAS signs the post-settlement reversal on CL, NG and SI at t 2.6–3.7. BTIC and TACO sign nothing (BTIC volume
    predicts size only).
- **The metals' settlement reversions died as a regime in 2022–23** (SI ρ −0.20 to −0.27 in 2016–21, +0.02 after, at
  unchanged volatility).
- **Resting entries were adverse-selected on every construction tested,** which generalises D770.
- **Free quotes, nothing bought:**
  - XNAS.ITCH imbalance for about 104 Nasdaq-100 names: USD 105.69 for 2018-05 → 2023, USD 22.73 for 2024;
  - NOII for the top 25 names, 2018–2023: USD 25.97.

## 7. Files

- **The debate records,** copied verbatim from the session scratchpad into
  [`docs/research/reversion-lead-hunt/`](../research/reversion-lead-hunt/00-index.md):
  - each pair's `FINAL` and `AGREED` files and both agents' notes;
  - the brief and the protocol.
- **The agents' premise scripts and their small statistics outputs** (under 300 KB each; the bulk bar extracts were
  not kept) are in `data/lead_hunt_d772/{opus,fable}/{scripts,out}/`.
  - They are archived as evidence, not as runners: their paths point to the session scratchpad.
  - The agents' files cite `scratchpad/leads/<pair>_pair/scripts/...`; read that as `data/lead_hunt_d772/<pair>/scripts/...`.
- **The main session's Lead 1 check** is in `data/lead_hunt_d772/main/`.

## 8. Status

- **Open as leads, none pre-registered:** L1–L4. L5 waits on a real pay-off before its purchase.
- **Fable's R1 (the MNG flow-sized fade)** is the principal's next question: how similar is it to what the vault
  already holds, and how does it perform without 2022? That is a separate piece of work after this record.
