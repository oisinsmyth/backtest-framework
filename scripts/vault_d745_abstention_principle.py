"""D745: the abstention principle on the joint vault, as pre-registered in
docs/decisions/D745-PRE-REG-the-abstention-principle-on-the-joint-vault.md (87a6d01d).

WITHDRAWN before its freeze (2026-10-01): the rehearsal showed the declared state does not reproduce the in-sample
pattern, and no candidate state sorts both continuation books (scripts/d745_candidate_states.py). --freeze and --vault
refuse; --selftest and the written rehearsal remain as evidence.

    uv run python scripts/vault_d745_abstention_principle.py --selftest
    uv run python scripts/vault_d745_abstention_principle.py --rehearse        # in-sample (<= 2023-12-29), run-once
    uv run python scripts/vault_d745_abstention_principle.py --freeze          # once, after --rehearse
    uv run python scripts/vault_d745_abstention_principle.py --vault --principals-word "..."   # the joint run ONLY,
                                                                   # after D716 --vault, D680 --run-vault, D734, D737

THE STATE (s.1): NQ's RTH panel (D727's panel_from_raw from 2016-01-04). A shock day: |ln(close/open)| at or above the
95th percentile (pandas linear) of the previous 250 panel sessions. FRESH: a shock in t-5..t-1; OLD: none there, one in
t-20..t-6; NONE: none in t-20..t-1. Known at the open. The in-sample frequencies (366 / 447 / 878 on 1,691 sessions)
are the known answer.

THE BOOKS (s.2): NQ F2 book B (D716's build and masks; 2024-01-01 -> 2026-09-18), C1 (D734's rebuild of the frozen
D680 path; 2025-03-01 -> 2026-09-18), D737 (its frozen cell over its vault load; 2024-01-01 -> 2026-09-18). Each is
reproduced against its recorded vault output before any state is joined. Units: $ at one MNQ, and y = net / sigma$
(sigma$ = the panel's sigma_oc x $2). A trade on a session the panel drops (a roll day) has no state and is counted,
not scored.

THE TESTS (s.3-s.4): P1 per continuation book mean y OLD > NONE > FRESH; P2 the pooled (C1 + F2) OLD - FRESH in y
against the exact circular rotation of each book's state labels over its own window sessions (offsets k = 0 .. the
longer window's length - 1; each book shifted by k mod its own length); P3 D737's OLD - FRESH below half the pooled one.
Readings CONFIRMED / CONSISTENT / REFUTED / NOT CONFIRMED, and the GENERIC VOLATILITY label.

Outputs (aggregates only): data/rehearsal_d745_abstention_principle.json, data/FROZEN_vault_d745_abstention_principle.json,
data/vault_d745_abstention_principle.json.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))

SPEC = REPO / "docs" / "decisions" / "D745-PRE-REG-the-abstention-principle-on-the-joint-vault.md"
REHEARSAL = REPO / "data" / "rehearsal_d745_abstention_principle.json"
FROZEN = REPO / "data" / "FROZEN_vault_d745_abstention_principle.json"
OUT = REPO / "data" / "vault_d745_abstention_principle.json"
DATA = REPO / "data"
Q, LOOKBACK, FRESH_W, OLD_W = 0.95, 250, 5, 20
STATES = ("OLD", "NONE", "FRESH")
KNOWN_STATE_COUNTS = {"FRESH": 366, "OLD": 447, "NONE": 878}      # in-sample, <= 2023-12-29 (temp/principle/state_freq.py)
IN_HI, VAULT_END = "2023-12-29", "2026-09-18"
WIN_VAULT = {"F2": ("2024-01-01", VAULT_END), "C1": ("2025-03-01", VAULT_END), "D737": ("2024-01-01", VAULT_END)}
WIN_IN = {"F2": ("2018-05-14", IN_HI), "C1": ("2018-01-09", IN_HI), "D737": ("2016-01-04", IN_HI)}
C1_IN_KNOWN = 328
CONT = ("C1", "F2")
ALPHA, HALF = 0.05, 0.5
USD = 2.0


class D745Error(AssertionError):
    pass


def need(ok: bool, msg: str) -> None:
    if not ok:
        raise D745Error(msg)


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


# ================================================================================ the state (s.1)
def state_series(days: np.ndarray, close: np.ndarray, open_: np.ndarray, leak: bool = False) -> pd.DataFrame:
    """Per panel session: the shock flag, its threshold and the state. `leak` (the canary) lets day t into its own
    threshold."""
    a = np.abs(np.log(close / open_))
    s = pd.Series(a)
    thr = (s if leak else s.shift(1)).rolling(LOOKBACK, min_periods=LOOKBACK).quantile(Q).to_numpy()
    shock = a >= thr                                   # NaN threshold -> False
    sh = pd.Series(shock.astype(float))
    fresh = sh.shift(1).rolling(FRESH_W, min_periods=FRESH_W).max().to_numpy() > 0
    old = sh.shift(FRESH_W + 1).rolling(OLD_W - FRESH_W, min_periods=OLD_W - FRESH_W).max().to_numpy() > 0
    ok = np.isfinite(thr) & np.isfinite(sh.shift(OLD_W).to_numpy())
    st = np.where(fresh, "FRESH", np.where(old, "OLD", "NONE"))
    st = np.where(ok, st, "NA")
    return pd.DataFrame({"a": a, "thr": thr, "shock": shock, "state": st}, index=pd.Index(np.asarray(days, str), name="day"))


def state_loop(a: np.ndarray, t: int) -> tuple[float, str]:
    """Second implementation for one session t (index into the panel)."""
    if t < LOOKBACK:
        return float("nan"), "NA"
    thr_t = float(np.quantile(a[t - LOOKBACK:t], Q))
    if t < OLD_W:
        return thr_t, "NA"

    def is_shock(j: int) -> bool:
        if j < LOOKBACK:
            return False
        return bool(a[j] >= np.quantile(a[j - LOOKBACK:j], Q))
    if any(is_shock(j) for j in range(t - FRESH_W, t)):
        return thr_t, "FRESH"
    if any(is_shock(j) for j in range(t - OLD_W, t - FRESH_W)):
        return thr_t, "OLD"
    return thr_t, "NONE"


def state_audit(st: pd.DataFrame, rng: np.random.Generator, n: int = 40) -> None:
    a = st["a"].to_numpy(float)
    cand = np.flatnonzero(st["state"].to_numpy() != "NA")
    for t in rng.choice(cand, min(n, len(cand)), replace=False):
        thr_t, s_t = state_loop(a, int(t))
        need(math.isclose(thr_t, float(st["thr"].iloc[t]), rel_tol=1e-12, abs_tol=1e-15) and s_t == st["state"].iloc[t],
             f"lag: the state at {st.index[t]} is {st['state'].iloc[t]} / {st['thr'].iloc[t]}, the loop's {s_t} / {thr_t}")


def counts_in_sample(st: pd.DataFrame) -> dict[str, int]:
    x = st[(st.index <= IN_HI) & (st["state"] != "NA")]["state"]
    return {k: int((x == k).sum()) for k in ("FRESH", "OLD", "NONE")}


# ================================================================================ joining and scoring (s.3-s.5)
def join(tr: pd.DataFrame, st: pd.DataFrame, soc: pd.Series, days_used: np.ndarray | None = None) -> pd.DataFrame:
    """Each trade's state and sigma$ by session string. `days_used` (the canary) shifts the panel's labels."""
    lab = st["state"]
    if days_used is not None:
        lab = pd.Series(lab.to_numpy(), index=pd.Index(np.asarray(days_used, str)))
    out = tr.copy()
    out["state"] = lab.reindex(out["session"]).to_numpy()
    out["sig_usd"] = soc.reindex(out["session"]).to_numpy(float) * USD
    out["y"] = out["net"] / out["sig_usd"]
    return out


def join_audit(tr: pd.DataFrame, st: pd.DataFrame, soc: pd.Series) -> None:
    j = join(tr, st, soc)
    for _, r in j.sample(min(30, len(j)), random_state=745).iterrows():
        want = st["state"].get(r["session"], np.nan)
        need((pd.isna(want) and pd.isna(r["state"])) or want == r["state"], f"join: {r['session']} reads {r['state']}, its own {want}")


def by_state(j: pd.DataFrame) -> dict[str, Any]:
    out = {}
    for s in STATES:
        x = j[j["state"] == s]
        out[s] = {"trades": int(len(x)), "mean_y": float(x["y"].mean()) if len(x) else None,
                  "mean_usd": float(x["net"].mean()) if len(x) else None, "median_usd": float(x["net"].median()) if len(x) else None,
                  "win_rate": float((x["net"] > 0).mean()) if len(x) else None, "total_usd": float(x["net"].sum())}
    out["unscored_no_state"] = int(j["state"].isna().sum() + (j["state"] == "NA").sum())
    return out


def p1(bs: dict[str, Any]) -> bool:
    m = [bs[s]["mean_y"] for s in STATES]
    return all(v is not None for v in m) and m[0] > m[1] > m[2]


def fresh_highest(bs: dict[str, Any]) -> bool:
    m = {s: bs[s]["mean_y"] for s in STATES}
    return all(v is not None for v in m.values()) and m["FRESH"] > m["OLD"] and m["FRESH"] > m["NONE"]


def window_frame(st: pd.DataFrame, lo: str, hi: str) -> pd.DataFrame:
    w = st[(st.index >= lo) & (st.index <= hi) & (st["state"] != "NA")]
    need(len(w) > 0, f"no state sessions in {lo} -> {hi}")
    return w


def delta(y: np.ndarray, lab: np.ndarray) -> float:
    o, f = lab == "OLD", lab == "FRESH"
    return float(y[o].mean() - y[f].mean()) if o.any() and f.any() else float("nan")


def rotation(parts: list[tuple[np.ndarray, np.ndarray, np.ndarray]]) -> dict[str, Any]:
    """parts: per book (window labels, trade positions in the window, trade y). Offset k shifts each book's labels by
    k mod its window length; the pooled OLD - FRESH at every k (k = 0 is the observed)."""
    K = max(len(L) for L, _, _ in parts)
    vals = np.full(K, np.nan)
    for k in range(K):
        ys, labs = [], []
        for L, pos, y in parts:
            ys.append(y)
            labs.append(L[(pos + k) % len(L)])
        vals[k] = delta(np.concatenate(ys), np.concatenate(labs))
    obs = vals[0]
    fin = vals[np.isfinite(vals)]
    return {"observed": float(obs), "offsets": int(K), "finite_offsets": int(len(fin)),
            "p_high": float(np.mean(fin >= obs)) if math.isfinite(obs) else None,
            "p_low": float(np.mean(fin <= obs)) if math.isfinite(obs) else None,
            "null_p50": float(np.percentile(fin, 50)), "null_p95": float(np.percentile(fin, 95)), "_vals": vals}


def episodes(w: pd.DataFrame, j: pd.DataFrame) -> dict[str, Any]:
    s = w["state"]
    run = (s != s.shift()).cumsum()
    out = {}
    for lab in ("OLD", "FRESH"):
        ids = run[s == lab].unique()
        pnl = []
        for i in ids:
            sess = set(s.index[run == i])
            pnl.append(float(j.loc[j["session"].isin(sess), "net"].sum()))
        out[lab] = {"episodes": int(len(ids)), "pnl_usd_by_episode": pnl}
    return out


def standard_views(j: pd.DataFrame, cal: np.ndarray) -> dict[str, Any]:
    def book(t: pd.DataFrame) -> dict[str, Any]:
        d = t.groupby("session")["net"].sum().reindex(cal).fillna(0.0).to_numpy()
        c = np.cumsum(d)
        sd = float(np.std(d, ddof=1)) if len(d) > 1 else float("nan")
        dn = math.sqrt(float(np.mean(np.minimum(d, 0.0) ** 2))) if len(d) else float("nan")
        return {"trades": int(len(t)), "total_usd": float(d.sum()), "usd_per_year": float(d.sum() / (len(d) / 252)),
                "sharpe": float(d.mean() / sd * math.sqrt(252)) if sd > 0 else None,
                "sortino": float(d.mean() / dn * math.sqrt(252)) if dn > 0 else None,
                "max_dd_usd": float(np.max(np.maximum.accumulate(np.r_[0.0, c])[1:] - c)) if len(c) else None,
                "share_sessions_traded": float((d != 0).mean())}
    return {"take_all": book(j), "skip_FRESH": book(j[j["state"] != "FRESH"]), "only_OLD": book(j[j["state"] == "OLD"])}


def score(books: dict[str, pd.DataFrame], wins: dict[str, tuple[str, str]], st: pd.DataFrame, soc: pd.Series) -> dict[str, Any]:
    res: dict[str, Any] = {"books": {}}
    parts = {}
    for nm, tr in books.items():
        lo, hi = wins[nm]
        t = tr[(tr["session"] >= lo) & (tr["session"] <= hi)].reset_index(drop=True)
        join_audit(t, st, soc)
        j = join(t, st, soc)
        w = window_frame(st, lo, hi)
        cal = np.array(sorted(set(w.index) | set(t["session"])))
        bs = by_state(j)
        sc = j[j["state"].isin(STATES) & np.isfinite(j["y"])]
        pos = pd.Series(np.arange(len(w)), index=w.index).reindex(sc["session"]).to_numpy()
        need(np.isfinite(pos).all(), f"{nm}: a scored trade is off its window's state sessions")
        parts[nm] = (w["state"].to_numpy(), pos.astype(int), sc["y"].to_numpy(float))
        res["books"][nm] = {"window": [lo, hi], "window_state_sessions": int(len(w)), "trades": int(len(t)),
                            "by_state": bs, "P1_order_OLD_NONE_FRESH": p1(bs), "FRESH_highest": fresh_highest(bs),
                            "delta_old_minus_fresh_y": delta(parts[nm][2], parts[nm][0][parts[nm][1]]),
                            "state_shares_in_window": {s: float((w["state"] == s).mean()) for s in STATES},
                            "episodes": episodes(w, j), "standard_views": standard_views(j, cal)}
    rot = rotation([parts[b] for b in CONT])
    rot.pop("_vals")
    d737 = res["books"]["D737"]["delta_old_minus_fresh_y"]
    pool = rot["observed"]
    P1c, P1f = res["books"]["C1"]["P1_order_OLD_NONE_FRESH"], res["books"]["F2"]["P1_order_OLD_NONE_FRESH"]
    P3 = bool(math.isfinite(pool) and pool > 0 and math.isfinite(d737) and d737 < HALF * pool)
    p_high = rot["p_high"] if rot["p_high"] is not None else 1.0
    p_low = rot["p_low"] if rot["p_low"] is not None else 1.0
    res["P2_pooled_rotation"] = rot
    res["P3"] = {"d737_delta": d737, "pooled_delta": pool, "holds": P3}
    res["reading"] = reading(P1c, P1f, P3, pool, p_high, p_low,
                             res["books"]["C1"]["FRESH_highest"] and res["books"]["F2"]["FRESH_highest"])
    return res


def reading(P1c: bool, P1f: bool, P3: bool, pool: float, p_high: float, p_low: float, fresh_top_both: bool) -> dict[str, Any]:
    if (math.isfinite(pool) and pool < 0 and p_low <= ALPHA) or fresh_top_both:
        r = "REFUTED"
    elif P1c and P1f and P3 and p_high <= ALPHA:
        r = "CONFIRMED"
    elif P1c and P1f and P3:
        r = "CONSISTENT"
    else:
        r = "NOT CONFIRMED"
    return {"reading": r, "GENERIC_VOLATILITY_NOT_PAYOFF_SPECIFIC": bool(P1c and P1f and p_high <= ALPHA and not P3),
            "P1_C1": bool(P1c), "P1_F2": bool(P1f), "P2_p_high": p_high, "P3": bool(P3)}


# ================================================================================ the books
def panel_state(rows: pd.DataFrame) -> tuple[pd.DataFrame, pd.Series, dict[str, Any]]:
    import stage0_d727_trend_curve as T7
    pn = T7.panel_from_raw("NQ", rows)
    st = state_series(pn["days"], pn["C"][:, -1], pn["O"])
    soc = pd.Series(pn["soc"], index=pd.Index(np.asarray(pn["days"], str)))
    return st, soc, pn


def state_checks(st: pd.DataFrame) -> dict[str, int]:
    rng = np.random.default_rng(745)
    state_audit(st, rng)
    leaky = state_series(st.index.to_numpy(), np.exp(st["a"].to_numpy()), np.ones(len(st)), leak=True)
    try:
        state_audit(leaky.assign(a=st["a"].to_numpy()), np.random.default_rng(745))
    except D745Error:
        pass
    else:
        raise D745Error("lag: the leaky-threshold canary did not fire")
    got = counts_in_sample(st)
    need(got == KNOWN_STATE_COUNTS, f"known answer: in-sample state counts {got} against {KNOWN_STATE_COUNTS}")
    return got


def in_sample_books() -> dict[str, Any]:
    """The rehearsal's books through the in-sample loaders (nothing on or after 2024-01-01)."""
    import stage0_d720_size_the_direction as Z
    import stage0_d738_follow_oracle as S1
    import stage0_d744_european_open_break as D744
    import vault_d716_nq_f2 as F
    import vault_d734_nq_book as K
    import vault_d737_nq_leads_the_dow as V737
    bd = F.build()
    ka = F.in_sample_answers(bd)
    F.check_known(ka)
    Bm, _ = F.masks(bd, F.B_START, F.IN_END)
    f_tr = K.f_part(bd, Bm)
    L = D744.load()                                   # D720's lowered cut; D672's per-year C1 known answer (D744-A1)
    tr = L["tr_c1"]
    c_mask = c1_in_mask(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(np.array_equal(c_mask, win), "C1: the in-sample session mask is not D672's t671 window")
    c_tr = K.c_part(tr, c_mask)
    cst = V737.cost()
    c_in = V737.in_sample(DATA)
    V737.check_known(c_in, cst)
    d_tr = d737_trades(c_in, cst, "2016-01-01", IN_HI)
    rows = S1.read_cut(S1.DATA / "fixtures" / "fut_NQ_rth_1m.csv.gz")
    Z.no_session_after(rows["day"].unique(), "the state panel")
    return {"books": {"F2": f_tr, "C1": c_tr, "D737": d_tr}, "rows": rows}


def c1_in_mask(tr: pd.DataFrame) -> np.ndarray:
    s = tr["session"].astype(str)
    m = ((s >= WIN_IN["C1"][0]) & (s <= IN_HI)).to_numpy() & np.isfinite(tr["ctier"].to_numpy(float)) & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(m.sum()) == C1_IN_KNOWN, f"C1 in-sample: {int(m.sum())} trades, not {C1_IN_KNOWN}")
    return m


def d737_trades(c: dict[str, Any], cst: float, lo: str, hi: str) -> pd.DataFrame:
    dd = np.asarray(c["days"], str)[c["d"]]
    m = (dd >= lo) & (dd <= hi)
    return pd.DataFrame({"session": dd[m], "net": (c["g"] - cst)[m]})


def strip(x: Any) -> Any:
    if isinstance(x, dict):
        return {k: strip(v) for k, v in x.items() if not str(k).startswith("_")}
    if isinstance(x, list):
        return [strip(v) for v in x]
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, np.bool_):
        return bool(x)
    return x


def write_once(path: Path, doc: dict[str, Any]) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(strip(doc), fh, indent=1)
        fh.write("\n")


# ================================================================================ modes
def rehearse() -> int:
    need(not REHEARSAL.exists(), f"{REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    b = in_sample_books()
    st, soc, _ = panel_state(b["rows"])
    cnt = state_checks(st)
    res = score(b["books"], WIN_IN, st, soc)
    res.update({"mode": "IN-SAMPLE REHEARSAL (POST HOC context; the freeze's known answer)", "state_counts_in_sample": cnt,
                "runner_sha256": sha(Path(__file__).resolve()), "prereg_sha256": sha(SPEC), "wall_s": round(time.time() - t0, 1)})
    write_once(REHEARSAL, res)
    show(res)
    return 0


def imported_repo_files() -> list[str]:
    out = set()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        p = Path(f).resolve()
        try:
            rel = p.relative_to(REPO).as_posix()
        except ValueError:
            continue
        if rel.startswith(("scripts/", "src/")) and rel.endswith(".py"):
            out.add(rel)
    return sorted(out)


def freeze() -> int:
    need(not FROZEN.exists(), f"{FROZEN.name} exists: the freeze is written once")
    need(REHEARSAL.exists(), "run --rehearse on the final code first")
    reh = json.loads(REHEARSAL.read_text(encoding="utf-8"))
    me = sha(Path(__file__).resolve())
    need(reh["runner_sha256"] == me and reh["prereg_sha256"] == sha(SPEC), "the rehearsal ran on another runner or record")
    import joint_d680_vault  # noqa: F401  (the vault path's modules, so their files are hashed)
    import stage0_d738_follow_oracle  # noqa: F401
    import stage0_d744_european_open_break  # noqa: F401
    import vault_d716_nq_f2  # noqa: F401
    import vault_d734_nq_book  # noqa: F401
    import vault_d737_nq_leads_the_dow  # noqa: F401
    files = [f for f in imported_repo_files() if f != "scripts/vault_d745_abstention_principle.py"]
    doc = {"record": "D745 (87a6d01d)", "runner": "scripts/vault_d745_abstention_principle.py", "runner_sha256": me,
           "prereg_sha256": sha(SPEC), "imported_unchanged": {f: sha(REPO / f) for f in files},
           "known_answer_in_sample": {"state_counts": reh["state_counts_in_sample"], "reading": reh["reading"],
                                      "books": {k: {"trades": v["trades"], "delta": v["delta_old_minus_fresh_y"]}
                                                for k, v in reh["books"].items()},
                                      "pooled_delta": reh["P2_pooled_rotation"]["observed"]},
           "frozen_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())}
    write_once(FROZEN, doc)
    print(json.dumps({k: doc[k] for k in ("runner_sha256", "prereg_sha256", "known_answer_in_sample")}, indent=1))
    print(f"hashed {len(files)} imported repo files")
    return 0


def check_freeze() -> dict[str, Any]:
    need(FROZEN.exists(), "D745 is not frozen")
    fz = json.loads(FROZEN.read_text(encoding="utf-8"))
    need(fz["runner_sha256"] == sha(Path(__file__).resolve()) and fz["prereg_sha256"] == sha(SPEC),
         "this runner or D745 has moved since the freeze")
    for p, h in fz["imported_unchanged"].items():
        need(sha(REPO / p) == h, f"{p} has moved since the freeze")
    return fz


def vault(word: str | None) -> int:
    if not (word or "").strip():
        print("refused: D745 reads the vault only in the joint run, on the principal's word (D745 s.7)")
        return 2
    fz = check_freeze()
    need(not OUT.exists(), "D745 has already been scored; a second opening is refused")
    t0 = time.time()
    import joint_d680_vault as J
    import vault_d716_nq_f2 as F
    import vault_d734_nq_book as K
    import vault_d737_nq_leads_the_dow as V737
    K.check_d716_freeze(F)
    J.check_freeze()
    V737.check_freeze(json.loads(V737.FROZEN.read_text(encoding="utf-8")))
    V680 = J.frozen_runner()
    for p, what in ((F.VAULT_OUT, "D716 --vault"), (V680.VAULT_OUT, "D680 --run-vault"), (K.VAULT_OUT, "D734 --vault"),
                    (V737.OUT, "D737 --vault")):
        need(p.exists(), f"order: {what} has not run")
    r716 = json.loads(F.VAULT_OUT.read_text(encoding="utf-8"))
    r680 = json.loads(V680.VAULT_OUT.read_text(encoding="utf-8"))
    r737 = json.loads(V737.OUT.read_text(encoding="utf-8"))
    # F2: D716's build and masks; the family's step 1 (2024-01-01 -> end) and both parts reproduced
    bd = F.build(VAULT_END, vault_open=True)
    net = np.asarray(bd["net"], float)
    Bf, _ = F.masks(bd, WIN_VAULT["F2"][0], VAULT_END)
    s1 = F.V.score(net[Bf])
    rs = r716["family"]["step1_nq_f2"]
    need(s1["trades"] == rs["trades"] and s1.get("mean_net") == rs.get("mean_net"), f"reproduce: D716 step 1 {s1} != {rs}")
    for nm, lo, hi in (("held_slice", "2024-01-01", "2025-02-28"), ("vault", "2025-03-01", VAULT_END)):
        b_, _ = F.masks(bd, lo, hi)
        g = F.V.score(net[b_])
        need(g["trades"] == r716["parts"][nm]["B"]["trades"] and g.get("mean_net") == r716["parts"][nm]["B"].get("mean_net"),
             f"reproduce: D716 {nm} B")
    f_tr = K.f_part(bd, Bf)
    Bi, _ = F.masks(bd, F.B_START, F.IN_END)
    f_in = K.f_part(bd, Bi)
    # C1: D734's path, reproduced against D680's vault output
    man = json.loads((J.JOINT / J.MANIFEST_NAME).read_text(encoding="utf-8"))
    bars_p, use_p = J.JOINT / J.BARS_NAME, J.JOINT / J.USE_NAME
    need(J.sha_bytes(bars_p.read_bytes()) == man["bars_sha256"] and J.sha_bytes(use_p.read_bytes()) == man["use_sha256"],
         "C1: the vault input files moved after their manifest")
    R = V680.M.S.load_v2().R
    bv, uv = J.read_like_runner(bars_p, use_p)
    with J.held(V680.T, "RESERVED_FROM", J.RAISED):
        tr, _sessions = V680.book(bv, uv, R, None)
    need(V680.T.RESERVED_FROM == J.CUT, "C1: the cut was not restored")
    sess = tr["session"].astype(str)
    v = ((sess >= WIN_VAULT["C1"][0]) & (sess <= VAULT_END)).to_numpy()
    c1 = v & (tr["ctier"].to_numpy(float) < 1 / 3)
    got_c = V680.score(tr.loc[c1, "gross"].to_numpy(float), tr.loc[c1, "net"].to_numpy(float), R)
    rc = r680["C1"]
    need(got_c["trades"] == rc["trades"] and got_c.get("gross_bp") == rc.get("gross_bp") and got_c.get("net_bp") == rc.get("net_bp"),
         f"reproduce: D680 C1 {got_c} != {rc}")
    c_tr = K.c_part(tr, c1)
    in_note = None
    try:
        c_in = K.c_part(tr, c1_in_mask(tr))
    except D745Error as e:
        c_in, in_note = None, f"C1's in-sample column is unavailable from the vault frame: {e}"
    # D737: its vault load and window, reproduced
    cst = V737.cost()
    c737_in = V737.in_sample(DATA)
    V737.check_known(c737_in, cst)
    cv = V737.vault_load(DATA, VAULT_END)
    V737.overlap_check(c737_in, cv)
    w = V737.window(cv, V737.VAULT_FROM, VAULT_END)
    g737 = np.asarray(w["g"], float)
    need(len(g737) == r737["score"]["trades"] and math.isclose(float((g737 - cst).mean()), r737["score"]["mean_net"], rel_tol=0, abs_tol=1e-9),
         "reproduce: D737's vault trades")
    d_tr = pd.DataFrame({"session": np.asarray(w["days"], str)[w["d"]], "net": g737 - cst})
    d_in = d737_trades(c737_in, cst, "2016-01-01", IN_HI)
    # the state on the full panel (2016-01-04 -> 2026-09-18); its in-sample prefix is the known answer
    import stage0_d727_trend_curve as T7
    rows = V737.read_window("NQ", DATA, T7.LO, VAULT_END)
    st, soc, _ = panel_state(rows)
    cnt = state_checks(st)
    res = score({"F2": f_tr, "C1": c_tr, "D737": d_tr}, WIN_VAULT, st, soc)
    res_in = score({"F2": f_in, "C1": c_in if c_in is not None else f_in.iloc[:0], "D737": d_in}, WIN_IN, st, soc) if c_in is not None else None
    reh = json.loads(REHEARSAL.read_text(encoding="utf-8"))
    same_in = None if res_in is None else (strip(res_in)["books"] == reh["books"])
    out = {"mode": "THE VAULT (the joint run)", "principals_word": word, "state_counts_in_sample": cnt,
           "reproduced": {"D716_step1": s1, "D680_C1": got_c, "D737_trades": int(len(g737))},
           "vault": res, "in_sample_column": res_in, "in_sample_matches_rehearsal": same_in, "in_sample_note": in_note,
           "frozen_known_answer": fz["known_answer_in_sample"], "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, out)
    show(res)
    return 0


def show(res: dict[str, Any]) -> None:
    for nm, b in res["books"].items():
        bs = b["by_state"]
        print(f"{nm} {b['window']}: trades {b['trades']}; " + "; ".join(
            f"{s} n {bs[s]['trades']} y {bs[s]['mean_y'] if bs[s]['mean_y'] is None else round(bs[s]['mean_y'], 4)}" for s in STATES)
            + f"; P1 {b['P1_order_OLD_NONE_FRESH']}; delta {b['delta_old_minus_fresh_y']}")
    r = res["P2_pooled_rotation"]
    print(f"pooled delta {r['observed']} p_high {r['p_high']} (p50 {r['null_p50']}, p95 {r['null_p95']}, {r['offsets']} offsets); "
          f"P3 {res['P3']}; READING {res['reading']}")


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []
    rng = np.random.default_rng(1)
    n = 900
    days = np.array([str(d.date()) for d in pd.bdate_range("2016-01-04", periods=n)])
    o = np.full(n, 100.0)
    c = 100.0 * np.exp(rng.standard_t(4, n) * 0.01)
    st = state_series(days, c, o)
    try:
        state_audit(st, rng, 60)
    except D745Error as e:
        fails.append(f"the state disagrees with its loop: {e}")
    leaky = state_series(days, c, o, leak=True)
    try:
        state_audit(leaky, np.random.default_rng(2), 60)
        fails.append("the leaky-threshold canary did not fire")
    except D745Error:
        pass
    shares = st["state"][st["state"] != "NA"].value_counts(normalize=True).to_dict()
    if not (0.05 < shares.get("FRESH", 0) < 0.6 and shares.get("OLD", 0) > 0.05):
        fails.append(f"implausible synthetic shares {shares}")
    # the join and its shifted canary
    soc = pd.Series(np.ones(n), index=pd.Index(days))
    tr = pd.DataFrame({"session": days[300::3], "net": rng.normal(0, 10, len(days[300::3]))})
    join_audit(tr, st, soc)
    shifted = join(tr, st, soc, days_used=np.roll(days, 1))
    if (shifted["state"].to_numpy() == join(tr, st, soc)["state"].to_numpy()).all():
        fails.append("a shifted join reads the same states (the canary cannot fire)")
    # the rotation: a planted state (OLD on the best trades, FRESH on the worst) comes out at p < 0.01
    m = 600
    y = rng.normal(0, 1, m)
    L = np.where(y > 0.8, "OLD", np.where(y < -0.8, "FRESH", "NONE"))
    pos = np.arange(m)
    r = rotation([(L, pos, y), (L[:400], pos[:400], y[:400])])
    if not (r["p_high"] is not None and r["p_high"] < 0.01):
        fails.append(f"the planted state's p is {r['p_high']}")
    if not math.isclose(r["_vals"][0], r["observed"]):
        fails.append("offset 0 is not the observed")
    # the readings
    cases = [((True, True, True, 0.3, 0.01, 0.99, False), "CONFIRMED"), ((True, True, True, 0.3, 0.2, 0.8, False), "CONSISTENT"),
             ((True, True, False, 0.3, 0.2, 0.8, False), "NOT CONFIRMED"), ((False, True, True, 0.3, 0.01, 0.99, False), "NOT CONFIRMED"),
             ((False, False, False, -0.3, 0.99, 0.01, False), "REFUTED"), ((False, False, False, 0.1, 0.5, 0.5, True), "REFUTED")]
    for args, want in cases:
        if reading(*args)["reading"] != want:
            fails.append(f"reading{args} is not {want}")
    if not reading(True, True, False, 0.3, 0.01, 0.99, False)["GENERIC_VOLATILITY_NOT_PAYOFF_SPECIFIC"]:
        fails.append("the GENERIC label does not fire")
    # p1 and the window frame
    bs = {"OLD": {"mean_y": 0.3}, "NONE": {"mean_y": 0.1}, "FRESH": {"mean_y": -0.2}}
    if not p1(bs) or p1({**bs, "NONE": {"mean_y": 0.4}}) or not fresh_highest({"OLD": {"mean_y": 0}, "NONE": {"mean_y": 0}, "FRESH": {"mean_y": 1}}):
        fails.append("p1 / fresh_highest")
    # refusal without the word, before anything is read
    if vault(None) != 2 or vault("  ") != 2:
        fails.append("--vault without the principal's word did not refuse with 2")
    try:
        need(False, "x")
        fails.append("need() did not raise")
    except D745Error:
        pass
    for f in fails:
        print(f"[SELFTEST FAIL] {f}")
    print(f"[D745] selftest: {'FAIL' if fails else 'all passed'}")
    return 1 if fails else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--rehearse", action="store_true")
    g.add_argument("--freeze", action="store_true")
    g.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word", default=None)
    a = ap.parse_args()
    if a.freeze or a.vault:
        print("[D745] WITHDRAWN before its freeze (the principal, 2026-10-01; the record's WITHDRAWN section): "
              "--freeze and --vault refuse. Kept as evidence; the vault is not spent on it.")
        return 3
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse()
    if a.freeze:
        return freeze()
    return vault(a.principals_word)


if __name__ == "__main__":
    sys.exit(main())
