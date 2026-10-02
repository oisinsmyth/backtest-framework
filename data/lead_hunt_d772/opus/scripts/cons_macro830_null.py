"""Date-permutation null for K1: draw len(events) random weekdays (non-event) 4000x, fade mean at the same
construction (K=5 entry 08:34, exit 11:00). Also a matched-impulse null: draw non-event days whose |impulse|
is in the same decile as each event's (controls for 'big move' alone). In-sample <= 2023."""
import numpy as np, pandas as pd
OUT = r"C:\Users\O\AppData\Local\Temp\claude\C--Users-O-Desktop-Projects-Backtest-Framework\213bd9ea-4aa0-4cf1-925c-eefc146a3454\scratchpad\leads\opus_pair\out"
EVT = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674\data\calendar\events.csv"
SEAL = "2024-01-01"; MICRO = {"ES": 5.0, "NQ": 2.0}
ev = pd.read_csv(EVT); ev = ev[(ev.datetime_et < SEAL) & ev.event.isin(["CPI", "EMPSIT"]) & (ev.datetime_et.str[11:16] == "08:30")]
ed = set(ev.datetime_et.str[:10])
d = pd.read_parquet(f"{OUT}\\cons_globex_0800_1230.parquet"); assert d.session.max() < SEAL
rng = np.random.default_rng(7)
for root, usd in MICRO.items():
    piv = d[d.root == root].pivot_table(index="session", columns="hhmm", values="close", aggfunc="last")
    piv = piv[pd.to_datetime(piv.index).weekday < 5]
    imp = piv["08:34"] - piv["08:29"]; pnl = -np.sign(imp) * (piv["11:00"] - piv["08:34"]) * usd
    ok = pnl.notna() & (imp != 0); pnl = pnl[ok]; a = imp.abs()[ok]
    ise = pnl.index.isin(list(ed)); score = pnl[ise].mean(); n = ise.sum()
    pool = pnl[~ise].values
    nul = np.array([rng.choice(pool, n, replace=False).mean() for _ in range(4000)])
    # matched-impulse null: per event, draw a non-event day from the same |impulse| decile (deciles over all days)
    dec = pd.qcut(a.rank(method="first"), 10, labels=False); dec_e = dec[ise].values; dec_n = dec[~ise].values
    byd = {k: pool[dec_n == k] for k in range(10)}
    mn = np.array([np.mean([rng.choice(byd[k]) for k in dec_e]) for _ in range(2000)])
    bs = np.array([np.percentile(rng.choice(nul, len(nul)), 95) for _ in range(500)])
    print(f"{root}: score {score:.2f} n {n} | random-day null p50 {np.median(nul):.2f} p95 {np.percentile(nul,95):.2f} "
          f"(SE {bs.std():.2f}) rank {(nul < score).mean():.4f} | matched-|impulse| null p50 {np.median(mn):.2f} "
          f"p95 {np.percentile(mn,95):.2f} rank {(mn < score).mean():.4f}")
