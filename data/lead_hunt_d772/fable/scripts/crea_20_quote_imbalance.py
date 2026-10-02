"""R2: FREE metadata quotes only (no download): the cost of Nasdaq TotalView NOII closing-cross imbalance history (XNAS.ITCH,
schema 'imbalance') for (a) ALL_SYMBOLS and (b) the 25 largest Nasdaq-100 names, 2018-05-01..2023-12-29; and of the
status/imbalance-equivalent on NYSE (XNYS.PILLAR) if available. Prints the available date range and the USD cost."""
import os
from pathlib import Path
import databento as db

key = os.environ.get("DATABENTO_API_KEY") or Path(os.path.expanduser("~/.config/databento/key")).read_text(encoding="utf-8").strip()
h = db.Historical(key)
for ds in ["XNAS.ITCH", "XNYS.PILLAR", "EQUS.MINI"]:
    try:
        rng = h.metadata.get_dataset_range(ds); print(ds, "range", rng)
        sch = h.metadata.list_schemas(ds); print("  schemas", sch)
    except Exception as e:
        print(ds, "ERR", e)
top25 = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "PEP", "COST", "ADBE", "CSCO", "NFLX", "AMD", "TMUS", "CMCSA", "INTC", "TXN", "QCOM", "HON", "AMGN", "INTU", "SBUX", "AMAT"]
for ds, syms, lab in [("XNAS.ITCH", "ALL_SYMBOLS", "all"), ("XNAS.ITCH", top25, "top25")]:
    for sch in ["imbalance"]:
        try:
            cost = h.metadata.get_cost(dataset=ds, symbols=syms, schema=sch, start="2018-05-01", end="2023-12-29")
            size = h.metadata.get_billable_size(dataset=ds, symbols=syms, schema=sch, start="2018-05-01", end="2023-12-29")
            print(ds, sch, lab, "USD", round(cost, 2), "bytes", size)
        except Exception as e:
            print(ds, sch, lab, "ERR", str(e)[:300])
# also: ES trades with block flags? CME GLBX trades for ES 2016-2023 (for the block-trade idea), and ES.OPT? skip.
try:
    cost = h.metadata.get_cost(dataset="GLBX.MDP3", symbols=["ES.FUT"], stype_in="parent", schema="trades", start="2016-01-01", end="2023-12-29")
    print("GLBX ES.FUT trades 2016-2023 USD", round(cost, 2))
except Exception as e:
    print("GLBX trades ERR", str(e)[:200])
