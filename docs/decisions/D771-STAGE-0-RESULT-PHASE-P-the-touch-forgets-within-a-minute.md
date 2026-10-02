# D771 STAGE 0 RESULT, PHASE P — PREMISE FAILS: the size imbalance at the touch at 09:30 Beijing does not predict the mid one minute later (GC ρ +0.034, t 1.47), and the lean itself is gone within the minute

*2026-10-02. One run of `scripts/stage0_d771_china_open_queue_imbalance.py --premise` (6 seconds).*
- **The order:** the [pre-registration](D771-STAGE-0-PRE-REG-queue-imbalance-at-the-china-open.md) (`9372f6f6`) and
  its amendment A1 (`4888cf23`, the principal: "Premise test first no prices") came before the runner (`a6ecbb4a`),
  and the runner before its one run.
- **Output:** `data/stage0_d771_china_open_queue_imbalance_premise.json` (statistics only).
- **What was read:** the GC and MGC `bbo-1m` records of the paid China window, each cut at 09:31 Beijing before use.
  No `tbbo`, no D765 bar, no fade side, fill, exit or P&L, nothing after 09:31.
- **Phase 2 (the decay curve beyond 09:31, Q1 and Q2) has not run.** Under A1 it does not run after a failed premise
  unless the principal says otherwise.

## 0. Checks

- **Sessions:** GC 1,945 read on Shanghai trading days, 1,918 used, 27 with no valid quote at 09:30 or 09:31, none
  with two instruments. MGC 484 read, 476 used, 8 with no quote. Read = used + exclusions, asserted.
- **The lag audit:** an explicit-loop second implementation re-derived I(09:30), the 09:31 mid change, the valid
  snapshot count and the ten-snapshot mean on 40 sampled sessions per root; all equal.
- **Right quantity:** I(09:30) differs from I(09:29), and the size imbalance from the count imbalance; every record
  used is stamped at or before 09:31 (asserted per file).
- **The self-test:**
  - hand-built books: the imbalance, a zero side invalid, a stale quote refused;
  - a wild 09:32 record changes nothing;
  - the sign audit in money, which raised on a mirrored reader;
  - the second implementation raised on a broken I(09:30);
  - chunk = whole on 4 processes over 40 real sessions.
- **The timestamp convention (POST HOC, `scripts/d771_bbo1m_timestamp_check.py`, the same reads):** because the
  pre-registration says a failed P may mean "a field, a timestamp or a sign is wrong".
  - Every one of 30,342 GC and 7,539 MGC records (every tenth session) is stamped exactly on the minute.
  - None has its last quote change (`ts_event`) after its stamp.
  - At 09:30 the last quote change came a median **2.4 seconds** earlier on GC (10th percentile 0.3 s), 5.8 s on MGC.
  - So each record is the book as of its minute, and the 09:30 snapshot is fresh. The measurement is what it says.

## 1. P: the declared gate

| | n | ρ(I(09:30), mid(09:31) − mid(09:30)) | t | gate (ρ > 0, t ≥ 3) |
|---|---|---|---|---|
| **GC, 2016–2023** | 1,918 | **+0.034** | **1.47** | **fail** |
| MGC, 2022–2023 (reported) | 476 | +0.073 | 1.59 | |

**The reading: PREMISE FAILS.**

## 2. What phase P reported

| | GC | MGC |
|---|---|---|
| hit rate (I and the mid change agree in sign, both nonzero) | 51.6% (1,559) | 51.7% (402) |
| minutes with no mid change | 11.7% | 5.3% |
| mean mid change, top third of I / bottom third, ticks | +0.15 / +0.14 | +0.96 / −0.19 |
| ρ on order counts instead of sizes | +0.038 (t 1.64) | +0.062 (t 1.34) |
| ρ of the ten-snapshot mean (Q's unsigned form) | +0.009 (t 0.38) | −0.039 (t −0.85) |
| **persistence: ρ(I(09:29), I(09:30))** | **+0.016** (t 0.72) | +0.049 (t 1.06) |
| persistence: ρ(I(09:21), I(09:30)) | +0.021 | +0.003 |
| EDT / EST | +0.004 / +0.094 (t 2.42) | +0.128 (t 2.26) / −0.053 |
| spread at 09:30, mean (median) ticks; touch size, median | 1.62 (1); 15 contracts | 3.56 (2); 10 |

- **By year (GC):** ρ between −0.021 (2020) and +0.086 (2017); no year reaches t 1.4.
- **ρ(I_GC(09:30), I_MGC(09:30)) on 476 shared sessions: +0.014.** At the same minute, the two books that quote the
  same metal within 0.2 ticks of each other (D770) do not lean the same way.
- The EDT/EST splits point opposite ways on GC and MGC: noise.

## 3. The reading

- **Declared:** PREMISE FAILS. Phase 2 does not run.
- **Not a broken measurement:** the fields, the timestamp and the sign are checked above.
- **What the book shows at this clock:**
  1. **The lean at the touch does not survive a minute.** Its correlation with itself one minute earlier is +0.016. In
     a minute the mid moves 88% of the time on GC, so the queues the snapshot measured are mostly gone.
  2. **What it predicts one minute ahead is at most a few hundredths of a correlation** (+0.03 to +0.07), and the
     top and bottom thirds of I move the mid by the same +0.15 ticks on GC.
  3. **The two books disagree with each other** at the same minute (+0.014). The size at the touch is local queue
     noise, not a market-wide lean.
- **What this does not test:** the published effect lives in seconds and is measured on the book just before each
  trade. That form is in the paid `tbbo` (the touch sizes before every trade), but at that horizon it cannot pay a
  micro round trip, and phase P was not asked to read it.
- **For the fade:** a snapshot that forgets in a minute cannot carry information to a 15:00 exit. Q1 and Q2 would
  test a score with no premise under it.
- **The principal's question ("could we predict price from the whole order book?"):** at the minute scale on gold's
  China open, the top of the book carries almost none, and its own lean is gone within the minute. Depth beyond the
  touch is not in this data.
- **Recommendation:** close D771 without phase 2. Closing it is the principal's call. The gold China-open line (D765,
  D767, D770) stays open by the principal's word.
