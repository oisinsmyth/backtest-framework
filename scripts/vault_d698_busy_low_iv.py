"""D698: the busy / low-IV/RV cell for the joint vault run, a pooled four-slice test (ES and NQ x D668's E4 plain break and
D663's opening-range break). Spec: docs/decisions/D698-PRE-REG-the-busy-low-iv-cell-for-the-joint-vault.md (68522305)
as amended by D698-A1 (85879686).

    uv run python scripts/vault_d698_busy_low_iv.py --selftest
    uv run python scripts/vault_d698_busy_low_iv.py --known-answer   # in-sample: D696's cells, the rehearsal of the vault path
    uv run python scripts/vault_d698_busy_low_iv.py --power          # the vault's power on contiguous in-sample windows -> data/vault_d698_power.json
    uv run python scripts/vault_d698_busy_low_iv.py --vault-bars B --vault-use U --vault-iv-es E --vault-iv-nq N --principals-word "..."
                                                                     # the joint run ONLY

X = compression tercile 3 (ctier >= 2/3) and the walk-forward IV/RV percentile < 1/2 (D696's declared cell). Per slice
d_s = mean gross of X breaks - mean of the other breaks, z_s its Welch z; T = sum of the four z. D698-A1: the null is the
enumerated rotation of each root's session-level X flag along the window's session axis (the same k for both roots and
both breaks, k = 21..n-21), trades fixed; p = (1 + #{T_k <= T}) / (1 + offsets). PASS: p <= 0.10 and >= 3 of 4 d_s < 0;
promotion p <= 0.005 (same sign rule); UNRESOLVED below 40 X breaks (or < 8 in either E4 slice). Programme slot 10.
The block-bootstrap helpers (`session_table`, `draw`, `resample`) remain for D698-A1's evidence script.

THE PIPELINE is cut-agnostic. D663's `root_frame` keeps only sessions before its module constant RESERVED_FROM, so the
vault path raises that constant for the duration of the build (`raised_cut`) and the known-answer mode proves the
mechanism both ways. The vault is never read here before the joint run; in-sample loaders cut at 2025-03-01.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any, Iterator

import numpy as np
import pandas as pd
from scipy import stats

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d696_busy_low_iv as Q  # noqa: E402

P, D, C = Q.P, Q.D, Q.C
M, T, X, S = Q.M, Q.T, Q.X, Q.S
ROOTS = ("ES", "NQ")
SLICES = ("ES_E4", "NQ_E4", "ES_D663", "NQ_D663")
CUT, VAULT_END, RAISED = "2025-03-01", "2026-09-18", "2026-09-19"
P_PASS, P_PROMO, MIN_X, MIN_X_E4, EDGE = 0.10, 0.005, 40, 8, 21
N_VAULT, BLOCK, WIN_STEP, SEED = 385, 20, 5, 698
PROGRAMME_SLOT = 10
SPEC = REPO / "docs" / "decisions" / "D698-PRE-REG-the-busy-low-iv-cell-for-the-joint-vault.md"
POWER_OUT = REPO / "data" / "vault_d698_power.json"
FROZEN = REPO / "data" / "FROZEN_vault_d698_busy_low_iv.json"
VAULT_OUT = REPO / "data" / "vault_d698_vault.json"
D696_JSON = REPO / "data" / "stage0_d696_busy_low_iv.json"
IMPORTED = ("stage0_d696_busy_low_iv.py", "stage1_d694_coiled_break.py", "stage0_d691_iv_size.py",
            "stage0_d671_break_construction.py", "stage0_d668_break_predictor.py", "stage0_d666_rebreak.py",
            "stage0_d663_per_root_gamma_break.py", "stage0_d662_gamma_product.py")


class VaultRuleError(RuntimeError):
    pass


# ================================================================================ the statistic
def slice_stat(g: np.ndarray, x: np.ndarray) -> dict[str, float]:
    """d = mean(X) - mean(rest), its Welch z; NaN when either side has fewer than 2."""
    a, b = g[x], g[~x]
    if len(a) < 2 or len(b) < 2:
        return {"n_x": int(len(a)), "n_rest": int(len(b)), "d": float("nan"), "z": float("nan")}
    se = math.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    d = float(a.mean() - b.mean())
    return {"n_x": int(len(a)), "n_rest": int(len(b)), "mean_x": float(a.mean()), "mean_rest": float(b.mean()),
            "d": d, "se": se, "z": d / se}


def rot_z(pos: np.ndarray, g: np.ndarray, f: np.ndarray, K: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Welch z, X count and d for every offset in K at once: break b takes the flag f[(pos_b - k) mod n] (1 X, 0 not,
    NaN no label, then left out). Returns (z, n_x, d), each of length len(K)."""
    n = len(f)
    F = f[(pos[:, None] - K[None, :]) % n]
    valid = np.isfinite(F)
    x, r = valid & (F == 1.0), valid & (F == 0.0)
    g2 = g * g

    def part(m: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        nn = m.sum(axis=0).astype(float)
        s, ss = g @ m, g2 @ m
        with np.errstate(divide="ignore", invalid="ignore"):
            mean = s / nn
            var = (ss - s * s / nn) / (nn - 1)
        return nn, mean, var
    nx, mx, vx = part(x)
    nr, mr, vr = part(r)
    with np.errstate(divide="ignore", invalid="ignore"):
        z = (mx - mr) / np.sqrt(vx / nx + vr / nr)
    z = np.where((nx >= 2) & (nr >= 2), z, np.nan)
    return z, nx, mx - mr


def rot_z_loop(pos: np.ndarray, g: np.ndarray, f: np.ndarray, k: int) -> float:
    """The same z for one offset through slice_stat (the assertion's second path)."""
    fl = f[(pos - k) % len(f)]
    ok = np.isfinite(fl)
    return slice_stat(g[ok], fl[ok] == 1.0)["z"]


def rotation_test(flags: dict[str, np.ndarray], sl: dict[str, tuple[np.ndarray, np.ndarray, str]]) -> dict[str, Any]:
    """D698-A1's test on one window: `flags` per root on the window's session axis, `sl` per slice (pos, gross, root)."""
    n = len(next(iter(flags.values())))
    K = np.arange(EDGE, n - EDGE)
    obs, Tk = {}, np.zeros(len(K))
    for k_ in SLICES:
        pos, g, r = sl[k_]
        z0, nx0, d0 = rot_z(pos, g, flags[r], np.array([0]))
        zk, _, _ = rot_z(pos, g, flags[r], K)
        obs[k_] = {"z": float(z0[0]), "n_x": int(nx0[0]), "d": float(d0[0])}
        Tk = Tk + zk
    nx = {k_: obs[k_]["n_x"] for k_ in SLICES}
    out: dict[str, Any] = {"slices": obs, "n_x_total": int(sum(nx.values())), "n_axis": n}
    z = np.array([obs[k_]["z"] for k_ in SLICES])
    if out["n_x_total"] < MIN_X or nx["ES_E4"] < MIN_X_E4 or nx["NQ_E4"] < MIN_X_E4 or not np.isfinite(z).all():
        out["verdict"] = "UNRESOLVED"
        return out
    T_ = float(z.sum())
    ok = np.isfinite(Tk)
    p = float((1 + (Tk[ok] <= T_).sum()) / (1 + ok.sum()))
    neg = int(sum(obs[k_]["d"] < 0 for k_ in SLICES))
    out.update({"T": T_, "offsets": int(ok.sum()), "offsets_dropped_nan": int((~ok).sum()),
                "null_p5_p10_p50": [float(np.quantile(Tk[ok], q)) for q in (0.05, 0.10, 0.50)],
                "p": p, "slices_negative": neg, "verdict": "PASS" if (p <= P_PASS and neg >= 3) else "FAIL",
                "programme_promotion_p_le_0.005": bool(p <= P_PROMO and neg >= 3)})
    return out


def axis_and_flags(labs: dict[str, pd.DataFrame], lo: str, hi: str) -> tuple[np.ndarray, dict[str, np.ndarray]]:
    """The window's session axis (sessions lo..hi where either root has a label) and each root's flag on it."""
    sets = []
    for r in ROOTS:
        L = labs[r]
        m = (L.index >= lo) & (L.index <= hi) & np.isfinite(L[["ctier", "p_iv"]].to_numpy(float)).all(axis=1)
        sets.append(set(L.index[m]))
    axis = np.array(sorted(set().union(*sets)))
    flags = {}
    for r in ROOTS:
        L = labs[r].reindex(axis)
        ct, pv = L["ctier"].to_numpy(float), L["p_iv"].to_numpy(float)
        flags[r] = np.where(np.isfinite(ct) & np.isfinite(pv), x_flags(ct, pv).astype(float), np.nan)
    return axis, flags


def on_axis(axis: np.ndarray, sess: np.ndarray, g: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pos = pd.Series(np.arange(len(axis)), index=axis).reindex(sess).to_numpy(float)
    m = np.isfinite(pos)
    return pos[m].astype(int), g[m]


# ================================================================================ the cut-agnostic pipeline
@contextlib.contextmanager
def raised_cut(value: str) -> Iterator[None]:
    """D663's root_frame keeps only sessions before its module constant; hold a different one for the build."""
    old = T.RESERVED_FROM
    T.RESERVED_FROM = value
    try:
        yield
    finally:
        T.RESERVED_FROM = old


def label_frame(d: pd.DataFrame, S_: pd.DataFrame, iv: pd.DataFrame) -> pd.DataFrame:
    """ctier and p_iv exactly as D694 builds them (the same functions and expressions), without the forecasts."""
    p_rv, p_on = C.tiers(S_["rv5"].to_numpy(float)), C.tiers(S_["on_range"].to_numpy(float))
    comp = (p_rv + p_on) / 2
    ctier = C.tiers(comp)
    ivs = iv["iv"].reindex(S_.index).to_numpy(float)
    rv = d["sig20"].reindex(S_.index).to_numpy(float) / 1e4 * np.sqrt(252.0)
    with np.errstate(divide="ignore", invalid="ignore"):
        ivrv = np.log(ivs / rv)
    p_iv = C.tiers(ivrv)
    step = max(1, len(ctier) // 12)
    C.tier_audit(ctier, comp, list(range(0, len(comp), step)))
    C.tier_audit(p_iv, ivrv, list(range(0, len(ivrv), step)))
    return pd.DataFrame({"ctier": ctier, "p_iv": p_iv, "ivrv": ivrv}, index=S_.index)


def build(b: pd.DataFrame, use: Any, R: Any, ivs: dict[str, pd.DataFrame], cut_hi: str) -> dict[str, dict[str, Any]]:
    """Per root: the labels, the E4 trades and D663's breaks, built with root_frame's cut held at `cut_hi`."""
    out: dict[str, dict[str, Any]] = {}
    with raised_cut(cut_hi):
        C._R = R
        T.MULT.update(M.MULT)
        tabs = R.session_table(b, use, roots=ROOTS)
        bars = R.bar_arrays(b)
        cal = pd.read_csv(D.DATA / "fixtures" / "cme_session_calendar.csv.gz", encoding="utf-8", dtype={"day": str})
        for r in ROOTS:
            dfull = T.root_frame(b, tabs[r], r)
            d = dfull[np.isfinite(dfull[["prior_high", "prior_low", "atr20"]]).all(axis=1)].copy()
            d["gd_spx"] = np.nan  # the labels do not read gamma
            on = C.overnight(b, r)
            C.overnight_audit(on)
            S_ = C.session_features(d, on, cal[cal["root"] == r].set_index("day"))
            lab = label_frame(d, S_, ivs[r])
            tr = P.trades(r, d, bars)
            rows = T.breaks(dfull, bars, r, S.MORNING)
            out[r] = {"lab": lab, "tr": tr, "rows": rows, "dfull_sessions": dfull.index}
    return out


def x_flags(ct: np.ndarray, piv: np.ndarray) -> np.ndarray:
    return (Q.tercile(ct) == 2) & (piv < 0.5)


def slices_from(built: dict[str, dict[str, Any]], lo: str, hi: str) -> tuple[dict[str, dict[str, float]], dict[str, Any]]:
    """The four slices on sessions lo..hi whose labels are finite."""
    sl, keep = {}, {}
    for r in ROOTS:
        lab = built[r]["lab"]
        tr, rows = built[r]["tr"], built[r]["rows"]
        for nm, sess, g in ((f"{r}_E4", tr["session"].to_numpy(str), tr["gross"].to_numpy(float)),
                            (f"{r}_D663", rows.index.to_numpy(str), rows["F"].to_numpy(float))):
            ct = lab["ctier"].reindex(sess).to_numpy(float)
            pv = lab["p_iv"].reindex(sess).to_numpy(float)
            m = (sess >= lo) & (sess <= hi) & np.isfinite(ct) & np.isfinite(pv)
            sl[nm] = slice_stat(g[m], x_flags(ct[m], pv[m]))
            keep[nm] = {"sessions": sess[m], "g": g[m], "x": x_flags(ct[m], pv[m])}
    return sl, keep


# ================================================================================ in-sample: known answers, R, power
def in_sample_slices() -> tuple[dict[str, Any], dict[str, dict[str, float]], dict[str, Any]]:
    """The four slices on D694's window from the audited bundle and D663's reproduced breaks (D696's objects)."""
    bd = P.get_bundle()
    bars, dfull = Q.load_bars()
    keep: dict[str, Any] = {}
    sl: dict[str, dict[str, float]] = {}
    labs: dict[str, pd.DataFrame] = {}
    for r in ROOTS:
        tr, lab = bd[r]["tr"], bd[r]["lab"]
        lab_ok = np.isfinite(lab[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
        labs[r] = lab.loc[lab_ok, ["ctier", "p_iv"]]
        win_sess = set(lab.index.to_numpy(str)[lab_ok])
        w1 = np.isfinite(tr[["t671", "ctier", "p_iv", "f1"]].to_numpy(float)).all(axis=1)
        t1 = tr[w1]
        rows = Q.d663_breaks(r, dfull[r], bars)
        t2 = rows[rows.index.isin(win_sess)]
        for nm, sess, g in ((f"{r}_E4", t1["session"].to_numpy(str), t1["gross"].to_numpy(float)),
                            (f"{r}_D663", t2.index.to_numpy(str), t2["F"].to_numpy(float))):
            ct = lab["ctier"].reindex(sess).to_numpy(float)
            pv = lab["p_iv"].reindex(sess).to_numpy(float)
            x = x_flags(ct, pv)
            sl[nm] = slice_stat(g, x)
            keep[nm] = {"sessions": sess, "g": g, "x": x}
    j = json.loads(D696_JSON.read_text(encoding="utf-8"))
    want = {"ES_E4": (j["B"]["ES"]["cells"]["X"]["n"], j["B"]["ES"]["cells"]["X"]["gross_bp"]),
            "NQ_E4": (j["B"]["NQ"]["cells"]["X"]["n"], j["B"]["NQ"]["cells"]["X"]["gross_bp"]),
            "ES_D663": (j["C"]["per_root_X_n"]["ES"], j["C"]["per_root_X_mean_F_bp"]["ES"]),
            "NQ_D663": (j["C"]["per_root_X_n"]["NQ"], j["C"]["per_root_X_mean_F_bp"]["NQ"])}
    for k, (n, mu) in want.items():
        if sl[k]["n_x"] != n or abs(sl[k]["mean_x"] - mu) > 1e-9:
            raise VaultRuleError(f"known answer: {k} X = ({sl[k]['n_x']}, {sl[k]['mean_x']}), D696 recorded ({n}, {mu})")
    return keep, sl, {"bd": bd, "dfull": dfull, "bars": bars, "labs": labs}


def session_table(keep: dict[str, Any]) -> tuple[np.ndarray, dict[str, dict[str, np.ndarray]]]:
    """The joint session axis and, per slice, the position of each break on it (one break a session per slice)."""
    axis = np.array(sorted(set().union(*[set(v["sessions"]) for v in keep.values()])))
    pos = pd.Series(np.arange(len(axis)), index=axis)
    tab = {}
    for k, v in keep.items():
        tab[k] = {"pos": pos.reindex(v["sessions"]).to_numpy(int), "g": v["g"], "x": v["x"]}
    return axis, tab


def draw(n_axis: int, n: int, rng: np.random.Generator) -> np.ndarray:
    """n session positions in contiguous blocks of BLOCK, drawn with replacement."""
    k = n // BLOCK + 1
    starts = rng.integers(0, n_axis - BLOCK, k)
    return np.concatenate([np.arange(s, s + BLOCK) for s in starts])[:n]


def resample(tab: dict[str, dict[str, np.ndarray]], idx: np.ndarray, shift: dict[str, float]) -> dict[str, dict[str, float]]:
    """The four slices on the drawn sessions (a session drawn twice contributes its break twice); X shifted by `shift`."""
    cnt = np.bincount(idx, minlength=int(max(v["pos"].max() for v in tab.values())) + 1)
    out = {}
    for k in SLICES:
        v = tab[k]
        rep = cnt[v["pos"]]
        g = np.repeat(v["g"] + np.where(v["x"], shift.get(k, 0.0), 0.0), rep)
        x = np.repeat(v["x"], rep)
        out[k] = slice_stat(g, x)
    return out


def power(keep: dict[str, Any], labs: dict[str, pd.DataFrame], sl: dict[str, dict[str, float]]) -> dict[str, Any]:
    """D698-A1: contiguous N_VAULT-session windows of the in-sample axis (starts every WIN_STEP), each scored by the
    rotation test inside the window, with every slice's X breaks shifted so its in-sample d is scaled."""
    axis, flags = axis_and_flags(labs, "0000", "9999")
    base = {k: on_axis(axis, keep[k]["sessions"], keep[k]["g"]) for k in SLICES}
    xs = {k: flags[k.split("_")[0]][base[k][0]] == 1.0 for k in SLICES}
    for k in SLICES:
        if len(base[k][0]) != len(keep[k]["x"]) or not np.array_equal(xs[k], keep[k]["x"]):
            raise VaultRuleError(f"power: the axis flags do not reproduce {k}'s X labels")
    starts = list(range(0, len(axis) - N_VAULT + 1, WIN_STEP))
    res: dict[str, Any] = {"n_vault_sessions": N_VAULT, "window_step": WIN_STEP, "windows": len(starts),
                           "distinct_windows_non_overlapping": len(axis) // N_VAULT, "axis_sessions": int(len(axis))}
    for s_ in (1.0, 0.5, 0.25, 0.0):
        ver, prom, ps, nx = [], [], [], []
        for s0 in starts:
            f_w = {r: flags[r][s0:s0 + N_VAULT] for r in ROOTS}
            sl_w = {}
            for k in SLICES:
                pos, g = base[k]
                m = (pos >= s0) & (pos < s0 + N_VAULT)
                g_s = g + np.where(xs[k], -(1 - s_) * sl[k]["d"], 0.0)
                sl_w[k] = (pos[m] - s0, g_s[m], k.split("_")[0])
            v = rotation_test(f_w, sl_w)
            ver.append(v["verdict"])
            prom.append(bool(v.get("programme_promotion_p_le_0.005", False)))
            ps.append(v.get("p", np.nan))
            nx.append(v["n_x_total"])
        vc = pd.Series(ver).value_counts(normalize=True).to_dict()
        res[f"effect_scale={s_:g}"] = {"PASS": float(vc.get("PASS", 0.0)), "FAIL": float(vc.get("FAIL", 0.0)),
                                       "UNRESOLVED": float(vc.get("UNRESOLVED", 0.0)), "promotion": float(np.mean(prom)),
                                       "p_median": float(np.nanmedian(ps)), "x_breaks_median": float(np.median(nx)),
                                       "x_breaks_p10_p90": [float(np.quantile(nx, 0.1)), float(np.quantile(nx, 0.9))]}
    return res


def rehearse(ctx: dict[str, Any]) -> dict[str, Any]:
    """The vault path on in-sample bars: the labels and trades it builds equal the audited bundle's; root_frame honours
    the held cut both ways. Nothing past 2025-02-28 exists in these bars."""
    b, use, _gd, R = M.load_bars(D.DATA, False, ROOTS)
    ivs = {r: D.iv_cached(r)[0] for r in ROOTS}
    built = build(b, use, R, ivs, RAISED)
    low = build(b, use, R, ivs, "2024-01-01")
    out: dict[str, Any] = prove(built, ctx)
    for r in ROOTS:
        if (low[r]["dfull_sessions"] >= "2024-01-01").any() or max(built[r]["dfull_sessions"]) < "2025-02-01":
            raise VaultRuleError("rehearsal: root_frame does not honour the held cut")
        out[r].update({"last_session_raised": str(max(built[r]["dfull_sessions"])),
                       "last_session_held_at_2024": str(max(low[r]["dfull_sessions"]))})
    sl, _ = slices_from(built, "2024-01-01", "2025-02-28")
    out["pseudo_vault_2024_counts"] = {k: sl[k]["n_x"] for k in SLICES}
    return out


def prove(built: dict[str, dict[str, Any]], ctx: dict[str, Any]) -> dict[str, Any]:
    """The vault path's objects before 2025-03-01 equal the audited in-sample ones exactly: the labels (D694's bundle),
    the E4 trades (the bundle) and D663's breaks (reproduced to D663's record)."""
    out: dict[str, Any] = {}
    for r in ROOTS:
        lab_b = ctx["bd"][r]["lab"]
        lab = built[r]["lab"].reindex(lab_b.index)
        for c in ("ctier", "p_iv"):
            if not np.array_equal(lab[c].to_numpy(float), lab_b[c].to_numpy(float), equal_nan=True):
                raise VaultRuleError(f"proof: {r} {c} from the vault path differs from D694's bundle")
        tb = ctx["bd"][r]["tr"]
        tv = built[r]["tr"][built[r]["tr"]["session"] < CUT].reset_index(drop=True)
        if len(tb) != len(tv) or not np.array_equal(tb["gross"].to_numpy(float), tv["gross"].to_numpy(float)):
            raise VaultRuleError(f"proof: {r} E4 trades from the vault path differ from the bundle")
        rw = built[r]["rows"]
        rw = rw[rw.index < CUT]
        if not rw["F"].equals(Q.d663_breaks(r, ctx["dfull"][r], ctx["bars"])["F"]):
            raise VaultRuleError(f"proof: {r} D663 breaks from the vault path differ")
        out[r] = {"labels_equal": True, "e4_trades_in_sample": int(len(tv)), "d663_breaks_in_sample": int(len(rw))}
    return out


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ================================================================================ selftest
def selftest() -> int:
    rng = np.random.default_rng(1)
    n = N_VAULT

    def markov(p_stay: float, base: float) -> np.ndarray:
        """A persistent 0/1 label with stationary share `base`."""
        p_in = base * (1 - p_stay) / (1 - base)
        f, s = np.zeros(n), rng.random() < base
        for i in range(n):
            f[i] = float(s)
            s = (rng.random() < p_stay) if s else (rng.random() < p_in)
        return f

    def world(effect: dict[str, float]) -> tuple[dict[str, np.ndarray], dict[str, tuple[np.ndarray, np.ndarray, str]]]:
        """Persistent labels (D698-A1's measured 0.3 / 0.09) and a slowly drifting mean shared by the slices: the
        clustered-outcome case that miscalibrated the registered test. `effect` is added to each slice's X breaks."""
        flags = {r: markov(0.3, 0.09) for r in ROOTS}
        e = rng.normal(0, 1, n)
        m = np.zeros(n)
        for i in range(1, n):
            m[i] = 0.97 * m[i - 1] + e[i]
        m *= 6.0
        sl = {}
        for k in SLICES:
            r = k.split("_")[0]
            pos = np.flatnonzero(rng.random(n) < 0.9)
            g = rng.normal(0, 40, len(pos)) + m[pos] + np.where(flags[r][pos] == 1.0, effect.get(k, 0.0), 0.0)
            sl[k] = (pos, g, r)
        return flags, sl
    # an injected effect is found
    v = rotation_test(*world({k: -40.0 for k in SLICES}))
    if not (v["verdict"] == "PASS" and v["p"] <= 0.01):
        raise AssertionError(f"an injected effect did not give p <= 0.01 ({v.get('p')})")
    # clustered noise: the rotation test holds its size where the registered pooled z did not
    ps, old = [], []
    for _ in range(200):
        w = world({})
        rt = rotation_test(*w)
        if rt["verdict"] != "UNRESOLVED":
            ps.append((rt["p"], rt["verdict"] == "PASS"))
            old.append(sum(rt["slices"][k]["z"] for k in SLICES) / 2.0 <= -1.2816)
    p_le_10 = float(np.mean([p <= 0.10 for p, _ in ps]))
    pass_rate = float(np.mean([ok for _, ok in ps]))
    if not (0.04 <= p_le_10 <= 0.16 and pass_rate <= 0.12):
        raise AssertionError(f"clustered noise: p <= 0.10 in {p_le_10:.3f}, PASS in {pass_rate:.3f}")
    # the vectorised rotation equals a loop over offsets; offset 0 equals slice_stat
    flags, sl = world({})
    pos, g, r = sl["NQ_E4"]
    K = np.array([0, 21, 57, 200, n - 22])
    zv, _, _ = rot_z(pos, g, flags[r], K)
    for i, k in enumerate(K):
        if not math.isclose(zv[i], rot_z_loop(pos, g, flags[r], int(k)), rel_tol=0, abs_tol=1e-9):
            raise AssertionError(f"the vectorised rotation differs from the loop at offset {k}")
    # UNRESOLVED below the counts; a pass carried by one slice FAILs
    f0 = {r_: np.zeros(n) for r_ in ROOTS}
    f0["ES"][:3] = 1.0
    few = {k: (np.arange(n), rng.normal(size=n), k.split("_")[0]) for k in SLICES}
    if rotation_test(f0, few)["verdict"] != "UNRESOLVED":
        raise AssertionError("fewer than 40 X breaks did not read UNRESOLVED")
    one = rotation_test(*world({"NQ_E4": -250.0, "ES_E4": +30.0, "ES_D663": +30.0, "NQ_D663": +30.0}))
    if one["verdict"] != "FAIL" or one["slices_negative"] != 1:
        raise AssertionError(f"a pass carried by one slice did not FAIL ({one['verdict']}, {one['slices_negative']} negative)")
    with raised_cut("2030-01-01"):
        if T.RESERVED_FROM != "2030-01-01":
            raise AssertionError("raised_cut did not hold")
    if T.RESERVED_FROM != "2025-03-01":
        raise AssertionError("raised_cut did not restore the module's cut")
    if main(["--vault-bars", "x.csv", "--vault-use", "u.json", "--vault-iv-es", "e.csv", "--vault-iv-nq", "n.csv"]) != 2:
        raise AssertionError("--vault ran without the principal's word")
    x = rng.normal(size=600)
    try:
        C.tier_audit(C.tiers(x, leak=True), x, [300, 450, 599])
    except C.D671Error:
        pass
    else:
        raise AssertionError("the tier's lag canary did not fire")
    # the bootstrap: resample with every session once reproduces the actual slice exactly; an injected X shift moves d
    keep = {k: {"sessions": np.array([f"s{i:04d}" for i in range(200)]), "g": rng.normal(0, 30, 200), "x": rng.random(200) < 0.15}
            for k in SLICES}
    axis, tab = session_table(keep)
    once = resample(tab, np.arange(len(axis)), {})
    for k in SLICES:
        if once[k]["d"] != slice_stat(keep[k]["g"], keep[k]["x"])["d"]:
            raise AssertionError("resampling every session once does not reproduce the slice")
    if not math.isclose(resample(tab, np.arange(len(axis)), {"ES_E4": -10.0})["ES_E4"]["d"], once["ES_E4"]["d"] - 10.0, abs_tol=1e-9):
        raise AssertionError("the X shift does not move d by the shift")
    print(f"selftest OK: an injected effect PASSes (p {v['p']:.4f}); clustered noise gives p <= 0.10 in {p_le_10:.3f} "
          f"and PASS in {pass_rate:.3f} (the registered pooled z would have passed {np.mean(old):.3f}); the vectorised "
          f"rotation equals the loop; UNRESOLVED below {MIN_X}; a one-slice pass FAILs; raised_cut holds and restores; "
          "--vault refused without the principal's word; the tier's lag canary fires; the bootstrap reproduces and shifts")
    return 0


# ================================================================================ main
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--known-answer", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--freeze", action="store_true", help="write the D698 freeze (once)")
    ap.add_argument("--vault-bars", default=None)
    ap.add_argument("--vault-use", default=None)
    ap.add_argument("--vault-iv-es", default=None)
    ap.add_argument("--vault-iv-nq", default=None)
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.vault_bars is not None:
        if not (a.principals_word or "").strip():
            print("refused: the vault is read only in the joint run, on the principal's word (A10)")
            return 2
        if not FROZEN.exists():
            raise VaultRuleError("the D698 freeze is missing")
        fz = json.loads(FROZEN.read_text(encoding="utf-8"))
        if fz.get("runner_sha256") != sha(Path(__file__).resolve()) or fz.get("prereg_sha256") != sha(SPEC) or \
                any(fz["imported_unchanged"][p] != sha(REPO / "scripts" / p) for p in IMPORTED):
            raise VaultRuleError("this runner, D698 or an imported module has moved since the freeze")
        if VAULT_OUT.exists():
            raise VaultRuleError("the vault line has already been scored; a second opening is refused")
        R = M.S.load_v2().R
        bv = pd.read_csv(a.vault_bars, encoding="utf-8", dtype={"session": str, "hhmm": str, "et": str})
        uv = json.loads(Path(a.vault_use).read_text(encoding="utf-8"))
        if (bv["session"] > VAULT_END).any():
            raise VaultRuleError("the vault bars hold a session after 2026-09-18")
        ivs = {}
        for r, pth in (("ES", a.vault_iv_es), ("NQ", a.vault_iv_nq)):
            t = pd.read_csv(pth, index_col=0, encoding="utf-8")
            t.index = t.index.astype(str)
            if (t.index > VAULT_END).any():
                raise VaultRuleError(f"the {r} IV table holds a session after 2026-09-18")
            ref = D.iv_cached(r)[0]["iv"]
            both = ref.index.intersection(t.index)
            if len(both) < 0.9 * len(ref) or not np.array_equal(ref.loc[both].to_numpy(float), t.loc[both, "iv"].to_numpy(float), equal_nan=True):
                raise VaultRuleError(f"the {r} vault IV table does not reproduce D691's in-sample IV exactly")
            ivs[r] = t
        built = build(bv, uv, R, ivs, RAISED)
        # proof first: the vault path's in-sample labels, trades and breaks equal the audited in-sample objects
        _keep, _sl, ctx = in_sample_slices()
        proof = prove(built, ctx)
        axis, flags = axis_and_flags({r: built[r]["lab"] for r in ROOTS}, CUT, VAULT_END)
        sl_v = {}
        for r in ROOTS:
            tr, rows = built[r]["tr"], built[r]["rows"]
            sl_v[f"{r}_E4"] = (*on_axis(axis, tr["session"].to_numpy(str), tr["gross"].to_numpy(float)), r)
            sl_v[f"{r}_D663"] = (*on_axis(axis, rows.index.to_numpy(str), rows["F"].to_numpy(float)), r)
        out = {"principals_word": a.principals_word, "proof_in_sample": proof, **rotation_test(flags, sl_v),
               "excluded_sessions_no_label": {r: int(((built[r]["lab"].index >= CUT) & (built[r]["lab"].index <= VAULT_END)
                                                      & ~np.isfinite(built[r]["lab"][["ctier", "p_iv"]].to_numpy(float)).all(axis=1)).sum())
                                              for r in ROOTS}}
        VAULT_OUT.write_text(json.dumps(out, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(out, indent=1, default=float))
        return 0
    if a.freeze:
        if FROZEN.exists():
            raise VaultRuleError(f"{FROZEN.name} exists; a freeze is written once (a change needs a new record)")
        pw = json.loads(POWER_OUT.read_text(encoding="utf-8"))
        doc = {"spec": SPEC.name, "prereg_sha256": sha(SPEC), "runner": "scripts/vault_d698_busy_low_iv.py",
               "runner_sha256": sha(Path(__file__).resolve()),
               "imported_unchanged": {p: sha(REPO / "scripts" / p) for p in IMPORTED},
               "params": {"cell": "ctier >= 2/3 and p_iv < 1/2", "statistic": "T = sum of the four Welch z",
                          "null": "rotation of each root's session X flag within the vault, same k, k = 21..n-21",
                          "p_pass": P_PASS, "p_promotion": P_PROMO, "signs": ">= 3 of 4 d < 0",
                          "min_x_total": MIN_X, "min_x_each_e4": MIN_X_E4, "slices": list(SLICES)},
               "amendment": "D698-A1 (85879686)",
               "known_answer_in_sample": pw["known_answer_in_sample"], "power": pw["power"],
               "vault": [CUT, VAULT_END], "programme_slot": PROGRAMME_SLOT}
        FROZEN.write_text(json.dumps(doc, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(doc, indent=1, default=float))
        return 0
    if a.known_answer or a.power:
        t0 = time.time()
        keep, sl, ctx = in_sample_slices()
        # the in-sample analogue of the amended test: the whole in-sample axis, rotated within itself (reported only)
        axis, flags = axis_and_flags(ctx["labs"], "0000", "9999")
        sl_in = {k: (*on_axis(axis, keep[k]["sessions"], keep[k]["g"]), k.split("_")[0]) for k in SLICES}
        ka = {"known_answer_in_sample": sl, "in_sample_rotation_test": rotation_test(flags, sl_in),
              "rehearsal": rehearse(ctx)}
        if a.known_answer:
            print(json.dumps(ka, indent=1, default=float))
            return 0
        res = {**ka, "power": power(keep, ctx["labs"], sl), "runtime_min": round((time.time() - t0) / 60, 2)}
        POWER_OUT.write_text(json.dumps(res, indent=1, default=float) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps({k: res[k] for k in ("in_sample_rotation_test", "power", "runtime_min")}, indent=1, default=float))
        return 0
    ap.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
