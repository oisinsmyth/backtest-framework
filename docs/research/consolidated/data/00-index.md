# Data — what can be obtained, and what is broken in it

[← consolidated index](../00-INDEX.md)

> **"The plumbing outlives the leads."** Three rounds running, the data lanes returned more than the
> signal lanes beside them — because a signal lane dies on its premise number, **and a data lane has
> no premise number to die on, so what it returns is whatever is actually true about the plumbing.**

| | one line |
|---|---|
| **[01 · SEC XBRL fundamentals](01-sec-xbrl-fundamentals.md)** | the gap IS closable — **but the obvious endpoint is a silent look-ahead** |
| **[02 · filing text and timestamps](02-filing-text-and-timestamps.md)** | **four rounds, four broken fixes** for one look-ahead. The route that is not broken is named |
| **[03 · corporate actions and splits](03-corporate-actions-and-splits.md)** | three ex-date regimes, two holes, and **a second source that cannot exist** |
| **[04 · fixture and vendor defects](04-fixture-and-vendor-defects.md)** | **the highest-yield page here** — the vendor contradicts itself, and nine flavours of wrong HTTP 200 |
| **[05 · futures data sources](05-futures-data-sources.md)** | ES + NQ + RTY + YM, 15 years, for **`$30`** — and three traps |
| **[06 · purchase proposals](06-purchase-proposals.md)** | what has been costed and never bought |

---

## The five cheapest open checks, all on data we already hold

| | check | why |
|---|---|---|
| 1 | **Are the two declared ex-dividend holes empty?** (2017-09-05, 2024-05-28) | **a recomputed ex-date column cannot produce them; a published one cannot avoid them.** It tells you which kind of column you have |
| 2 | **Do the four no-trade dates exist as rows?** | 4,187 vs 4,191 — the first externally-derived arithmetic prediction about this fixture |
| 3 | **Does a held name below `$5` get ejected or carried?** | ejected = an undeclared stop-loss truncating every trade's left tail |
| 4 | **Does the fixture preserve missing sessions or forward-fill them?** | decides whether a multi-day halt is visible at all |
| 5 | **Set `adjusted=false` on the intraday endpoint** | **puts both fixtures on one corporate-action basis** — the cheapest fix for a mismatch that has already cost this programme once |

**All five are in [`../../README.md`](../../README.md) §"What is open" and none has been run.**

## Three rules this folder earns

1. **A logged block names the TOOL and the RESPONSE, never the host.** Every IBKR 403 was a
   User-Agent exclusion; WebFetch's *"corrupted PDF"* is not a block — the bytes land on disk and
   `pypdf` reads them, which converted **seven "unreadable" fetches into full readings** in one brief.
2. **When harvesting a parameterised endpoint, census a value that MUST return zero.** It costs
   nothing and it caught two fabricated harvests.
3. **A fixture's NAME is not its composition, and a status count is not a cause of death.**
   `[REPO]` [FINDINGS §60](../../../FINDINGS.md).
