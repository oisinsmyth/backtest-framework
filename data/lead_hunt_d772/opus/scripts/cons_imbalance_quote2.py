"""FREE metadata only: get_cost of XNAS.ITCH imbalance for an approximate Nasdaq-100 list (2023 composition, typed
from memory; an estimate of the bill, not a constituent file), 2018-05-01..2023-12-31, and the pre-reg year 2024."""
from pathlib import Path
import databento as db
key = (Path.home() / ".config" / "databento" / "key").read_text(encoding="utf-8").strip()
c = db.Historical(key)
NDX = ("AAPL MSFT AMZN NVDA META GOOGL GOOG TSLA AVGO COST PEP ADBE CSCO NFLX AMD TMUS CMCSA INTC TXN QCOM INTU AMGN "
       "HON AMAT ISRG BKNG SBUX MDLZ ADP GILD VRTX ADI LRCX REGN PANW MU SNPS KLAC CDNS PYPL MELI CSX MAR ORLY ASML "
       "ABNB CTAS MNST CHTR NXPI PDD WDAY MRVL LULU ADSK KDP FTNT PCAR ROST AEP CPRT KHC PAYX MCHP ODFL DXCM EXC "
       "IDXX AZN BIIB CRWD TEAM EA FAST VRSK CSGP XEL CTSH GEHC BKR DDOG ON CEG ANSS ZS TTD WBD DLTR GFS ILMN WBA "
       "MRNA SIRI ENPH JD LCID ALGN SGEN EBAY ZM DOCU OKTA SPLK VRSN").split()
print(len(NDX), "symbols")
for start, end in [("2018-05-01", "2024-01-01"), ("2024-01-01", "2025-01-01")]:
    kw = dict(dataset="XNAS.ITCH", schema="imbalance", start=start, end=end, symbols=NDX)
    print(start, end, f"USD {c.metadata.get_cost(**kw):,.2f}", f"bytes {c.metadata.get_billable_size(**kw):,}")
