# D706 PREMISE COUNT — how many short-gamma days the unseen slices hold, and whether the short-gamma direction line can ever be confirmed on them

*2026-09-30. The principal: "Count short-gamma days". The script is `scripts/count_d706_vault_short_gamma.py`. It and
this record, down to "The result", were committed before the run.*

## Why

The short-gamma direction line now holds three weak signals that point the same way:
- D699's V1, t 1.64 against the drift;
- D700's 15-minute channel, t 1.86, independent of V1 (D701);
- D704's no-aggressive-push gate on V1, about 1 SE.

None is established, and no pre-2016 sample exists: the ES options book starts 2016-01-04, and Sierra's first ES
contract is ESZ15. More in-sample tests only add multiplicity. **The question that decides the line** is whether any
unseen slice has enough short-gamma days for a test to have power.

## What this reads, on or after 2024-01-01 (the conditioner only)

**Read:**
- SqueezeMetrics GEX (`DIX.csv`: date, gex);
- the ES options open interest and prior settlements (`fut_es_options_eod.csv.gz`, D688's columns);
- the ES settlement strip (`fut_settle_strip.csv.gz`, root ES);
- the ES session calendar (`fut_index_sessions.csv.gz`: root, day, bars).

**Not read:** no ES bar, no intraday price and no return.
- The ES book's gamma needs the prior settlement prices of the future and the options (D581's Black-76 at the prior
  settlement). That is the whole of the price information read, and no statistic of it is reported.
- The script asserts that no option row outside the slice reaches the reader, and that open interest is keyed before
  10:00.

**The vault is not spent.** Nothing about the trades' outcomes is read. What the count does reveal is the vault's
gamma regime (how many short-gamma days, by month). That is a fact about its market, and it is disclosed here.

## The slices

| slice | span | note |
|---|---|---|
| clean | 2024-01-01 → 2025-02-28 | D689 counted it, and its 66 is reproduced exactly as the guard |
| vault | 2025-03-01 → 2026-09-18 | reserved for the joint run. Sessions and the options book run to 2026-09-09, so the last week is uncountable |

## Outputs

- **Per slice:** sessions, sessions with both books, short-gamma days by G_SUM, by the SPX data alone and by the ES
  book alone, the composition of the G_SUM-short days, and the count by month.
- **The same composition in-sample** (D688's panel, 2016–2023), to see whether the unseen short days are the same
  kind.
- **The power table.** Each component's per-unit signal-to-noise is its published in-sample t / √n, and its vault
  count is its in-sample rate a short-gamma day × the vault's short-gamma days. The table gives the expected t and the
  one-sided 5% pass probability at 100%, 50% and 25% of the in-sample effect:
  - V1 net > 0;
  - V1 against the drift;
  - V1 gated to D704's upper half;
  - the 15-minute channel;
  - V1 plus the channel as independent components (Stouffer).

  It is computed for the vault alone and for the clean slice plus the vault. The in-sample t's are the best of a
  searched line, so the 50% and 25% rows are the realistic ones.

## The result

*(appended after the run)*
