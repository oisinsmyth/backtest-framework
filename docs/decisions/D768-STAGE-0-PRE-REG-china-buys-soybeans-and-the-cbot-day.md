# D768 STAGE 0 PRE-REGISTRATION — China's demand footprint: when USDA announces a large soybean (or corn) sale to China or unknown destinations at 09:00 ET, does the CBOT day session that opens half an hour later carry the purchase on, or has the open already priced it? (ZS and ZC prices, scored at one micro, MZS / MZC; prop book)

*2026-10-02. Prop book.*
- *The principal: "Can we take advantage of demand economies like chinas effects on markets? They should have a
  different type of footprint". They then chose "USDA China sales (Recommended)" and approved the download.*
- *Numbered D768, claimed with the documentation-review session (D767 is theirs).*
- ***Committed alone, before its runner exists.** In-sample only (≤ 2023-12-29). No price after the fixture's
  announcements has been looked at.*

## 0. The mechanism and what is on file

**A demand economy leaves a footprint a speculator does not: its purchases are reported.** China takes about 60% of
world soybean imports. A US exporter that sells 100,000 tonnes or more of one commodity to one destination in a day
must report it to USDA by 15:00 ET the next business day. USDA's Foreign Agricultural Service (FAS) publishes it the
business day after that, at **09:00 ET**. China's state and private buyers often buy through "unknown destinations".

**The clock is the test's lever.** CBOT grains trade 20:00 → 08:45 ET overnight, then **break**, then trade the day
session 09:30 → 14:20 ET. The announcement lands at 09:00, **inside the break, while the market is shut.** The
09:30 open is the first price that can carry it.
- **The question:** is the purchase fully priced at the open, or does the day session continue it (a demand shock
  absorbed slowly), or give it back (an opening overreaction)?
- **The direction comes with the news.** A purchase is demand. This is the one footprint in the line where the sign
  is known before the price moves.

**What could already price it:**
- **Rumour.** "Trade talk of Chinese buying" runs ahead of the announcement, so the overnight session may move first.
- **The two-day lag.** The sale happened one or two business days before the announcement.

The overnight move and the break gap are measured separately (§3).

**On file:**
- **Nothing on file uses export sales.** The grain records are D567 (harvest, WASDE) and the crush line (closed).
- **D765** (the China open on CME metals): China's clock is real *size* on CME metals, and it does not carry on.
- **The scheduled-event pattern** (D749/D751/D755): scheduled events give size, not direction. **This test differs:**
  the event's content has a known sign.

**The new fixture:** `data/fixtures/usda_daily_export_sales.csv` and its meta file.
- **The source:** every FAS daily export-sales announcement listed in the FAS newsroom under the Export Sales
  Reporting Program, with release dates from 2016-01-04 to 2023-12-29: 920 announcements.
- **How it was collected:**
  - **The listing:** 920 cards, read in this session's browser on fas.usda.gov, with listing pages 23–102
    deduplicated. Announcements dated 2024 or later were dropped unread.
  - **The full pages.** Each announcement whose listing text could hide a sale needed its full page: 200 pages,
    excluding four notices.
    - **82 were read in the browser,** before the site's bot protection began refusing this session; it was not
      worked around.
    - **The other 118 the principal fetched from another machine,** with their own script:
      - it honoured `robots.txt` and waited 5–7 seconds between pages;
      - all 118 were saved on the first attempt, with no 403 or 429;
      - the script and its logs are kept in `data/raw/usda/daily_sales/manual_fetch/`.
    - **Every page's text was taken from its `<main article>`** the same way.
  - **The raw cache** is `data/raw/usda/daily_sales/`.
- **Built by:** `scripts/build_usda_daily_sales.py`, which re-implements the browser parser
  `scripts/fas_daily_sales_parse.js` and **refuses to write unless the two CSVs are byte-identical.**
- **Each row:** one sale clause, with the announcement's path (its URL).
  - **Columns:** date, commodity, tonnes, destination, marketing year.
  - **Kinds:** *sale*, *cancel*, *change* (of destination), and *restated* (an earlier sale re-stated inside a
    correction or retraction, never a new sale).
- **Twelve random announcements were checked against their text by hand,** including a correction, a retraction, a
  split across marketing years and a three-sale list. All were right.
- **The release time is 09:00 ET,** per the FAS programme page. Two announcements say so in their own text: "issued at
  9:00 a.m." (FAS-ESR-088-20, FAS-ESR-089-18).

**The tradable instrument.** CME's micro grains are cash-settled at one tenth of the full contract:
- **MZS** (soybeans) and **MZC** (corn), 500 bushels;
- a tick of ½ cent a bushel, $2.50;
- listed since 2025-02-24.

**In-sample prices are the full contracts' (ZS, ZC) scaled to one micro: 1 cent a bushel = $5.00.** Positions are
intraday only. No construction holds an expiring physically delivered contract (the principal's standing ruling);
the in-sample front is asserted to be before its first notice day.

## 1. Data and quantities (fixed now)

**Prices:**
- **Source:** the front-month 1-minute bars of ZS and ZC, from the raw Databento GLBX `ohlcv-1m` archive (all
  hours), 2015-12-01 → 2023-12-29.
- **Extracted by:** the runner's `--extract`, D765's method restated:
  - the instrument-id validity windows;
  - the front as `fut_breadth_hourly`'s contract for the trade date;
  - a CME trade date that is the ET date of wall time + 6 hours;
  - **nothing dated 2024-01-01 or later decoded.**

**On trade date d, all times in ET:**
- **O** = the open of the first bar starting in [09:30, 09:35]. This is the day session's first print, and the
  entry.
- **P(14:15)** = the close of the last bar starting before 14:15, ineligible if staler than 10 minutes. This is the
  exit, before the 14:20 close.
- **P(08:45)** = the close of the last bar starting before 08:45 (the overnight session's end), ineligible if staler
  than 60 minutes.
- **P_prev** = the close of the last bar starting before 14:20 on the previous trade date, ineligible if staler than
  10 minutes.
- All four on one contract, or the quantity is void.

**The quantities:**
- **y** = (P(14:15) − O) × $5.00 per cent: the day session's move per micro;
- **g_break** = (O − P(08:45)) × $5.00: the break gap, which holds the announcement;
- **g_night** = (P(08:45) − P_prev) × $5.00: the overnight move.

**Eligible sessions:** trade dates 2016-01-04 → 2023-12-29 with O and P(14:15) valid. g_break and g_night are
reported where they are valid.

**Events:**
- **E_ZS(d) = 1** when the fixture has a row dated d of kind *sale*, commodity *soybeans*, and destination *China*
  or *unknown destinations*.
- **E_ZC(d)** is the same for *corn*.
- **The fixture date is the release date.** An announcement on a day CBOT is shut is lost; that count is reported.
- **Dropped from a cell's eligible sessions, never relabelled:**
  - **an ambiguous release day:** an announcement row for that commodity whose "WASHINGTON, \<date\>" dateline is 1–3
    days after its listing date. Both days are dropped:
    - ZS: 2016-04-14 and 04-15;
    - ZC: 2016-02-09/10/11, 04-18/19, 04-28/29 and 05-11/12.

    Larger differences are typos (a wrong year or month) and keep the listing date;
  - **a same-day retraction:** a sale withdrawn the morning it was announced (2022-07-15, corn). The day is dropped.
- *Cancel*, *change* and *restated* rows never make an event. Cancellations are reported (§3).

**The trade:** at one micro (MZS on the ZS cell, MZC on the ZC cell):
- enter at O on an event day, in G1's direction;
- exit at P(14:15).

**The cost:** $3.00 commission (the repo's declared micro convention, D468) + one micro tick ($2.50) a round trip,
the `d556_one_tick` convention. **$5.50 a round trip.** It is also reported at one extra tick ($8.00).

## 2. The gates (each cell: ZS and ZC)

| gate | what | passes when |
|---|---|---|
| **G1 direction** | A = the mean y on event sessions | A lies outside the [p2.5, p97.5] band of the **exact enumerated rotation of the event label** across the eligible sessions (offsets 1 … n−1). That gives a two-sided p, and **Holm over the two cells at 0.05**. The rotation keeps the events' seasonal clustering and count. **Direction:** long when A is above p97.5, short when below p2.5 |
| **G2 prize** | the trade in G1's direction | mean gross ≥ $5.50 with a Newey-West(5) t ≥ 2 over the event sequence |
| **G3 not one era** | the trade's net | positive in at least 5 of the 8 years; positive without its best year; no calendar month carrying more than 25% of the net |

**The readings, per cell:**

| reading | when |
|---|---|
| **NO DIRECTION** | G1 fails |
| **DIRECTION, NO PRIZE** | G1 passes; G2 fails |
| **EPISODIC** | G1 and G2 pass; G3 fails |
| **PREMISE HOLDS** | all three |

**What follows a PREMISE HOLDS:** a trading pre-registration read on the held slice (2024-01 → 2025-02, full-size
prices) and then forward on MZS / MZC, on the principal's word. The prop firm's product list is the principal's to
check.

## 3. Reported, never gating

1. **Is the sale news? (the premise behind the premise)**
   - Δg_break = mean g_break on event days − on other days, with the same rotation (its p50 / p95 and p);
   - the same for g_night (anticipation by rumour).
   - **If neither moves, the announcement is not news,** and a NO DIRECTION reading means there was nothing to
     carry.
2. **China against unknown destinations,** and tonnage at or above 500,000 t against smaller.
3. **The placebo destinations:** sales of the same commodity to named non-China destinations (Mexico, Japan and the
   rest). A demand shock specific to China should not appear there.
4. **Cancellations** of sales to China or unknown destinations: their g_break and y (expected negative; small n).
5. **The fade:**
   - ρ(g_break, y) on event days against other days;
   - the gross of trading against the gap on event days.
6. **Size:** the mean |y| on event days against other days, with the rotation.
7. **Splits:**
   - **era:** before the trade war (to 2018-07-05); the trade war (2018-07-06 → 2020-01-14); Phase One
     (2020-01-15 → 2021-12-31); 2022–23;
   - **Thursdays** (the weekly export-sales report, 08:30 ET) against other days;
   - **WASDE days** (12:00 ET; dates from `wasde_grains_su.csv`) against other days;
   - **September–November** (the US export season) against other months.
8. **Both cells together:** days with both a soybean and a corn event.
9. **The four groups** of each cell's trade, with the top trades named.
10. **The component line:** net Sharpe and Sortino at one micro, hit rate, skew, gross beside net, and ρ of the
    daily net with D737, F2 and C1.

## 4. Size and power (stated now)

*(the event counts come from the fixture; no price has been read)*

- **ZS: 493 event days** (China 288, unknown destinations 287, both 82; 24 with a sale of 500,000 t or more) of about
  2,000 sessions. There are 12 cancellation days.
- **ZC: 175 event days** (China 56, unknown 126). There are 10 cancellation days.
- **The SE:**
  - a ZS day session (09:30 → 14:15) moves about 10–15 cents (sd), or $50–75 per MZS, so the SE of A is about
    $50–75 / √493 ≈ $2.3–3.4. Clustering raises it;
  - on ZC (sd about 6–9 cents, $30–45 per MZC) it is about $30–45 / √175 ≈ $2.3–3.4.
- **The bar:** G2 needs a mean of at least $5.50 (1.1 cents a bushel) and a t of 2. That is a drift of about 1.1–1.5
  cents on event days, against an SE of about 0.5–0.7 cents. It is reachable if the open under-prices the purchase,
  and a high bar for a move the open has had half an hour to price.

## 5. The runner's assertions (each proved to raise in `--selftest`)

1. **Lag:**
   - a second implementation re-derives each session's event flag from the fixture's text with the `csv` module,
     without pandas;
   - **the break:** flags shifted to the next business day's release must raise;
   - the entry bar starts at or after 09:30 ET, after the 09:00 release.
2. **The clock and the break:**
   - 09:30 ET = 14:30 UTC in January and 13:30 UTC in July;
   - **no bar starts in (08:45, 09:30) ET** on at least 99% of sessions (the market is shut when the announcement
     lands).
3. **Sign in money:** a long gains when the price rises by one cent ($5.00), and a short loses the same.
4. **Units:** the median ZS front close lies in [700, 1,800] cents, and ZC in [300, 800].
5. **Delivery:** every front contract used is on a trade date before its first notice day.
6. **The seal:** a 2024-dated bar or fixture row raises.
7. **The rotation's offset 0** equals A.
8. **Chunk == whole:** the largest extraction file re-decoded serially equals its process result.
9. **Synthetic:**
   - a planted event-day drift passes G1;
   - noise fails it about 95% of the time;
   - **a seasonally clustered event label against a seasonal drift fails it about 95% of the time** (the rotation
     carries the clustering).

**Speed:** the extraction is a few minutes (four processes over the raw files, as in D765); the run is seconds.
**Output:** `data/stage0_d768_usda_china_sales.json`.

## 6. Predictions (Opus)

- **P1: the sale is news at the open.** On ZS, Δg_break is above its rotation p95 (P 0.7).
- **P2: NO DIRECTION on both cells** (P 0.6). The open prices the purchase, and the day session does not continue it.
- **P3: cancellation days have a negative mean g_break** (P 0.6; few events).
- **P(PREMISE HOLDS):** about 0.08 on ZS and 0.05 on ZC.
