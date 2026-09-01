# Data acquisition proposal

**One month of Databento, one comprehensive Alpha Vantage top-up, then cancel both.**
Costed 2026-08-29 against [the twelve-lane search](00-SYNTHESIS.md).

---

## The principle

**Historical data is a stock, not a flow.** A subscription buys new bars, corrections, and things
you did not think to pull. Once 16 years are on disk they stay on disk. **So the correct shape is:
subscribe, strip-mine, cancel — and re-subscribe for a month when a study actually needs fresh
data.**

That applies to **both** providers, and it is why this is a one-off cost rather than a running one.

---

## Current footprint, measured

| | size | files |
|---|---:|---:|
| `data/fixtures` | 0.28 GB | 53 |
| `data/raw` | 0.90 GB | 11,282 |
| `.git` | 0.33 GB | 367 |
| **total project** | **~2.0 GB** | |

**The whole programme to date fits on a phone.** That is the baseline everything below is measured
against.

---

## Part 1 — Databento, one month

### Which plan, and why not the credit alone

| route | cost | what it gives |
|---|---:|---|
| **credit only, usage-based** | **$0** (of $125) | ~246 symbol-years at `ohlcv-1m`. Enough for 15 symbols x 16 years |
| **Standard, first month, credit applied** | **$74** | **All L0 schemas (1s/1m/1h/1d) across every CME dataset, 16+ years, no per-byte metering** |

**The list below is ~35 symbols x 16 years = ~560 symbol-years. Usage-based that is ~$286; under
Standard it is included.** The subscription is worth taking **precisely because** the intention is to
strip-mine it — and it additionally unlocks **1-second** bars, which usage-based would price at
~$457 for ES alone.

**Recommendation: Standard, $74 net, one month.**

### What to pull, in priority order

**Priority 1 — the prop track's open question**

| symbol | why | span |
|---|---|---|
| **ES, NQ, YM** | the venue's liquid equity index contracts | 2010-06 → now |
| **RTY** | same, but the contract only moved to CME in 2017 | 2017 → now |
| **BTC, MBT** | **a genuine Globex contract that ran the exact ES session template** | **2017-12-17 → 2026-05-28** |

That set alone re-runs [C1](../../BOOK_PROP.md) on real futures instead of a 16-of-23-hour equity
proxy — the measurement that currently rests on an assumption.

**Priority 2 — the diversified complex**

[D261](../../decisions/D261-the-index-spread-pair.md) measured effective breadth at **3.00 for a
diversified futures book against 1.17 for equity indices alone** — worth `sqrt(2.6) = 1.6x` on IR
before any new idea. **Every prop screen so far ran at 1.17.**

- **Energy:** CL, NG
- **Metals:** GC, SI, HG
- **Rates:** ZB, ZN, ZF
- **FX:** 6E, 6J, 6B

**Priority 3 — the micros, and they matter more than they look**

**MES, MNQ, M2K, MYM.**

At a $50k prop account one ES contract is ~$250k notional. **[D260](../../decisions/D260-the-vol-targeted-overnight-hold.md)
found the size that clears the 2% daily limit is 0.21x — which is not expressible in ES minis at
all.** MES is a tenth the size. **The sizing conclusion may be an artefact of contract granularity
rather than of the edge**, and only micro data can tell the difference.

**Priority 4 — completeness, since it costs nothing extra**

ZC, ZS, ZW, HE, LE, PL, PA — plus the **`definition`** schema (roll calendars, contract metadata) and
**`statistics`** (settlement prints). **`definition` is not optional**: it is what makes a correct
continuous series possible, and [the roll warning](00-SYNTHESIS.md#6-the-roll-warning) is the single
most likely way this dataset gets silently corrupted.

### Volume

`OhlcvMsg` is a fixed **56 bytes**; `1,380 min/day x 252 days = 347,760` bars per symbol-year is an
upper bound (no bar prints for a minute without a trade).

| | |
|---|---:|
| per symbol-year, raw DBN | **19.5 MB** |
| **~35 symbols x 16 years** | **~11 GB raw** |
| stored zstd-compressed | **~4 GB** |
| stored as our gzipped-CSV convention | **~7 GB** |

**If 1-second is ever pulled: 60x the bars, so ~650 GB.** Not proposed, but it is the one thing that
would change the storage answer.

### The traps, restated

1. `stype_in="continuous"` (`ES.c.0`) — **never `parent`**, which resolves to every outright *plus*
   every calendar spread.
2. `batch.submit_job`, **not** streaming — streaming re-bills on retry; batch bills once with 30
   days of free re-downloads.
3. **Confirm the unit price first** with `list_unit_prices(dataset="GLBX.MDP3")` — 30 seconds, and
   it removes the one inferred number in the whole costing.
4. **Credit expires 6 months.**

---

## Part 2 — Alpha Vantage, one comprehensive top-up before pausing

**Databento cannot replace Alpha Vantage.** Five fetchers depend on `LISTING_STATUS`, `SPLITS` and
`DIVIDENDS` — Databento is a market-data provider, not a reference-data one. Specifically it would
not give us **the delisted roster** that made D252's **35.7%-dead** universe possible, nor corporate
actions, without which [D226's +1,772% unadjusted split bar](00-SYNTHESIS.md) recurs.

**So: top it up comprehensively, then pause for the Databento month, then decide whether to resume.**

| what | why it is missing | cost |
|---|---|---|
| **Extended-hours 15m for all 57 ETFs** | [D259](../../decisions/D259-the-extended-session-and-the-overnight-interior.md) only fetched SPY/QQQ/IWM/DIA. **The existing 57-ETF fixture discarded the extended session at build time** — we already paid for those slices | **~11,400 requests, ~3 h**, ~600 MB |
| Refresh every existing fixture to current | cheap, and stops the next study starting on stale data | ~1 h |
| Wide-universe daily refresh | D245's cohort is reserved but should not go stale | ~30 min |

**Total: roughly half a day of paced fetching, ~1 GB.**

---

## Part 3 — storage

### Projected total

| | |
|---|---:|
| current project | 2.0 GB |
| CME 1-minute complex | 7 GB *(compressed)* |
| AV extended-hours top-up | 0.6 GB |
| derived fixtures, working space, headroom 2x | ~10 GB |
| **projected total** | **~20 GB** |

### What to buy

**A 1 TB portable NVMe SSD, £55–75 / $60–85.** Crucial X9, Samsung T7, or SanDisk Extreme.

**That is 50x more than the projection needs**, and it is still the right purchase — it is the
cheapest capacity point where the drive is NVMe rather than spinning, and it will never be the
constraint.

**Two specifics that matter:**

1. **NVMe, not a portable hard disk.** Fixtures are read sequentially and decompressed at load; a
   5,400 rpm USB drive would add minutes to every run. A USB 3.2 NVMe unit does 1,000+ MB/s and is
   effectively free of that cost.
2. **Put the RAW CACHE on the external drive, keep the git repo on internal storage if there is any
   room at all.** The cache is the bulk (11,282 files today, growing to ~50,000) and is read
   sequentially; git does small random I/O and is much happier on internal.

**Only go larger if tick data becomes a real requirement** — ES `trades` alone for 15 years is
~78 GB, and the full complex would be ~2.7 TB. **That is a decision to make when a study needs it,
not now**, and a 4 TB unit is ~£180 / $220 whenever that day comes.

---

## Total cost

| | |
|---|---:|
| Databento Standard, one month, credit applied | **$74** |
| Alpha Vantage | **$0 extra** — one month you are already paying for |
| 1 TB portable NVMe SSD | **~$70** |
| **total, one-off** | **~$145** |

**Recurring: nothing.** Re-subscribe for a month if and when a study needs fresh data.

---

## Sequencing

1. **Confirm the Databento unit price** (`list_unit_prices`) before spending anything.
2. **Alpha Vantage top-up first**, on the month already paid for — the extended-hours 57 is the
   real gap.
3. **Buy the drive**, move the raw cache, verify the fixtures still load.
4. **Databento month**: Priority 1 and 2 in one `batch.submit_job`, `definition` alongside.
5. **Acceptance-test the roll** against [§6 of the synthesis](00-SYNTHESIS.md) *before* any study
   reads it. Yahoo's failure mode — a spliced front month with `adjclose` a verbatim copy of
   `close` — is subtle enough that a paid vendor could share it.
6. **Cancel Databento. Decide on Alpha Vantage separately**, once the top-up is banked.
