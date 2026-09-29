# SqueezeMetrics DIX/GEX: licence note

**Source:** SqueezeMetrics' public daily DIX/GEX history (`DIX.csv`: date, price, dix, gex), 2011 onward. **Credit:
SqueezeMetrics** in anything published that uses it.

**Permission:** written, received by the principal on **2026-09-28** in two replies. Their Terms of Service forbid
compiling their data into a database without it.
1. An automated reply that states it is the written permission.
2. A personal reply to the principal's clarification, confirming that the prop-account use is covered.

Both are verbatim in the gitignored raw cache, `data/raw/squeezemetrics/PERMISSION-2026-09-28.txt`. They are
correspondence, so they are not tracked.

## The terms, as they bind this repository

| term | what it means here |
|---|---|
| private research; findings may inform the principal's **own** trading, **including their funded prop-firm account** (second reply) | usable for research, for `docs/BOOK.md`, and for trades the principal places in the prop account |
| **personal to the principal**; not the firm or anyone there | the prop firm may benefit only from the principal's trades. It never receives the data or anything built from it |
| **don't share with the firm the data, or any datasets, research files or models built from it** (second reply) | see "The public cut" below: DIX-consuming code and outputs are research files and models built from the data |
| **no redistribution or publication, including in public repositories, of the raw data or lightly transformed versions** | neither `DIX.csv` nor any per-date series derived from it is ever tracked. `.gitignore` carries `**/*dix*` / `**/*gex*` csv and parquet guards. The raw file lives only under `data/raw/squeezemetrics/` |
| charts, summary statistics and findings in write-ups are fine (first reply) | decision records may state coefficients, statistics and findings, crediting SqueezeMetrics |
| attribution | records that use it name SqueezeMetrics as the source |
| reasonable access | download occasionally, by hand or one request; no polling or scraping |
| as is | no warranty. It is a vendor series with a naive sign convention (dealers long calls, short puts), D661 C1 |
| anything else (commercial use, a product or service, the firm's own use) is not covered | ask SqueezeMetrics first |

## The public cut: the principal's ruling (2026-09-28)

`scripts/build_public_cut.py` ships **every tracked file**: "nothing is redacted and nothing is excluded".

**The principal's ruling:** "so long as we are not publishing the data, we are only publishing the results of our
tests, that is very different". Code that reads DIX/GEX contains no data, and test results are findings, which the
first reply explicitly allows. So:
- **Tracked and published (allowed):** scripts that read DIX/GEX, and outputs holding coefficients, statistics and
  verdicts, with SqueezeMetrics credited.
- **Never tracked:** `DIX.csv`, and any per-date series derived from it (a dataset, a fixture, an output with a dated
  gamma column), because those are the data or "lightly transformed versions". The `.gitignore` guards stay, and
  runners write per-date intermediates only to gitignored paths.

This supersedes the interim rule of commit `2c1d5b3`, that DIX/GEX-consuming code was not to be committed.

**What the data is:** GEX is SqueezeMetrics' dealer gamma exposure for the SPX complex. It is the series Baltussen et
al. (JFE 2021) used after 2017. D661's source report C1 characterises it: median +$3.2bn per 1%, negative on about 10%
of days.
