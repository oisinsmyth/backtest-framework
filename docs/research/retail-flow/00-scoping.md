# Retail flow — scoping, 2026-09-12

*The principal opened this line: "Lets try using more auxiliary data. Lets hunt retail traders."
This is the scoping pass before any pre-registration: what retail-activity data exists, what it
costs, what the literature says it predicts, and which stage 0 fits the programme's constraints
(daily-ish frequency, intraday-closable for the prop track, one round trip a session at micro
cost, direction from OUTSIDE the instrument's own price path — D473).*

## 0. Why this is not another price-path map

Every price-level and structure map in this programme died the same way: a pure function of the
past price path, killed by a rotation that preserves the path and destroys the alignment
(PICKUP §0d2). Retail flow is the first candidate since the filing events (D446–D455) that
carries information the price path cannot: *who* traded, not *what* the price did. The filing
lines were real per trade and net zero at the crossed cost of thin names; the retail-flow data
below is concentrated in the most liquid names and in the index futures, which is the opposite
cost regime.

## 1. What the literature says retail flow predicts (peer-reviewed only)

| result | data | horizon | magnitude | sign |
|---|---|---|---|---|
| Boehmer, Jones, Zhang & Zhang, *JF* 2021, "Tracking Retail Investor Activity" | TAQ sub-penny retail identification, 2010–2015 | one week | **+10 bp** long high-imbalance minus low | **with** retail: net retail buying predicts *higher* returns |
| Barber, Huang, Odean & Schwarz, *JF* 2022, "Attention-Induced Trading and Returns" | Robintrack user counts, 2018-05 → 2020-08 | 20 days | **−4.7%** abnormal for the top-herded stocks each day | **against** retail, at the extreme of attention only |
| Welch, *JF* 2022, "The Wisdom of the Robinhood Crowd" | same Robintrack data | months | aggregate crowd portfolio earns positive alpha | with retail, in aggregate |
| Barber, Huang, Jorion, Odean & Schwarz, *JF* 2024, "A (Sub)penny for Your Thoughts" | 85,000 placed trades | — | the Boehmer algorithm identifies 35% of retail trades and mis-signs 28%; midpoint signing cuts the error to 5% | method |
| Chicago Fed WP 2023-34 / NBER w34086, "Retail Investors' Contrarian Behavior" | TAQ retail imbalance | days | retail buys losers after news; the contrarian flow *contributes to* momentum and PEAD | retail is on the wrong side around news |

Two readings, and both are testable here: **the body of retail flow is weakly informed or
neutral (+10 bp a week, with it); the extreme of retail attention is a contrarian signal (−4.7%
a month, against it).** A stage 0 has to declare which object it measures. "Trade against
retail" as a blanket rule is not what the evidence says; the repo's own YouTube extract on that
claim (`docs/youtube-lessons.md` §1) already found the video's 70% win rate was the exit's
geometry, not retail flow.

## 2. The data, ranked by fit to the programme

| # | source | what it is | span | cost | on disk | fits which book |
|---|---|---|---|---|---|---|
| **A** | **CME micro contracts** (MES, MNQ, M2K, MYM; MCL, MGC) | `tbbo` trade-and-quote for **every instrument** (sign each trade by the quote midpoint, the 2024 correction to Boehmer); `ohlcv-1m` volume since the 2019 launch | tbbo 2025-09-11 → 2026-09-10 (≈250 sessions); volume 2019 → 2026 | **$0** | **yes**, `data/raw/databento/` (job `GLBX-20260911-6DA3JPNQE3` for tbbo) | **prop**: daily, intraday, ES/NQ |
| **B** | **Robintrack** full database | hourly count of Robinhood users holding each of 8,467 tickers | 2018-05 → 2020-08 (27 months) | $0; **3.3 GB**, 8,467 CSVs, from `robintrack.net/data-download` (MIT-licensed scraper; site says the full DB is still available) | no — **download needs the principal's permission** | personal, daily equities; the Barber et al. object exactly |
| **C** | **Nasdaq Retail Trading Activity Tracker**, free top-10 table `NDAQ/RTAT10` | each day the 10 tickers with the largest share of retail dollar volume, with `activity` (share of all retail dollars) and `sentiment` (net buy−sell over the last 10 days, −100..+100); built from SIP data, ≈45% of US retail flow | **2016-01 → present, daily** | $0 with a Nasdaq Data Link account and API key — **the principal creates the account**; I cannot | not yet | personal, daily equities; a ten-year daily herding list |
| C′ | the premium full-universe table `NDAQ/RTAT` | the same two fields for 9,500+ tickers | 2016 → present | price not published on the page; sales-quoted | no | personal; the Boehmer object at scale |
| D | CFTC Commitments of Traders, non-reportable positions | small-trader net positions, weekly, 41 roots | 1986 → | $0 | no | futures, weekly — the literature finds the non-reportable coefficient ≈ 0; **low** |
| — | TAQ sub-penny retail identification | the academic standard | 2010 → | TAQ licence | no | out of reach; **A is the same construction on the futures tape** |

## 3. The recommended stage 0: **A, the micro-contract flow on the futures tape**

It is the only source that is on disk, daily, intraday-closable, on the prop instruments, and
signed. The design question is whether micro flow *is* retail, and a stage 0 must answer that
before anything is traded — [[stage-0-premise-check]].

**The object.** For each session and each clock bucket, sign every MES/MNQ trade and every ES/NQ
trade by the quote midpoint at the trade (Barber et al. 2024's correction), and form two order
imbalances: `OI_micro` and `OI_mini`. The candidate information is **the divergence**
`OI_micro − OI_mini`, not `OI_micro` alone: if micros are the E-mini scaled down, the two
imbalances move together and there is nothing to read; if the micro crowd is a different
population, the divergence is where it shows.

**Premise checks, declared before any return is read:**

1. *Is the micro population different?* Trade-size distribution (1–2 lot share), time-of-day
   profile, and the correlation of `OI_micro` with `OI_mini` within the session. If the
   within-session correlation exceeds ~0.9 the proxy is dead and the line reports that.
2. *Does micro flow behave like retail in the literature?* Retail is contrarian on the past
   week's return and buys losers after news: sign of `corr(OI_micro_t, r_{t-1})` versus
   `corr(OI_mini_t, r_{t-1})`. Same-sign, same-size = not a distinct population.
3. *The prop-firm fingerprint, which is the one mechanism specific to this crowd.* Prop
   accounts (Topstep, MyFundedFutures, Apex) must be flat by 15:10–16:10 ET and carry daily
   loss limits. A crowd positioned one way into the last hour must unwind. Test: micro net
   position built 09:30→15:00 against the signed move 15:00→16:10, and the micro *sell*
   imbalance in the last 30 minutes as a share of the day's. This is the only hypothesis on
   the list whose mechanism has a clock and a rulebook behind it.

**Nulls.** D464's exact within-session time rotation of the flow series; a common-offset family
maximum over the (instrument × bucket × horizon) cells actually declared; the difference between
sides as the family statistic (D472 §1). The 2024+ slice is irrelevant here (tbbo starts
2025-09); the reserve is the last quarter of the tbbo year, unread until a pick is declared.

**Cost of running it.** tbbo for ES/NQ/MES/MNQ is a subset of a 37 GB schema; `scripts/bench_decode_pipeline.py`
measured decompression at 254 MB/s a worker, so one pass is minutes, not hours. No fixture
exists yet for tbbo; the stage 0 builds one (per-session signed-flow buckets) and commits it
under `data/fixtures/` with the gates written down.

**What it cannot give.** 250 sessions. A cell that needs more than one round trip a session is
dead on arrival at micro cost (D473). Anything found is a **pick**, tested forward on new tape
(the subscription runs to ~2026-10-11; the tbbo pull can be extended for $0 until then).

## 4. What B and C add, and what they need from the principal

**B (Robintrack)** reproduces the one published *contrarian* retail result on our own dead-inclusive
daily fixture: the top-herded names each day, 20-day forward return, against a matched-attention
control. 27 months, 8,467 tickers against our 1,573 + 803 + 576 names. Personal book only. **Needs:
permission to download 3.3 GB (8,467 CSV files) from robintrack.net to `data/raw/robintrack/`.**

**C (RTAT10)** is the same object with ten years of history and a daily *sentiment* field, but only
the day's ten most retail-traded names. That is exactly Barber et al.'s "top of the herding
list", every day since 2016 — and every name on it is liquid, so the crossed cost that killed
the filing lines does not bind. **Needs: a Nasdaq Data Link account and API key from the
principal** (free tier; account creation is the principal's to do). C′ (full universe) is a
purchase decision once C has reported.

**D** is not proposed.

## 5. Order

1. **A**, stage 0 pre-registered next: the premise checks in §3, the three fingerprints, the
   nulls, an abandon condition (premise 1 fails → the proxy is closed in writing, no trade
   read). Nothing traded until the premise holds.
2. **C** as soon as a key exists (a ten-year daily table is a day's work to pull and a stage 0
   on the herding list is cheap).
3. **B** if the download is authorised; it is the published result's own data and the cleanest
   replication available.

*Sources read for this note: Boehmer et al. (SSRN 2822105; JF 2021); Barber et al. 2022 (JF 77(6)
3141–3190); Welch 2022 (JF 77(3) 1489–1527); Barber et al. 2024 (JF 79(4) 2403–2427); Chicago Fed
WP 2023-34 / NBER w34086; Nasdaq Data Link RTAT overview PDF (April 2021, field definitions quoted
above); robintrack.net and github.com/Ameobea/robintrack (archived 2025-02-10, MIT); the repo's own
`docs/research/Prop-Firm-080926/13-documented-intraday-effects.md` and `docs/youtube-lessons.md` §1.*
