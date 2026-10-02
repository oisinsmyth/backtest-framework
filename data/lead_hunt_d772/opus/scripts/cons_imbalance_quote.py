"""FREE metadata only: what would the Nasdaq/NYSE closing-cross imbalance history cost? No data is downloaded.
Calls metadata.list_schemas / get_dataset_range / get_cost / get_billable_size. The key is read from the file and never printed."""
from pathlib import Path
import databento as db
key = (Path.home() / ".config" / "databento" / "key").read_text(encoding="utf-8").strip()
c = db.Historical(key)
for ds in ["XNAS.ITCH", "XNYS.PILLAR", "ARCX.PILLAR"]:
    try:
        sch = c.metadata.list_schemas(dataset=ds); rng = c.metadata.get_dataset_range(dataset=ds)
        print(ds, "schemas:", sch, "range:", rng)
    except Exception as e:
        print(ds, "ERR", type(e).__name__, str(e)[:200])
# cost of the imbalance schema, all symbols, 2018-05-01 .. 2023-12-31, and a 100-name subset proxy
for ds, start in [("XNAS.ITCH", "2018-05-01"), ("XNYS.PILLAR", "2018-05-01")]:
    for sym in ["ALL_SYMBOLS", ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "AVGO", "COST", "PEP"]]:
        try:
            kw = dict(dataset=ds, schema="imbalance", start=start, end="2024-01-01", symbols=sym)
            cost = c.metadata.get_cost(**kw); size = c.metadata.get_billable_size(**kw)
            print(ds, "imbalance", "ALL" if sym == "ALL_SYMBOLS" else f"{len(sym)} names", f"USD {cost:,.2f}", f"bytes {size:,}")
        except Exception as e:
            print(ds, "imbalance ERR", type(e).__name__, str(e)[:300])
