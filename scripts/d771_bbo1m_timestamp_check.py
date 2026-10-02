"""D771, POST HOC (after phase P's run): the bbo-1m timestamp convention, from the bbo-1m records stamped up to 09:31 Beijing only (amendment A1's reads).
If each record is the book AS OF ts_recv (the interval's end), ts_event (the last quote change) is never after ts_recv.
If it were stamped at the interval's start with the end-of-interval book, ts_event would often exceed ts_recv."""
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d770_china_open_flow_passive as D  # noqa: E402
import stage0_d771_china_open_queue_imbalance as Q  # noqa: E402

for root in ("GC", "MGC"):
    days = Q.days_of(root)[::10]
    n = after = on_min = 0
    lag_s = []
    for d in days:
        a = D.read(root, "bbo-1m", d)
        if a is None:
            continue
        a = a[a["ts_recv"].astype(np.int64) <= D.bj_ns(d, "09:31")]
        tr, te = a["ts_recv"].astype(np.int64), a["ts_event"].astype(np.int64)
        n += len(a)
        after += int((te > tr).sum())
        on_min += int((tr % 60_000_000_000 == 0).sum())
        i = int(np.searchsorted(tr, D.bj_ns(d, "09:30"), side="right")) - 1
        lag_s.append((tr[i] - te[i]) / 1e9)
    print(root, "records", n, "ts_event > ts_recv:", after, "ts_recv on the minute:", on_min,
          "| 09:30 record: seconds since the last quote change, median",
          round(float(np.median(lag_s)), 2), "p10", round(float(np.percentile(lag_s, 10)), 2))
