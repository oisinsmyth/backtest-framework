# Audit — which fixtures still carry the flat instrument-id map, and is anything exposed?

**2026-09-13, on the principal's question after D515's CL check.** D520 found the flat
`{instrument_id: symbol}` dict ingested **229,206 bars (0.297% of 77.2M)** that belonged to other
instruments entirely, and fixed `build_fut_sessions_hourly.py`. The question here: does any **term
structure** work inherit it?

## 1. There is no term-structure study to expose

Searched `docs/decisions/` and `scripts/` for term structure, calendar spread, roll yield, contango
and backwardation. **Every hit is an incidental mention** — D409 on expiry effects, D448 on the T+0
future, D510/D511 on the *quoted* spread (bid-ask, not calendar). **No study reads the curve.** So
nothing is exposed as a study; the exposure, if any, is latent in the data layer.

## 2. Three builders are fixed, three still use a flat lookup

| builder | mapping | roots it covers |
|---|---|---|
| `build_fut_breadth_hourly.py` | **windowed** — `(iid, root, symbol, start_ns, end_ns)`, plus two guards | 36 |
| `build_fut_sessions_hourly.py` | **windowed** — fixed by D520 (`w0`/`w1`) | 9 |
| `build_fut_day5m.py` | **windowed** — imports `ids_of` from the breadth builder, and takes the front month from the breadth fixture rather than re-deriving it | index |
| `build_fut_open_interest.py` | **FLAT** — `ids[int(x)][0]`, keyed on the id alone | ES, NQ, **CL**, GC |
| `build_fut_micro_flow.py` | **FLAT** — `ids[int(x)]` | ES, MES, NQ, MNQ |
| `build_fut_index_1m.py` | **FLAT** — `ids_of` returns `instrument_id -> (root, symbol)` | four index roots |

**Only one of the three flat builders touches a contaminated root.** Of D467's bad list — CL, SR3,
BZ, ZS, ZM — the micro-flow and index-1m fixtures cover **none**; the open-interest fixture covers
**CL**. `build_fut_day5m.py` shows the fix is a one-line import, so the pattern to copy already
exists.

## 3. Empirically, CL's open-interest rows show no gross contamination

| check | result |
|---|---|
| CL days with total open interest below 20% of its median | **0 of 2,808** |
| CL total / front open interest, median | **1,997,486 / 365,660** — correct for WTI |
| CL listed contracts per day, mean | **59.4** — correct for crude's strip |

**And the one real anomaly in the fixture is a different problem.** On **2025-07-28**, ES, GC and NQ
*simultaneously* report near-zero open interest — 326, 9,158 and 82 contracts — with truncated
contract counts (9, 22, 7). A synchronised one-day dropout across three **clean** roots is a source
artefact, not an id-mapping defect, and **CL is unaffected on that date**. Any study reading this
fixture should drop 2025-07-28 or treat it as missing.

## 4. What this does and does not establish

**Does:** no *gross* contamination reaches CL's open-interest series, and no current study reads a
curve, so nothing on the record needs revisiting on these grounds.

**Does not:** rule out *small* contamination. D520's was **0.297% of bars**, and a perturbation that
size hides inside a two-million-contract total. A distributional check cannot see it.

**The decisive test is the one D520 used**: rebuild with the windowed mapping and diff the output.
For the sessions builder that diff came back **byte-identical**, which is the outcome to expect here
too, and it is the only way to know.

## 5. Recommendation

1. **Port `ids_of` to the three flat builders.** `build_fut_day5m.py` already imports it from the
   breadth builder; the same import fixes the other three. Rebuild and diff; expect byte-identical
   and record it either way.
2. **Flag 2025-07-28** in `data-available.md` as a bad session for the open-interest fixture.
3. **Do it before any curve work, not after.** A term-structure study is precisely the kind that
   reads *all* contracts rather than the volume-selected front month, which is where the flat map
   stops being harmless — the front-month rule filters the contamination out by volume, and a curve
   study has no such filter.
