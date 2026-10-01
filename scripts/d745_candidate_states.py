"""D745 withdrawal evidence (POST HOC, in-sample <= 2023-12-29 only): after the rehearsal showed D745's declared state
(shock recency) does not reproduce the in-sample pattern, the principal chose to amend to a state that does. This
searches the open-known candidates on the same books, panel and units as the scorer
(scripts/vault_d745_abstention_principle.py: in_sample_books, panel_state, WIN_IN, y = net / sigma$):

  vol_level   : walk-forward percentile (prior 250 panel sessions) of sigma_oc / open
  compress    : walk-forward percentile of prior-5 RMS(open->close) / prior-20 RMS (sigma_oc)
  since_shock : sessions since the last shock, 1-5 / 6-20 / none (checked equal to D745's recency state)
  recency     : D745's FRESH / OLD / NONE

For each book: by tercile, n, mean y, mean $ net. For the one candidate that orders C1 and F2 the same way (compress):
the per-year lo-minus-hi y, and the exact circular rotation of the tercile labels over each book's own window
sessions (pooled C1 + F2 at a shared offset k, each book shifted by k mod its own length, as D745's P2).
A trade on a session the panel drops (a roll day) has no state and is counted, not scored.

    uv run --no-sync python scripts/d745_candidate_states.py        # writes data/d745_candidate_states.json once
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
import stage0_d727_trend_curve as T7  # noqa: E402
import vault_d745_abstention_principle as D  # noqa: E402

OUT = REPO / "data" / "d745_candidate_states.json"
LABELS = ("lo", "mid", "hi")


def wf_pct(x: np.ndarray, n: int = 250) -> np.ndarray:
    """Share of the previous n values strictly below today's; NaN until n priors exist."""
    return pd.Series(x).rolling(n + 1, min_periods=n + 1).apply(lambda w: (w[:-1] < w[-1]).mean(), raw=True).to_numpy()


def tercile(p: np.ndarray) -> np.ndarray:
    return np.where(np.isnan(p), -1, np.where(p < 1 / 3, 0, np.where(p < 2 / 3, 1, 2)))


def cells(t: pd.DataFrame, lab: np.ndarray, names) -> dict:
    out = {}
    for k, nm in enumerate(names):
        g = t[lab == k]
        out[nm] = {"n": int(len(g)), "mean_y": float(g["y"].mean()) if len(g) else None,
                   "mean_usd": float(g["net"].mean()) if len(g) else None}
    return out


def main() -> int:
    if OUT.exists():
        print(f"{OUT.name} exists: run-once")
        return 1
    t0 = time.time()
    b = D.in_sample_books()
    pn = T7.panel_from_raw("NQ", b["rows"])
    st, soc, _ = D.panel_state(b["rows"])
    days = np.asarray(pn["days"], str)
    assert max(days) <= D.IN_HI, "in-sample only"
    oc = pn["C"][:, -1] - pn["O"]
    s5 = np.sqrt(pd.Series(oc * oc).shift(1).rolling(5, min_periods=5).mean().to_numpy())
    feats = {"vol_level": tercile(wf_pct(pn["soc"] / pn["O"])), "compress": tercile(wf_pct(s5 / pn["soc"]))}
    shock = st["shock"].to_numpy()
    since = np.full(len(days), 21)
    last = None
    for i in range(len(days)):
        since[i] = min(i - last, 21) if last is not None else 21     # sessions since the last shock strictly before i
        if shock[i]:
            last = i
    feats["since_shock"] = np.where(since <= 5, 0, np.where(since <= 20, 1, 2))
    rec = st["state"].to_numpy()
    feats["recency"] = np.select([rec == "FRESH", rec == "OLD", rec == "NONE"], [0, 1, 2], -1)
    names = {"vol_level": LABELS, "compress": LABELS, "since_shock": ("1-5", "6-20", "none"),
             "recency": ("FRESH", "OLD", "NONE")}
    pos = {d: i for i, d in enumerate(days)}

    books, res = {}, {"books": {}}
    for nm, tr in b["books"].items():
        lo, hi = D.WIN_IN[nm]
        t = tr[(tr["session"] >= lo) & (tr["session"] <= hi)].copy()
        t["y"] = t["net"] / (soc.reindex(t["session"]).to_numpy() * D.USD)
        t["i"] = t["session"].map(pos)
        dropped = int(t["i"].isna().sum())
        t = t[t["i"].notna()].copy()
        t["i"] = t["i"].astype(int)
        wi = np.where((days >= lo) & (days <= hi))[0]
        books[nm] = (t, wi)
        r = {"trades": int(len(tr[(tr["session"] >= lo) & (tr["session"] <= hi)])), "on_dropped_sessions": dropped,
             "window": [lo, hi]}
        for f, arr in feats.items():
            r[f] = cells(t, arr[t["i"].to_numpy()], names[f])
        # since_shock and recency are one split on the books' sessions (recency's NA = no 250-session history yet)
        ss, rc = feats["since_shock"][t["i"]], feats["recency"][t["i"]]
        ok = rc >= 0
        r["since_shock_equals_recency"] = bool(np.array_equal(ss[ok], np.select([rc[ok] == 0, rc[ok] == 1], [0, 1], 2)))
        res["books"][nm] = r

    lab_c = feats["compress"]

    def lohi(nm: str, k: int) -> tuple[np.ndarray, np.ndarray]:
        t, wi = books[nm]
        m = np.full(len(days), -1)
        m[wi] = np.roll(lab_c[wi], k % len(wi))
        L = m[t["i"].to_numpy()]
        y = t["y"].to_numpy()
        return y[L == 0], y[L == 2]

    def d(nms, k):
        a = np.concatenate([lohi(n, k)[0] for n in nms])
        c = np.concatenate([lohi(n, k)[1] for n in nms])
        return float(a.mean() - c.mean())

    comp = {}
    for nm in books:
        t, wi = books[nm]
        lab = lab_c[t["i"].to_numpy()]
        yr = t["session"].str[:4].to_numpy()
        per = {}
        for y_ in sorted(set(yr)):
            a, c = t["y"].to_numpy()[(yr == y_) & (lab == 0)], t["y"].to_numpy()[(yr == y_) & (lab == 2)]
            per[y_] = {"n_lo": int(len(a)), "n_hi": int(len(c)),
                       "lo_minus_hi_y": float(a.mean() - c.mean()) if len(a) and len(c) else None}
        null = np.array([d([nm], k) for k in range(len(wi))])
        obs = d([nm], 0)
        assert obs == null[0]
        comp[nm] = {"lo_minus_hi_y": obs, "offsets": int(len(wi)), "p_high": float(np.mean(null >= obs)),
                    "null_p50": float(np.percentile(null, 50)), "null_p95": float(np.percentile(null, 95)), "by_year": per,
                    "years_positive": int(sum(1 for v in per.values() if v["lo_minus_hi_y"] is not None and v["lo_minus_hi_y"] > 0)),
                    "years_scored": int(sum(1 for v in per.values() if v["lo_minus_hi_y"] is not None))}
    K = max(len(wi) for _, wi in (books[n] for n in D.CONT))
    null = np.array([d(D.CONT, k) for k in range(K)])
    obs = d(D.CONT, 0)
    comp["pooled_C1_F2"] = {"lo_minus_hi_y": obs, "offsets": int(K), "p_high": float(np.mean(null >= obs)),
                            "null_p50": float(np.percentile(null, 50)), "null_p95": float(np.percentile(null, 95))}
    res["compress_check"] = comp
    res.update({"record": "D745 WITHDRAWN (evidence, POST HOC)", "in_sample_last_session": str(max(days)),
                "runner": "scripts/d745_candidate_states.py", "runner_sha256": D.sha(Path(__file__).resolve()),
                "wall_s": round(time.time() - t0, 1)})
    D.write_once(OUT, res)
    print(json.dumps(D.strip(res), indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
