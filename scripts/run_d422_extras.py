"""D422 EXTRAS -- exploratory, after the primary, and both arms can only weaken the secondary.
(a) the matched-count random-pool control for the ANY-REQ cell-2 book, which the pre-registration
    ran only for SAME; (b) ANY's premium by year, and the late-sample concentration of both rungs.
"""
import importlib.util, json, multiprocessing as mp, pathlib, sys
import numpy as np
REPO = pathlib.Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("d422r", REPO / "scripts" / "run_d422_second_zone.py")
M = importlib.util.module_from_spec(_s); sys.modules["d422r"] = M; _s.loader.exec_module(M)

if __name__ == "__main__":
    I, P, B, fl = M.load_all()
    N = len(I["t"]); c2 = I["c2"]; rb = I["r_base"]; t = I["t"]
    yr = np.array([int(str(x)[:4]) for x in I["dates"][t]])
    res = json.loads(M.OUT.read_text(encoding="utf-8"))
    # (b) per-year, both rungs, and the share of each rung's 2018+ P&L from 2020-2026
    print("premium by year, pooled: SAME / ANY")
    for y in sorted(set(yr.tolist())):
        m = yr == y
        gs = M.diff(rb[m & fl["s2same"]], rb[m & ~fl["s2same"]], "s")["diff_bp"]
        ga = M.diff(rb[m & fl["s2any"]], rb[m & ~fl["s2any"]], "a")["diff_bp"]
        print(f"  {y}  SAME {gs:+6.1f}   ANY {ga:+6.1f}")
    for k in ("s2same", "s2any"):
        h2 = fl[k] & (yr >= 2018); late = fl[k] & (yr >= 2020)
        print(f"  {k}: 2018+ mean {1e4*rb[h2].mean():+.2f} (n {h2.sum():,});  2018-2019 mean {1e4*rb[fl[k] & (yr>=2018) & (yr<=2019)].mean():+.2f};  "
              f"2020-2026 mean {1e4*rb[late].mean():+.2f} (n {late.sum():,})")
    # (a) the ANY-REQ control
    count = int((c2 & fl["s2any"]).sum()); workers = 8
    jobs = [(M.N10, count, list(range(w, M.N_DRAW, workers))) for w in range(workers)]
    with mp.Pool(workers) as pool:
        results = pool.map(M._ctrl_worker, jobs)
    out = sorted(o for oo in results for o in oo)
    net = np.array([o[1] for o in out]); ut = np.array([o[3] for o in out])
    obs = res["deltas"]["ANY-REQ_C2N10"]["net_abs"]
    p95 = float(np.quantile(net, .95)); se = float(net.std(ddof=1) / np.sqrt(net.size)); edge = obs - p95
    print(f"\nANY-REQ cell-2 book net {obs:+.3f} (mean over seeds)   random pools of {count:,}: p5 {np.quantile(net,.05):+.3f}  "
          f"p50 {np.median(net):+.3f}  p95 {p95:+.3f} (+-{se:.3f})   margin {edge/se:+.1f} SE   "
          f"{'BEATS p95' if edge > 0 else 'below p95'}{'  UNRESOLVED' if abs(edge) < 2*se else ''}   util ctrl {100*ut.mean():.1f}%")
    json.dump(dict(any_ctrl=dict(count=count, p5=float(np.quantile(net,.05)), p50=float(np.median(net)), p95=p95, se=se, observed=obs,
                                 margin_se=float(edge/se), beats=bool(edge>0), unresolved=bool(abs(edge)<2*se))),
              open(REPO / "data" / "d422_extras.json", "w"), indent=1)
    print("wrote data/d422_extras.json")
