"""Cached per-root Globex 1-minute panels (root, day, et, contract, open, high, low, close, volume), 2016-2023, from the
repo's fixtures (ES NQ YM RTY CL NG GC SI HG HO RB BZ PL) or from crea_02's decode (6J 6A 6E MES MNQ MGC). SEAL asserted."""
from pathlib import Path
import pandas as pd

FIX = Path(r"C:/Users/O/Desktop/Projects/Backtest Framework/data/fixtures")
OUT = Path(__file__).resolve().parents[1] / "out"
SRC = {"ES": "fut_opening_globex_1m.csv.gz", "NQ": "fut_opening_globex_1m.csv.gz",
       "YM": "fut_opening_globex_1m_ym_rty.csv.gz", "RTY": "fut_opening_globex_1m_ym_rty.csv.gz",
       "CL": "fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "NG": "fut_opening_globex_1m_cl_ng_gc_si.csv.gz",
       "GC": "fut_opening_globex_1m_cl_ng_gc_si.csv.gz", "SI": "fut_opening_globex_1m_cl_ng_gc_si.csv.gz",
       "HG": "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "HO": "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz",
       "RB": "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "BZ": "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz",
       "PL": "fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz"}


def panel(root: str) -> pd.DataFrame:
    cache = OUT / f"crea_panel_{root}.parquet"
    if cache.exists():
        return pd.read_parquet(cache)
    if root in SRC:
        chunks = []
        for ch in pd.read_csv(FIX / SRC[root], usecols=["root", "session", "et", "contract", "open", "high", "low", "close", "volume"], chunksize=2_000_000):
            ch = ch[(ch["root"] == root) & (ch["session"] >= "2016-01-01") & (ch["session"] <= "2023-12-31")]
            chunks.append(ch)
        d = pd.concat(chunks, ignore_index=True).rename(columns={"session": "day"})
        d["et"] = pd.to_datetime(d["et"])
        d = d[(d["et"] >= "2015-12-31") & (d["et"] < "2024-01-01")]
    else:
        d = pd.read_parquet(OUT / f"crea_globex1m_{root}.parquet")
        d["et"] = pd.to_datetime(d["et"])
    assert d["et"].max() < pd.Timestamp("2024-01-01"), "SEAL"
    d = d.sort_values("et").drop_duplicates("et").reset_index(drop=True)
    d.to_parquet(cache, index=False)
    return d
