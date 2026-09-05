"""Stage-0 for D333: how many events-file 'dividends' are corporate actions?
The panel adds every dividend as log1p(amount / close) with no bound. Count the
dividends by amount-to-close ratio, and the return days they create."""
import sys, json, time, importlib.util
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
spec = importlib.util.spec_from_file_location("b", REPO / "scripts" / "run_book_single_names.py")
B = importlib.util.module_from_spec(spec); sys.modules["b"] = B; spec.loader.exec_module(B)
spec = importlib.util.spec_from_file_location("rp", REPO / "scripts" / "ragged_panel.py")
RP = importlib.util.module_from_spec(spec); sys.modules["rp"] = RP; spec.loader.exec_module(RP)
t0 = time.time()
panel, _ = RP.load_ragged(B.FIXTURE, B.EVENTS, fee_bps=B.FEE_BPS)
ev = json.loads(Path(B.EVENTS).read_text())
pos = {d: i for i, d in enumerate(panel.dates)}
idx = {s: i for i, s in enumerate(panel.symbols)}
rows = []
for s, items in ev["dividends"].items():
    i = idx.get(s)
    if i is None:
        continue
    for d, amt in items:
        t = pos.get(d[:10])
        if t is None or amt <= 0 or not panel.live[i, t] or np.isnan(panel.closes[i, t]):
            continue
        prev = panel.closes[i, t - 1] if t > 0 and panel.live[i, t - 1] else np.nan
        rows.append((s, d[:10], amt, panel.closes[i, t], amt / panel.closes[i, t],
                     (panel.closes[i, t] / prev - 1) if np.isfinite(prev) else np.nan))
r = np.array([x[4] for x in rows]); pxmove = np.array([x[5] for x in rows])
print(f"{len(rows):,} dividends applied to the panel ({time.time() - t0:.0f}s)")
print("\nratio of dividend to same-day close:")
for lo, hi in ((0, 0.01), (0.01, 0.05), (0.05, 0.10), (0.10, 0.25), (0.25, 0.50), (0.50, 1.0), (1.0, 3.0), (3.0, 1e9)):
    m = (r >= lo) & (r < hi)
    if m.sum():
        print("  %5.0f%% - %-5s : %6d dividends   median price move that day %+6.1f%%   names %d"
              % (100 * lo, ("%.0f%%" % (100 * hi)) if hi < 1e8 else "inf", m.sum(),
                 100 * np.nanmedian(pxmove[m]), len({rows[j][0] for j in np.flatnonzero(m)})))
big = sorted([x for x in rows if x[4] >= 0.25], key=lambda x: -x[4])
print(f"\n{len(big)} 'dividends' of 25% of price or more, on {len({x[0] for x in big})} names. The largest 25:")
print("  %-7s %-11s %10s %9s %8s %10s" % ("symbol", "date", "amount", "close", "ratio", "px move"))
for s, d, amt, c, ratio, mv in big[:25]:
    print("  %-7s %-11s %10.3f %9.3f %7.2fx %+9.1f%%" % (s, d, amt, c, ratio, 100 * mv if np.isfinite(mv) else np.nan))
print("\nA real special dividend drops the price by about its amount on the ex-date. A spin-off or merger "
      "consideration booked as a dividend does not -- the price is already the post-transaction price.")
print(f"done ({time.time() - t0:.0f}s)")
