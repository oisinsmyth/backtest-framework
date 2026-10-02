import pandas as pd, gzip, os, json
F = r"C:\Users\O\Desktop\Projects\Backtest Framework\data\fixtures"
for f in ["fut_opening_globex_1m_ho_rb_bz_hg_pl.csv.gz", "fut_opening_globex_1m_cl_ng_gc_si.csv.gz",
          "fut_btc_1m.csv.gz", "crypto_binance_15m_raw.csv.gz", "fut_breadth_hourly.csv.gz", "fut_premarket_1m.csv.gz"]:
    p = os.path.join(F, f)
    d = pd.read_csv(p, nrows=8)
    print("=====", f)
    print(d.columns.tolist())
    print(d.head(4).to_string())
m = json.load(open(os.path.join(F, "crypto_binance_15m_raw.meta.json"), encoding="utf-8"))
print(json.dumps(m)[:1500])
