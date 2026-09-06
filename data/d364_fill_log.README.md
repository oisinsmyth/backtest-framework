# d364_fill_log

**A measurement instrument, not a trading system.** It records fills the principal obtained by
placing orders themselves; Claude places none and this file authorises none. **Nothing here is a
book entry** ([R8](../docs/RULES.md#r8) needs a pre-registered out-of-sample test, which a fill log
is not), and nothing measured from it promotes anything.

**One row is one fill, not one order.** A partial fill is one row per fill, all sharing the same
`date` / `symbol` / `side` / `intended_print`, with `shares` the quantity *of that fill*.

**`fill_price` minus the day's official print, in bp, is the number the whole exercise exists to
produce.** Every cost line here charges a *modelled* half-spread (D363's PUB / PB, inferred from the
OHLC) against a print taken from the daily fixture. Nothing has ever measured the distance between
that print and a price actually obtainable. This log is the only input that can.

**`intended_print` is not renegotiable after the fact.** An MOO fill is scored against the day's
**open**, an MOC against the **close**. Scoring an MOO against the close manufactures a slippage
number out of the day's drift. Order placed intraday against neither auction: say so in `note`.

**`fill_time` distinguishes an auction fill from a continuous one.** An MOO/MOC that really printed
in the auction carries the auction stamp (09:30:00 / 16:00:00 ET); one stamped 09:31:47 was a
continuous fill wearing the same order type — a different measurement. Blank only if the broker did
not report it, and say so in `note`.

## Columns

| column | type | meaning |
|---|---|---|
| `date` | `YYYY-MM-DD` | the **bar the order belongs to** — the fixture session the print is taken from, exchange-local |
| `symbol` | string | the fixture's ticker, exactly as in `data/d361_trades_gap_up_fade.csv`; case-sensitive |
| `side` | `short_entry` \| `cover_exit` | sells to open / buys to close. No other value |
| `intended_print` | `open` \| `close` | the official print this fill is measured against |
| `order_type` | `MOO` \| `MOC` \| `LMT` \| `MKT` | as sent |
| `shares` | positive int | the quantity **of this fill**, positive on both sides |
| `limit_price` | float > 0, blank unless `LMT` | the limit as sent |
| `fill_price` | float > 0, required | executed price per share, **as traded** (no split or dividend adjustment) |
| `fill_time` | `HH:MM:SS` US/Eastern, blank if unknown | see above |
| `venue` | string | exchange / MIC / route as reported (`XNAS`, `ARCA`, `IBKR-SMART`); blank if unreported |
| `commission_usd` | float >= 0 | all-in commission and fees **for this fill**, USD. `0` is genuinely zero; blank is unknown — they are reported separately |
| `note` | free text | partial-fill sequence, a halt, a cancel/replace, a non-USD currency. Quote any comma |

Floats plainly (`11.39`), not the repr form the machine-written exports use. Blank means "not
applicable or not known" and never means zero.

**Input to [`scripts/d364_slippage.py`](../scripts/d364_slippage.py)**, which joins each row to the
fixture's own open and close for the same `(symbol, date)` in the as-traded frame. Its convention,
printed on every run: **positive = the fill was worse for the strategy** — a short entry filled
*below* the open, a cover filled *above* the close.

**Committed with a header row and no data rows.** That is the honest state until orders are placed;
the script prints the schema, says so, and exits 0.
