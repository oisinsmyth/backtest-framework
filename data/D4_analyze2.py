"""D4 analysis, part 2:
  (a) is leave-one-YEAR-out fragility remarkable? order-destroying null for the worst-LOO mean.
  (b) WHICH window is the clustered one -- named, with its dates.
  (c) the short leg measured on the negated series so the statistics are defined.
  (d) firm counts in the decile, for breadth.
  (e) a reproduction control: the series rebuilt here must match D4_series.json's means.
"""
import json, math, os, random, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from D4_defs import *          # noqa -- SER, WINDOWS, loaders, controls
from D4_measure import perm_p_rolling, max_rolling_share, moments

OUT2 = {}

# ---------- (e) reproduction control, run first: same objects as part 1?
PREV = json.load(open(os.path.join(HERE, "D4_series.json")))
rep = {"checked": 0, "mismatch": 0, "worst_abs_diff": 0.0, "missing": []}
for lab, d in SER.items():
    for wl, (a, b) in WINDOWS.items():
        months = sorted(m for m in d if a <= m <= b)
        if len(months) < 36:
            continue
        prev = PREV.get(lab, {}).get(wl)
        if prev is None:
            rep["missing"].append(lab + "|" + wl)
            continue
        mine = sum(d[m] for m in months) / len(months)
        rep["checked"] += 1
        diff = abs(mine - prev["mean"])
        rep["worst_abs_diff"] = max(rep["worst_abs_diff"], diff)
        if diff > 1e-12 or len(months) != prev["n"]:
            rep["mismatch"] += 1
rep["PASS"] = (rep["mismatch"] == 0 and not rep["missing"])
OUT2["_E_reproduction_control"] = rep
print("reproduction control:", rep, file=sys.stderr)


def loo_year(months, xs):
    """EXACT: each LOO mean is summed over the filtered list, in month order."""
    yrs = sorted({m[:4] for m in months})
    out = {}
    for y in yrs:
        f = [x for m, x in zip(months, xs) if m[:4] != y]
        out[y] = sum(f) / len(f)
    return out, min(out, key=lambda y: out[y]), max(out, key=lambda y: out[y])


def loo_null(xs, months, draws, seed):
    """Null: the SAME returns, re-ordered at random, so calendar years become random
    groupings. Total and marginal preserved exactly; only the time ordering is destroyed."""
    obs, w, b = loo_year(months, xs)
    rng = random.Random(seed)
    s = list(xs)
    vals = []
    for _ in range(draws):
        rng.shuffle(s)
        o, ww, bb = loo_year(months, s)
        vals.append(o[ww])
    vals.sort()
    le = sum(1 for v in vals if v <= obs[w])
    return dict(full_mean=sum(xs) / len(xs), n_years=len(obs),
                worst_year=w, worst_loo_mean=obs[w], best_year=b, best_loo_mean=obs[b],
                null_p05=vals[int(0.05 * len(vals))], null_p50=vals[len(vals) // 2],
                null_p95=vals[int(0.95 * len(vals))], draws=draws,
                p_value_worst_loo_at_least_this_low=(le + 1) / (len(vals) + 1),
                loo_by_year={k: round(v, 4) for k, v in obs.items()})


def best_window(months, xs, w):
    tot = sum(xs)
    bi, bv = None, None
    for i in range(len(xs) - w + 1):
        v = sum(xs[i:i + w])
        if bv is None or v > bv:
            bi, bv = i, v
    wi, wv = None, None
    for i in range(len(xs) - w + 1):
        v = sum(xs[i:i + w])
        if wv is None or v < wv:
            wi, wv = i, v
    return dict(best_start=months[bi], best_end=months[bi + w - 1], best_sum_pct=bv,
                best_share_of_total=(bv / tot if tot > 0 else None),
                worst_start=months[wi], worst_end=months[wi + w - 1], worst_sum_pct=wv,
                total_pct=tot)


SER2 = dict(SER)
SER2["NEG OP Lo10 VW short leg sign-flipped"] = {m: -v for m, v in SER["OP Lo10 VW - VW market"].items()}

for lab, d in SER2.items():
    OUT2[lab] = {}
    for wl, (a, b) in WINDOWS.items():
        months = sorted(m for m in d if a <= m <= b)
        if len(months) < 60:
            continue
        xs = [d[m] for m in months]
        rec = {"n": len(xs), "mean": sum(xs) / len(xs)}
        if len(xs) <= 200:           # LOO null only where it is affordable and relevant
            rec["loo_year"] = loo_null(xs, months, 2000, 77001)
        else:
            o, w_, b_ = loo_year(months, xs)
            rec["loo_year"] = dict(full_mean=sum(xs) / len(xs), n_years=len(o),
                                   worst_year=w_, worst_loo_mean=o[w_],
                                   best_year=b_, best_loo_mean=o[b_],
                                   note="no null: n>200, cost")
        for w in (12, 36):
            bw = best_window(months, xs, w)
            if len(xs) <= 760:
                pv = perm_p_rolling(xs, w, 1000, 77100 + w)
                bw["perm_p"] = (pv or {}).get("p_value")
                bw["perm_p50_share"] = (pv or {}).get("p50")
            rec["window_%dmo" % w] = bw
        pos = sorted([x for x in xs if x > 0], reverse=True)
        sp = sum(pos)
        rec["n_positive_months"] = len(pos)
        rec["top3_share_of_positive_sum"] = (sum(pos[:3]) / sp) if sp else None
        rec["top10pct_share_of_positive_sum"] = (sum(pos[:max(1, len(pos) // 10)]) / sp) if sp else None
        OUT2[lab][wl] = rec
    print("done2", lab, file=sys.stderr)

# ---------- (d) firm counts in the OP deciles
fc = {}
for col in ("Lo 10", "Hi 10"):
    vals = [(m, v[inf[col]]) for m, v in sorted(op_nf.items()) if v[inf[col]] is not None]
    dv = dict(vals)
    fc[col] = dict(first=vals[0], last=vals[-1],
                   min=min(vals, key=lambda t: t[1]), max=max(vals, key=lambda t: t[1]),
                   mean=sum(v for _, v in vals) / len(vals),
                   at_2014_01=dv.get("2014-01"), at_2024_12=dv.get("2024-12"))
OUT2["_firm_counts_OP_deciles"] = fc

json.dump(OUT2, open(os.path.join(HERE, "D4_series2.json"), "w"), indent=1, default=str)
print("written D4_series2.json", file=sys.stderr)
