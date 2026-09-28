# SqueezeMetrics DIX/GEX: licence note

**Source:** SqueezeMetrics' public daily DIX/GEX history (`DIX.csv`: date, price, dix, gex), 2011 onward. **Credit:
SqueezeMetrics** in anything published that uses it.

**Permission:** written, received by the principal on **2026-09-28** in reply to a request. Their Terms of Service
forbid compiling their data into a database without it. The verbatim reply is kept in the gitignored raw cache,
`data/raw/squeezemetrics/PERMISSION-2026-09-28.txt`; it is correspondence, so it is not tracked.

## The terms, as they bind this repository

| term | what it means here |
|---|---|
| private, non-commercial research; findings may inform **personal** trading | usable for research and for `docs/BOOK.md` (the personal book) |
| **not covered: use by or for a fund or firm** | **anything built on it does not go to `docs/BOOK_PROP.md` (the prop account)** unless SqueezeMetrics agrees in writing; the reply asks for details by return |
| **no redistribution, including in public repositories, of the raw data or lightly transformed versions** | **the public cut (`scripts/build_public_cut.py`) ships every tracked file**, so neither `DIX.csv` nor any per-date series derived from it may be tracked. It lives only under `data/raw/squeezemetrics/` (gitignored), and derived per-session arrays only in gitignored paths (`temp/`, or a `*gex*` / `*dix*` fixture the `.gitignore` excludes). Committed outputs carry coefficients, summary statistics and findings, never a dated gamma column |
| attribution | records that use it name SqueezeMetrics as the source |
| reasonable access | download occasionally, by hand or one request; no polling or scraping |
| as is | no warranty; it is a vendor series with a naive sign convention (dealers long calls, short puts), D661 C1 |

**What the data is:** GEX is SqueezeMetrics' dealer gamma exposure for the SPX complex. It is the series Baltussen et
al. (JFE 2021) used after 2017, and D661's source report C1 characterises it: median +$3.2bn per 1%, negative on about
10% of days.
