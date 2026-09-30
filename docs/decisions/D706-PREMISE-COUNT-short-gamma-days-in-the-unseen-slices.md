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

*One run (`8923ee98`), 214 s. D689's clean-slice count was reproduced exactly (66), and D688 was reproduced for the
in-sample composition. Output: `data/d706_vault_short_gamma_count.json`.*

| slice | sessions (with both books) | short gamma, G_SUM | share | SPX short | short by the ES book only (SPX long) |
|---|---:|---:|---:|---:|---:|
| in-sample 2016–2023 | 1,989 | 603 | 30% | 249 | 354 (59%) |
| clean 2024-01 → 2025-02 | 300 (288) | 66 | 23% | 1 | 65 (98%) |
| vault 2025-03 → 2026-09-09 | 394 (380) | **120** | 32% | 18 | 102 (85%) |

**Power** (the expected t, and the one-sided 5% pass probability, at 100% / 50% / 25% of the in-sample effect):

| component | vault alone | clean + vault (186 short-gamma days) |
|---|---|---|
| V1, net > 0 | 0.85 (0.21) / 0.43 (0.11) / 0.21 (0.08) | 1.06 (0.28) / 0.53 (0.13) / 0.27 (0.08) |
| V1 against the drift | 0.73 (0.18) / 0.37 (0.10) / 0.18 (0.07) | 0.91 (0.23) / 0.46 (0.12) / 0.23 (0.08) |
| V1, gated to D704's upper half | 0.82 (0.20) / 0.41 (0.11) / 0.20 (0.07) | 1.02 (0.27) / 0.51 (0.13) / 0.25 (0.08) |
| the 15-minute channel | 0.83 (0.21) / 0.42 (0.11) / 0.21 (0.08) | 1.03 (0.27) / 0.52 (0.13) / 0.26 (0.08) |
| V1 + channel (Stouffer) | 1.11 (0.29) / 0.55 (0.14) / 0.28 (0.09) | **1.38 (0.39)** / 0.69 (0.17) / 0.34 (0.10) |

**What it says:**
1. **The unseen slices cannot confirm the short-gamma direction line.**
   - At the full in-sample effect, even the two components combined and every unseen short-gamma day used (186),
     the pass probability is 0.39.
   - At a realistic 50% of the effect (the in-sample t's are the best of a searched line), it is 0.17 or less.
   - A test with that power spends the vault and cannot tell a real edge from none.
2. **The unseen short-gamma days are a different mix.**
   - 85% (vault) and 98% (clean) are short by the ES options book alone, with SPX long. In-sample it was 59%.
   - D692 found the ES-short, SPX-long cell the strongest in-sample, so this is not bad news for the mechanism. It
     does mean the unseen days test mostly one cell.
3. **The binding constraint is the regime's frequency, not the signals.** About 75 short-gamma days a year, and
   effects of 0.06–0.09 of the noise a trade, need about a decade of unseen data. The vault is 1.5 years.
