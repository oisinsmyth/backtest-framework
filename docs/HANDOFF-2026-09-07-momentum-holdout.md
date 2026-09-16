# HANDOFF — 2026-09-07, the session that spent the programme's first holdout read

**D365 → D371.** This is a session handoff, not the programme's state file — at the time of writing,
[`PICKUP.md`](internal/PICKUP.md) (last updated 2026-09-02, D264–D284) was untouched and still
described the short-side work. It has since been brought current and now runs to 2026-09-14.

---

## 0. THE ONE-LINE STATE

**THE MOMENTUM BOOK CLEARED EVERY IN-SAMPLE CONTROL AND FAILED OUT OF SAMPLE. BOTH CONSTRUCTIONS ARE RETIRED.
THE HOLDOUT IS SPENT. THE BOOK IS UNCHANGED.**

| | |
|---|---|
| **Book** | `docs/BOOK.md`: **S1, S2 only — neither at capital.** `docs/BOOK_PROP.md`: **none.** |
| **Holdout reads spent** | **1** (D371, 2026-09-07). Programme total: **1**. |
| **Retired today** | **S6** (nine-condition gate) and **C9** (252-bar high alone) |

## 1. THE HOLDOUT LEDGER — READ THIS BEFORE ANYTHING ELSE

**`data/fixtures/us_shorts_daily_holdout.csv.gz` (803 names) HAS BEEN READ. It is spent.**

- **Do not read it again.** Re-reading after a failure is exactly what R8's one-read discipline forbids
  (*fail, search more, read again*).
- **A clean second holdout IS available.** `scripts/fetch_short_universe.py` records **5,201 eligible names
  unfetched** beyond the current slice. The permutation is deterministic — alphabetical sort, one shuffle at
  `POOL_SEED = 20260828`, mining `order[:3400]`, holdout #1 `order[3400:5100]` — so **`order[5100:]` can be cut
  without re-picking anything.** Never fetched, never scored.
- **Casualty to record:** D357 pre-registered a read for the `rsi`/`hist_L` k=40 SHORT candidate **on this same
  fixture**. Spending it on momentum means **the short candidate has lost its clean fixture** and needs the new
  slice too. That trade-off was not visible when the read was authorised.
- **The guard.** `run_d365_momentum_buffer.py` installs an audit hook refusing any path containing "holdout",
  including metadata. It is **default-deny**; an authorised process calls `V65.allow_holdout(why)`, which prints
  loudly and logs every holdout file opened. Only D371's `--dry`/`--read` call it. CPython has no
  `removeaudithook`, so this is the only way through.

## 2. WHAT HAPPENED, D365 → D371

| study | question | outcome |
|---|---|---|
| **D365** | can a momentum buffer beat the cost problem? | yes in sample: +2.59 bp/bar, Sharpe 0.417. **Turnover, not the signal, was the cost problem** |
| **D366** | does the gated version survive its nulls? | +8.09 bp/bar, Sharpe 0.887, clears all. **But GATE-ROT's median is +4.10 — half the gate is not timing** |
| **D367** | which of the nine gate conditions matter? | **six are LOGICALLY ENTAILED** by "index at a 252-bar high" and change the book *identically*. The gate is really two conditions |
| **D368** | is the gate a knife-edge? | **neither knife-edge nor curve** — only d=0 clears its own rotation, the premium wanders, capacity closes negatively |
| **D369** | are the 200-draw verdicts safe? | **no.** p95 SE 0.301 at 200 draws → 0.02–0.06 at 10,000. Trigger **164 SE, 0 of 10,000**; gate 32.9 SE; C9 alone **UNRESOLVED** on multiplicity |
| **D370** | was the top-10 removal test fair? | **no — it reversed.** Symmetric version (each draw loses *its own* ten) CLEARS at 10.3 SE. **D367 Q7 retracted** |
| **D371** | **THE HOLDOUT READ** | **FAILED 4 of 6 hurdles on both arms. Retired.** |

### D371 in numbers

| | in sample | **holdout (803 names)** |
|---|---|---|
| net PUB | +8.11 | **+3.19** bp/bar |
| Sharpe | 0.887 | **0.344** |
| annualised | +20.4% | **+8.0%** |
| max drawdown | 3,158 bp | 6,234 bp |
| names to half P&L | 12 of 515 | **2 of 255** |
| **top 1 / 5 / 10 name share** | 11 / 30 / 45% | **36 / 142 / 231%** |

**The top-5 share above 100% is the finding: everything outside the top five names loses money.** One trade
(CAR, entered 2021-04-19, held to the 252-bar cap, +19,325 bp) is **30% of all P&L**. The 1% trimmed mean per
trade is **+63.9 against a 94.8 bp round trip** — the average trade does not cover its own costs.

**Both nulls failed**, contrary to prediction: A′ at the **96.2nd percentile** (clears the conventional p95,
fails the pre-registered Bonferroni p97.5) and GATE-ROT at the **93.9th**. **The trigger is borderline, not
intact.**

**Combined 50/50 with mining** = Sharpe 0.716 vs mining's 0.911. The two disjoint universes correlate **+0.545**
— far too high for diversification to rescue it. That arm was declared *context, not evidence* before the read.

**Twelve predictions** were committed before the fixture was touched — eight mine (5 held; the load-bearing P2
falsified), four the principal's (P10, P11 held; P9 and P12 falsified).

### The partition was audited and is SOUND — D371 §6a

Random slice of one seeded permutation. Price, dollar volume, half-spread, bars per name and **the dispersion of
`mom_252_21` itself** all match within a few percent (ratios 0.94–1.08). The only difference is **size**: 704 vs
369 eligible per bar, so the book held 24.5 names in sample and **12.7** out.

**Consequence: H5 (≥10 names to half the P&L) was MIS-SPECIFIED** — an absolute count applied to books of half
the breadth. **The retirement stands on H2 and H3, which are size-neutral** (the nulls are computed on the same
universe; a per-trade trimmed mean below the round trip does not care how many names are held).

## 3. STANDING CONSTRAINTS — the principal's, and they bind

- **R15: a signal is a positive GROSS mean per trade above its nulls. Costs and confluences come later.
  ONLY THE PRINCIPAL CLOSES A RESEARCH AVENUE.**
- **No holdout read without explicit, specific authorisation.** Building and rehearsing is fine; reading is not.
- **Costs are IBKR's official costs.**
- **No subagents unless the work is genuinely parallel** — build and run sequential work directly.
- **R8**: pre-registration committed *before* the runner exists; the result committed separately.
- **Never pipe a background command through `tail`/`grep`** — the pipe buffers and progress is invisible.
  Redirect to `temp/<job>.log` and tail that.

## 4. WHAT IS OWED NEXT, RANKED

**Free, and owed — do these first:**

1. **The breadth test.** Run the mining book on a random ~803 names, matched to the holdout's size, and see
   whether H4/H5 fail there too. Separates mechanical breadth from genuine out-of-sample decay, and answers
   whether this construction is runnable at all below ~25 held names. **In-sample, no data cost.**
2. **Make the hurdles breadth-relative** — H5 as a share of names held, not a flat count. **Precondition for any
   future read.**

**Costs data — only when a candidate deserves it:**

3. **Decide whether the trigger alone warrants a test.** A′ at the 96.2nd percentile is genuinely undecided. The
   honest successor is a *simpler* construction — no gate, wider selection, more names held — designed from
   **in-sample reasoning only** and pre-registered before anything is fetched.
4. **Cut holdout #2** from `order[5100:]` (1,700 names → ~800 after the screen). Costs Alpha Vantage budget and
   time, not statistical purity.
5. **The short side** (`hist_L` k=40, D357) also needs the new slice.

**Longer-standing, untouched:** D336's quoted-spread pull (needs the principal's TWS session — every net number
is still a PB/PUB pair); the winners'-dip long from D359 (+160/trade, no nulls run); sizing for any momentum
sleeve.

## 5. TRAPS FOUND THIS SESSION — all cost real time

- **`_m_start_of` took the bar after the LAST undefined market bar.** Correct only when every gap is a warm-up
  prefix. The holdout has 3 interior holiday bars → `m_start` 4,125 of 4,190, **a 65-bar sample with every check
  green**. Fixed (`ce2947c`); mining is a verified no-op at 63.
- **`d348_prep` hard-asserted the MINING fixture's F0 count and floor share.** Now fixture-aware via
  `PREP.EXPECT`, and printed as **"regression lock, not an independent check"** on any re-pointed fixture.
- **The holdout score cache never contained `mom_252_21`.** D357 built families A/B/E/F only. Family G is now
  built in-process by `scripts/d371_build_holdout_scores.py`, verified **bit-identical to the 8-worker fan** on
  the mining fixture first.
- **`V58.pct_of` memoises by score NAME only** — a process touching both fixtures gets the **wrong percentile
  grid** for the second. Clear `V58._PCT` between re-points.
- **`np.savez` appends `.npz`** unless the name already ends in it (`.npz.tmp` → `.npz.tmp.npz`); **`np.load`
  returns a lazy handle** Windows will not let you replace until closed.
- **Backticks in `git commit -m` are command substitution** — they ate an expression from a commit body. Use
  `-F <file>`.
- **A one-shot measurement must persist its result BEFORE it renders it.** D371's first execution computed the
  evidence then lost the JSON to a `KeyError` in the print loop, and the console had printed only each hurdle's
  boolean rather than the null distributions, so the loss was total. Recovered only because the per-draw seeds
  are deterministic.

## 6. WHERE TO READ

- **How to work here:** `CLAUDE.md` · **rules:** `docs/RULES.md` (R8, R14 + amendment, R15)
- **Truth:** `docs/FINDINGS.md` **§§46–51**
- **Where the programme stands:** `docs/STACK.md` **§§32–42, 40a, and §0**; §7 lists what earlier versions of
  that document got wrong
- **This session's records:** `docs/decisions/D366…D371*` — each has a PRE-REGISTRATION and a RESULT; D371
  carries the twelve predictions and the partition audit as §6a
- **The read itself:** `data/d371_read.json` · construction frozen in `data/d371_construction.json`

## 7. THE LESSON THAT OUTRANKS THE RESULT

**In-sample null strength does not forecast out-of-sample survival.** This construction cleared its time rotation
at **164 standard errors with zero of 10,000 draws beating it**, cleared a best-of-ten multiplicity control, and
cleared a symmetric winner-removal test. **It still failed.** Permutation nulls test whether a pattern is real
*in the data you have*; they say nothing about whether it recurs.

Three studies went into making the in-sample verdicts precise (D369) and unbiased (D370). Both were necessary.
Neither was sufficient.
