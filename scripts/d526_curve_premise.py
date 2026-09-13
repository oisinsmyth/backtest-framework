"""D526 -- STAGE 0 on the curve story: does the front-vs-next spread condition the day session?

THE STORY. A price move is asymmetric when it forces somebody else to trade the same way. In a
storable commodity the front-to-next spread is the market price of IMMEDIACY -- what you pay to have
the barrel or the ounce now rather than in thirty days. Steep backwardation means inventory is tight
and someone with a physical obligation cannot wait, so a dip forces buying and the left tail is
truncated. The prediction is about the SHAPE of the day-session move, not its mean, because the
admitted arm hits 50.5% and is paid by a payoff ratio of 1.13 -- shape is what this book monetises.

FOUR CHECKS, cheapest-to-kill first:
  1 PERSISTENCE  does the state last a session? (measure the conditioner's own persistence FIRST)
  2 COLLINEARITY is it momentum wearing a hat? rank correlation against trailing returns
  3 SHAPE        does skew and the win/loss ratio differ by state?
  4 n_eff        do both states occur INSIDE a year, or is the tercile just a period?

NO P&L, no position, no cost, nothing admitted (R15). Window 2016-01-04..2023-12-29; the 2024+
slice is RESERVED and is not read.

    python scripts/d526_curve_premise.py --extract    # SYSTEM python (databento) -> data/d526_curve_strip_CL_GC.csv.gz
    python scripts/d526_curve_premise.py --run        # the four checks -> data/d526_curve_premise.json
"""
from __future__ import annotations
import argparse
import json
import re
import sys
import time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
FIX = REPO / "data" / "fixtures"
STRIP = REPO / "data" / "d526_curve_strip_CL_GC.csv.gz"
OUT = REPO / "data" / "d526_curve_premise.json"
ROOTS = ("CL", "GC")
ST_SETTLE = 3
PX = 1e-9
UNDEF = np.iinfo(np.int64).max
LO, HI = "2016-01-04", "2023-12-29"
BAND = {"CL": (-50.0, 200.0), "GC": (900.0, 3000.0)}      # CL settled -37.63 on 2020-04-20
MONTH = {c: i + 1 for i, c in enumerate("FGHJKMNQUVXZ")}
RE_C = re.compile(r"^(CL|GC)([FGHJKMNQUVXZ])(\d{1,2})$")


# ------------------------------------------------------------------ the settlement strip
def extract():
    """One settlement per (root, session, contract month), every listed month, from `statistics`.

    Uses the WINDOWED id mapping (D521), because a curve study is precisely the case a flat dict
    breaks: it reads ALL contracts rather than the volume-selected front month, so nothing filters a
    mislabelled back month out.
    """
    import databento as db
    import build_fut_open_interest as OI
    fs = [f for f in sorted(OI.RAW.glob("*.statistics.dbn.zst"))
          if not (f.name[24:28] < LO[:4] or f.name[10:14] > HI[:4])]
    print(f"{len(fs)} statistics files in {LO}..{HI}\n", flush=True)
    t0 = time.time()
    out = []
    for i, f in enumerate(fs, 1):
        store = db.DBNStore.from_file(f)
        w = OI.ids_of(store)
        w = w[w["root"].isin(ROOTS)].reset_index(drop=True)
        keys = w["iid"].to_numpy(np.uint32)
        n_keep = 0
        for arr in store.to_ndarray(count=5_000_000):
            a = arr[np.isin(arr["instrument_id"], keys) & (arr["stat_type"] == ST_SETTLE)]
            if not a.size:
                continue
            j = OI.label_rows(a, w)
            if not len(j):
                continue
            k = j["_i"].to_numpy()
            px = a["price"][k].astype("int64")
            ok = px != UNDEF
            if not ok.any():
                continue
            ts = pd.to_datetime(a["ts_ref"][k][ok].astype("int64"), utc=True).tz_convert("US/Eastern")
            out.append(pd.DataFrame({"root": j["root"].to_numpy()[ok], "contract": j["contract"].to_numpy()[ok],
                                     "ref": (ts + pd.Timedelta(days=1)).strftime("%Y-%m-%d"),
                                     "settle": px[ok] * PX}))
            n_keep += int(ok.sum())
        print(f"  [{i:2d}/{len(fs)}] {f.name[10:18]}  settlements {n_keep:>8,}  ({(time.time()-t0)/60:.1f} min)", flush=True)
    D = pd.concat(out, ignore_index=True)
    D = D[(D["ref"] >= LO) & (D["ref"] <= HI)]
    D = D.drop_duplicates(["root", "contract", "ref"], keep="last").sort_values(["root", "ref", "contract"])
    # A settlement of EXACTLY zero is not a price. UNDEF (INT64_MAX) is one missing marker and is
    # filtered above; ZERO IS A SECOND ONE and nothing else in the repo filters it. The rule cannot be
    # "drop non-positive": CL legitimately settled -37.63 on 2020-04-20.
    z = D["settle"] == 0.0
    if z.any():
        print(f"\n  dropped {int(z.sum())} settlements of exactly 0.0 (a missing marker): "
              f"{D[z].groupby('root').size().to_dict()}, contracts e.g. {sorted(D.loc[z,'contract'].unique())[:6]}")
        D = D[~z]
    for r, g in D.groupby("root"):
        lo, hi = BAND[r]
        bad = g[(g["settle"] < lo) | (g["settle"] > hi)]
        assert len(bad) == 0, f"[BAND] {r}: {len(bad)} settlements outside {lo}..{hi}\n{bad.head()}"
        print(f"  {r}: {len(g):,} settlements, {g['ref'].nunique():,} sessions, {g['contract'].nunique()} contracts, "
              f"price {g['settle'].min():.2f}..{g['settle'].max():.2f}, per session p50 {g.groupby('ref').size().median():.0f}")
    D.to_csv(STRIP, index=False, compression="gzip")
    print(f"\nwrote {STRIP.relative_to(REPO)} ({len(D):,} rows)")


# ------------------------------------------------------------------ the curve state
def ym(contract, session):
    """(year, month) of a contract code, resolved against the session it is quoted in.

    A one-digit year is ambiguous by a decade -- CLZ5 is Dec 2015 AND Dec 2025 -- so it resolves to
    the nearest delivery not more than one month behind the session. Two-digit years are explicit.
    """
    m = RE_C.match(contract)
    if not m:
        return None
    mon = MONTH[m.group(2)]
    y = m.group(3)
    sy, sm = int(session[:4]), int(session[5:7])
    if len(y) == 2:
        return (2000 + int(y), mon)
    for cand in range(sy - 1, sy + 12):
        if cand % 10 == int(y) and (cand * 12 + mon) >= (sy * 12 + sm) - 1:
            return (cand, mon)
    return None


def curve_state(strip):
    rows, drops = [], {"unparsed": 0, "collision": 0, "nonpositive": 0, "too_few": 0}
    for (root, ref), g in strip.groupby(["root", "ref"], sort=True):
        keys = [(ym(c, ref), c, s) for c, s in zip(g["contract"], g["settle"])]
        keys = [k for k in keys if k[0] is not None]
        drops["unparsed"] += len(g) - len(keys)
        if len(keys) < 2:
            drops["too_few"] += 1
            continue
        seen = {}
        for k, c, s in keys:
            seen.setdefault(k, []).append((c, s))
        if any(len(v) > 1 for v in seen.values()):
            drops["collision"] += 1
            continue
        order = sorted(seen)
        (c0, s0), (c1, s1) = seen[order[0]][0], seen[order[1]][0]
        if s0 <= 0 or s1 <= 0:
            drops["nonpositive"] += 1
            continue
        rows.append(dict(root=root, ref=ref, front=c0, nxt=c1,
                         curve=float(np.log(s0 / s1)), n_months=len(order)))
    return pd.DataFrame(rows), drops


def payoff(x):
    w, l = x[x > 0], x[x < 0]
    return float(w.mean() / abs(l.mean())) if len(w) > 5 and len(l) > 5 else float("nan")


def run():
    strip = pd.read_csv(STRIP, dtype={"root": str, "contract": str, "ref": str})
    C, drops = curve_state(strip)
    print(f"curve state for {len(C):,} (root, session) pairs; dropped {drops}\n")
    B = pd.read_csv(FIX / "fut_breadth_hourly.csv.gz",
                    usecols=["root", "day", "contract", "same_front", "present", "h09_o", "h15_c"],
                    dtype={"root": str, "day": str, "contract": str})
    B = B[(B["day"] >= LO) & (B["day"] <= HI) & B["root"].isin(ROOTS)]
    B = B[B["present"].astype(str).str.lower().isin(("true", "1")) &
          B["same_front"].astype(str).str.lower().isin(("true", "1"))]
    B = B.dropna(subset=["h09_o", "h15_c"])
    B = B[(B["h09_o"] > 0) & (B["h15_c"] > 0)]
    B["ret"] = np.log(B["h15_c"].to_numpy(float) / B["h09_o"].to_numpy(float))
    res = dict(window=[LO, HI], roots=list(ROOTS), drops=drops, per_root={})

    for root in ROOTS:
        c = C[C.root == root].sort_values("ref").reset_index(drop=True)
        b = B[B.root == root].sort_values("day").reset_index(drop=True)
        r = {}
        print("=" * 96)
        print(f"{root}: {len(c):,} curve observations, {len(b):,} day sessions, strip p50 {c['n_months'].median():.0f} months")
        r["backwardation_share"] = float((c["curve"] > 0).mean())
        print(f"      backwardation on {100*r['backwardation_share']:.1f}% of sessions")

        s = c.set_index("ref")["curve"]
        r["autocorr"] = {str(k): float(s.autocorr(k)) for k in (1, 5, 20, 60)}
        r["sign_flip_rate"] = float(np.mean(np.sign(s.to_numpy()[1:]) != np.sign(s.to_numpy()[:-1])))
        r["persistent_one_session"] = bool(r["autocorr"]["1"] > 0.8 and r["sign_flip_rate"] < 0.10)
        print(f"  [1] persistence  " + "  ".join(f"lag {k}: {v:+.3f}" for k, v in r["autocorr"].items())
              + f"   sign flips {100*r['sign_flip_rate']:.1f}%  -> {'PERSISTENT' if r['persistent_one_session'] else 'NOT persistent'}")

        m = b.merge(c[["ref", "curve"]].rename(columns={"ref": "day"}), on="day", how="inner")
        m["curve_lag"] = m["curve"].shift(1)           # settlement published ~21:00 ET on T, usable T+1
        assert m["curve_lag"].isna().sum() == 1, "[CAUSAL] the shift did not consume exactly one row"
        m = m.dropna(subset=["curve_lag"]).reset_index(drop=True)
        lc = np.log(m["h15_c"].to_numpy(float))
        r["collinearity"] = {}
        for k in (5, 20, 60):
            tr = pd.Series(lc).diff(k).to_numpy()
            ok = np.isfinite(tr)
            x, y = m["curve_lag"].to_numpy()[ok], tr[ok]
            r["collinearity"][str(k)] = dict(
                pearson=float(np.corrcoef(x, y)[0, 1]),
                spearman=float(np.corrcoef(pd.Series(x).rank().to_numpy(), pd.Series(y).rank().to_numpy())[0, 1]))
        print("  [2] collinearity " + "  ".join(
            f"{k}d p {v['pearson']:+.3f}/s {v['spearman']:+.3f}" for k, v in r["collinearity"].items()))

        m["yr"] = m["day"].str[:4]
        m["state"] = pd.qcut(m["curve_lag"], 3, labels=["contango", "middle", "backwardation"])
        r["shape"] = {}
        for st, g in m.groupby("state", observed=True):
            x = g["ret"].to_numpy() * 1e4
            r["shape"][str(st)] = dict(n=len(g), mean_bp=float(x.mean()), sd_bp=float(x.std(ddof=1)),
                                       skew=float(pd.Series(x).skew()), hit=float((x > 0).mean()),
                                       payoff=payoff(x))
        print("  [3] shape        " + "   ".join(
            f"{k}: skew {v['skew']:+.2f} payoff {v['payoff']:.3f}" for k, v in r["shape"].items()))

        r["years_with_both_states"] = int(sum(
            1 for _, g in m.groupby("yr")
            if (g.state == "contango").sum() >= 20 and (g.state == "backwardation").sum() >= 20))
        r["n_years"] = int(m["yr"].nunique())
        print(f"  [4] n_eff        years containing BOTH states (>=20 each): "
              f"{r['years_with_both_states']} of {r['n_years']}"
              + ("   <-- THE TERCILE IS A PERIOD, NOT A STATE" if r["years_with_both_states"] <= 1 else ""))

        m["dcurve"] = m["curve_lag"].diff()
        mm = m.dropna(subset=["dcurve"]).copy()
        mm["dstate"] = pd.qcut(mm["dcurve"], 3, labels=["flattening", "flat", "steepening"])
        r["change"] = {"years_with_both": int(sum(
            1 for _, g in mm.groupby("yr")
            if (g.dstate == "flattening").sum() >= 20 and (g.dstate == "steepening").sum() >= 20))}
        for st, g in mm.groupby("dstate", observed=True):
            x = g["ret"].to_numpy() * 1e4
            r["change"][str(st)] = dict(n=len(g), mean_bp=float(x.mean()), skew=float(pd.Series(x).skew()),
                                        hit=float((x > 0).mean()), payoff=payoff(x))
        gaps = np.array([payoff(g[g.dstate == "steepening"]["ret"].to_numpy() * 1e4)
                         - payoff(g[g.dstate == "flattening"]["ret"].to_numpy() * 1e4) for _, g in mm.groupby("yr")])
        gaps = gaps[np.isfinite(gaps)]
        r["change"]["year_gap_mean"] = float(gaps.mean())
        r["change"]["year_gap_positive"] = int((gaps > 0).sum())
        r["change"]["year_gap_n"] = int(len(gaps))
        print(f"  [5] the CHANGE   years with both extremes {r['change']['years_with_both']} of {r['n_years']}; "
              f"steepening payoff {r['change']['steepening']['payoff']:.3f} vs flattening "
              f"{r['change']['flattening']['payoff']:.3f}; year gap mean {r['change']['year_gap_mean']:+.3f}, "
              f"positive in {r['change']['year_gap_positive']} of {r['change']['year_gap_n']}")
        res["per_root"][root] = r
    print("=" * 96)
    OUT.write_text(json.dumps(res, indent=1))
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--extract", action="store_true")
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.extract:
        extract()
    elif a.run:
        run()
    else:
        ap.error("pick --extract or --run")
