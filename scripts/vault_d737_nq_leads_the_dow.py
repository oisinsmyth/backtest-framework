"""D737: NQ's lead over the Dow (D735's cell YM k1.0 1 sigma_rem) for the joint vault run. Spec:
docs/decisions/D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md, committed before this file existed.

    uv run python scripts/vault_d737_nq_leads_the_dow.py --selftest                # synthetic only
    uv run python scripts/vault_d737_nq_leads_the_dow.py --rehearse --data-root D  # in-sample (<= 2023-12-29), once
    uv run python scripts/vault_d737_nq_leads_the_dow.py --power --data-root D     # in-sample, once
    uv run python scripts/vault_d737_nq_leads_the_dow.py --freeze                  # once, after both
    uv run python scripts/vault_d737_nq_leads_the_dow.py --vault --principals-word "..." [--data-root D] \\
        [--accept-end YYYY-MM-DD]                                                  # the joint run ONLY

The construction is D735's own functions, imported (stage0_d735_nq_breaks_from_the_market: minute_x, align_rows,
spread, trigger, e1_tables, g_at, timing_null, matched_rows, fw_design, fw_delta, fw_null; D727's panel_from_raw and
load_root; D733's panels and nw_t). Nothing is re-implemented. In every mode but --vault the bars are read through
D727's load_root, which filters to 2023-12-29 and raises on a later session; --vault reads 2023-09-01 -> 2026-09-18
and nothing later.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
import time
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d720_size_the_direction as Z  # noqa: E402
import stage0_d727_trend_curve as T  # noqa: E402
import stage0_d731_flat_u as F  # noqa: E402
import stage0_d733_pullback_entry as B  # noqa: E402
import stage0_d735_nq_breaks_from_the_market as S  # noqa: E402

RUNNER_REL = "scripts/vault_d737_nq_leads_the_dow.py"
SPEC_REL = "docs/decisions/D737-PRE-REG-nq-leads-the-dow-for-the-joint-vault.md"
D735_PRE_REL = "docs/decisions/D735-STAGE-0-PRE-REG-nq-breaks-from-the-market.md"
D735_RES_REL = "docs/decisions/D735-STAGE-0-RESULT-nq-breaking-from-the-market-beats-its-null.md"
D735_JSON = REPO / "data" / "stage0_d735_nq_breaks_from_the_market.json"
REHEARSAL = REPO / "data" / "rehearsal_vault_d737.json"
POWER = REPO / "data" / "vault_d737_power.json"
FROZEN = REPO / "data" / "FROZEN_vault_d737_nq_leads_the_dow.json"
OUT = REPO / "data" / "vault_d737_nq_leads_the_dow.json"
D716_VAULT_OUT = REPO / "data" / "vault_d716_nq_f2_result.json"

LEG, K, STOP_MULT, CELL = "YM", 1.0, 1.0, "YM_k1.0_1s"
IN_HI, VAULT_FROM, VAULT_END, LOAD_FROM = "2023-12-29", "2024-01-01", "2026-09-18", "2023-09-01"
OVERLAP = ("2023-11-01", "2023-12-29")
KNOWN = {"trades": 1699}                                  # mean net read from D735's JSON, to 1e-9
MIN_TRADES, T_GATE, NW_LAGS = 100, 1.645, 5
SEED, POWER_DRAWS, POWER_BLOCK, POWER_STEP = 737, 4000, 20, 20
PROGRAMME_FAMILY = "NQ leads the Dow (D735 YM k1.0)"
INSTRUCTION = ('the principal, 2026-10-01: "I choose YM 1.0, it look really good"; '
               '"Yes write it into slot 110 and freeze"')
REFUSED = 2
P = Z.P


class VaultError(RuntimeError):
    pass


# ================================================================================ the cell (D735's functions)
def cell(pnN: dict[str, Any], pnY: dict[str, Any]) -> dict[str, Any]:
    pp = B.panels(pnN)
    days = pnN["days"]
    XN = S.minute_x(pp["C"], pp["O"], pp["soc"])
    XL = S.align_rows(pnY["days"], S.minute_x(pnY["C"], pnY["O"], pnY["soc"]), days)
    sp = S.spread(XN, XL)
    m0, D = S.trigger(sp["Z"], sp["S"], K)
    G = S.e1_tables(pp, STOP_MULT)
    d = np.flatnonzero(m0 >= 0)
    g = S.g_at(G, d, m0[d], D[d])
    if not np.isfinite(g).all():
        raise VaultError("a trade has no E1 value")
    return {"days": days, "pp": pp, "XN": XN, "XL": XL, "sp": sp, "m0": m0, "D": D, "G": G, "d": d, "g": g}


def cost() -> float:
    import stage1_d711_f2_mechanism as M711
    return float(M711.cost_line("NQ")["cost"])


def known_mean() -> float:
    return float(json.loads(D735_JSON.read_text(encoding="utf-8"))["cells"][CELL]["mean_net"])


def check_known(c: dict[str, Any], cst: float) -> dict[str, Any]:
    sel = c["days"][c["d"]] <= IN_HI
    net = c["g"][sel] - cst
    got = {"trades": int(sel.sum()), "mean_net": float(net.mean())}
    if got["trades"] != KNOWN["trades"] or not math.isclose(got["mean_net"], known_mean(), rel_tol=0, abs_tol=1e-9):
        raise VaultError(f"the in-sample known answer is not reproduced: {got} against {KNOWN['trades']} / {known_mean()}")
    return got


# ================================================================================ loading
def in_sample(data_root: Path) -> dict[str, Any]:
    pnN, pnY = T.load_root("NQ", data_root), T.load_root("YM", data_root)
    for pn in (pnN, pnY):
        if (pn["days"] > IN_HI).any():
            raise VaultError("seal: an in-sample load holds a session after 2023-12-29")
    return cell(pnN, pnY)


def read_window(root: str, data_root: Path, lo: str, hi: str) -> pd.DataFrame:
    b = pd.read_csv(data_root / "fixtures" / f"fut_{root}_rth_1m.csv.gz", encoding="utf-8",
                    dtype={"day": str, "hhmm": str, "contract": str})
    return window_rows(b, lo, hi)


def window_rows(b: pd.DataFrame, lo: str, hi: str) -> pd.DataFrame:
    b = b[(b["day"] >= lo) & (b["day"] <= hi)]
    if len(b) and b["day"].max() > hi:
        raise VaultError(f"seal: a row after {hi} survived the filter")
    return b


def vault_load(data_root: Path, end: str) -> dict[str, Any]:
    if end > VAULT_END:
        raise VaultError(f"seal: the vault load may not pass {VAULT_END}")
    rows = {r: read_window(r, data_root, LOAD_FROM, end) for r in ("NQ", LEG)}
    for r, b in rows.items():
        last = b["day"].max() if len(b) else ""
        if last < end:
            raise VaultError(f"{r}'s fixture ends {last}, before {end}: rebuild it (D462) or pass --accept-end")
    return cell(T.panel_from_raw("NQ", rows["NQ"]), T.panel_from_raw(LEG, rows[LEG]))


def overlap_check(a: dict[str, Any], b: dict[str, Any]) -> int:
    """The trades of two loads on the overlap days must be identical: days, m0, sides, gross."""
    def rows(c: dict[str, Any]) -> pd.DataFrame:
        dd = c["days"][c["d"]]
        m = (dd >= OVERLAP[0]) & (dd <= OVERLAP[1])
        return pd.DataFrame({"day": dd[m], "m0": c["m0"][c["d"]][m], "D": c["D"][c["d"]][m], "g": c["g"][m]}).reset_index(drop=True)
    ra, rb = rows(a), rows(b)
    if len(ra) == 0 or not ra.equals(rb):
        raise VaultError(f"the overlap {OVERLAP} does not reproduce: {len(ra)} against {len(rb)} trades")
    return len(ra)


# ================================================================================ scoring a window
def window(c: dict[str, Any], lo: str, hi: str) -> dict[str, Any]:
    r = np.flatnonzero((c["days"] >= lo) & (c["days"] <= hi))
    if len(r) == 0:
        raise VaultError(f"no sessions in {lo} -> {hi}")
    pos = np.full(len(c["days"]), -1)
    pos[r] = np.arange(len(r))
    keep = (c["days"][c["d"]] >= lo) & (c["days"][c["d"]] <= hi)
    G = {k: v[r] for k, v in c["G"].items()}
    return {"days": c["days"][r], "XN": c["XN"][r], "XL": c["XL"][r], "S": c["sp"]["S"][r], "G": G,
            "soc": c["pp"]["soc"][r], "pp": {k: (v[r] if np.ndim(v) else v) for k, v in c["pp"].items()},
            "d": pos[c["d"][keep]], "m0": c["m0"][c["d"]][keep], "D": c["D"][c["d"]][keep], "g": c["g"][keep]}


def gate(n: int, mean_net: float, t: float, c2a_p95: float) -> dict[str, Any]:
    g0 = n >= MIN_TRADES
    g1 = mean_net > 0 and t >= T_GATE
    g2 = mean_net > c2a_p95
    verdict = ("UNRESOLVED" if not g0 else "PASS" if (g1 and g2) else "FAIL" if mean_net <= 0 else "UNRESOLVED")
    return {"G0_trades": bool(g0), "G1_mean_and_t": bool(g1), "G2_beats_timing_null": bool(g2), "verdict": verdict}


def score(w: dict[str, Any], cst: float, full: bool = True) -> dict[str, Any]:
    d, m0, D, g = w["d"], w["m0"], w["D"], w["g"]
    n = len(w["days"])
    net = g - cst
    t = B.nw_t(net) if len(net) >= 10 else float("nan")
    offs = np.arange(S.EDGE, n - S.EDGE)
    c2a = S.timing_null(w["G"], d, m0, w["XN"], w["XN"], cst, offs)
    p95 = float(np.nanquantile(c2a["mean_net"], 0.95))
    res: dict[str, Any] = {"sessions": int(n), "trades": int(len(d)), "mean_net": float(net.mean()) if len(net) else float("nan"),
                           "mean_gross": float(g.mean()) if len(g) else float("nan"), "nw_t": t,
                           "C2a_mean": S.rot(float(net.mean()), c2a["mean_net"])}
    res["gate"] = gate(len(d), res["mean_net"], t, p95)
    if not full:
        return res
    eff = float(g.sum() / np.abs(g).sum())
    c2b = S.timing_null(w["G"], d, m0, w["S"], w["XN"], cst, offs)
    c2b0 = S.timing_null(w["G"], d, m0, w["S"], w["XN"], cst, np.array([0]))
    if not math.isclose(float(c2b0["mean_net"][0]), res["mean_net"], rel_tol=0, abs_tol=1e-9):
        raise VaultError("right quantity: C2b's offset 0 does not reproduce the window's trades")
    gfull = np.full(n, np.nan)
    gfull[d] = g
    bk, daily = F.book(np.where(np.isfinite(gfull), 1.0, 0.0), gfull, cst, w["days"])
    aligned = np.sign(w["XN"][d, m0]) == D
    ctr = ~aligned
    fol = S.g_at(w["G"], d[ctr], m0[ctr], np.sign(w["XN"][d[ctr], m0[ctr]]))
    fol = np.where(np.isfinite(fol), fol, 0.0)
    pair = g[ctr] - fol
    from backtest_framework.validation.concentration import year_concentration
    yc = year_concentration(w["days"][d].astype(str), net, scale=w["soc"][d] * S.USD)
    mr = S.matched_rows(w["G"], w["XN"], d, m0, g, cst, np.random.default_rng(SEED))
    fw = S.fw_design(w["XN"], w["XL"])
    dl, bt, tcl = S.fw_delta(fw["x"], fw["y"], fw["e"], cluster_t=True)
    mfe = {}
    pp = w["pp"]
    for h in (15, 30, 60, None):
        a_, b_ = [], []
        for dd, mm, DD in zip(d, m0, D):
            last = S.NMIN - 1 if h is None else min(mm + h - 1, S.NMIN - 1)
            ent = pp["Op"][dd, mm]
            hi_, lo_ = pp["H"][dd, mm:last + 1], pp["L"][dd, mm:last + 1]
            a_.append(((hi_.max() - ent) if DD > 0 else (ent - lo_.min())) * S.USD)
            b_.append(((lo_.min() - ent) if DD > 0 else (ent - hi_.max())) * S.USD)
        mfe["close" if h is None else str(h)] = {"mean_mfe": float(np.mean(a_)), "mean_mae": float(np.mean(b_))}
    res.update({
        "t_vs_1.2816": bool(t >= 1.2816), "t_vs_2.576": bool(t >= 2.576),
        "efficiency": {"observed": eff, "C2a_p95": float(np.nanquantile(c2a["eff"], 0.95))},
        "C2b_mean": S.rot(res["mean_net"], c2b["mean_net"]), "book": bk,
        "counter": {"trades": int(ctr.sum()), "mean_gross": float(g[ctr].mean()) if ctr.any() else None,
                    "C1_paired_mean": float(pair.mean()) if len(pair) else None},
        "mirror_mean_net": float((S.g_at(w["G"], d, m0, -D) - cst).mean()),
        "matched_rows": mr, "year_concentration": {"label": yc["label"], "max_share_usd": yc["gross"]["max_share"],
                                                   "max_share_vol": (yc.get("vol_units") or {}).get("max_share")},
        "mechanism_delta": {"delta": dl, "beta": bt, "t_clustered": tcl,
                            "rotation": S.rot(dl, S.fw_null(fw["x"], fw["y"], fw["e"]))},
        "entry_hour_counts": {str(k): int(v) for k, v in pd.Series([(570 + m) // 60 for m in m0]).value_counts().sort_index().items()},
        "stopped_share": float(S.stopped_at(w["G"], d, m0, D).mean()), "mfe_mae": mfe})
    res["_daily"] = daily
    return res


def strip(res: dict[str, Any]) -> dict[str, Any]:
    return {k: v for k, v in res.items() if not k.startswith("_")}


# ================================================================================ power (in-sample)
def power(c: dict[str, Any], cst: float) -> dict[str, Any]:
    rng = np.random.default_rng(SEED)
    sel = c["days"][c["d"]] <= IN_HI
    g = c["g"][sel]
    socd = c["pp"]["soc"][c["d"][sel]] * S.USD
    u = g / socd
    n_in = int((c["days"] <= IN_HI).sum())
    rate = len(g) / n_in
    vault_sessions = 680                                   # 2024-01-01 -> 2026-09-18, about, before roll days
    N = int(round(rate * vault_sessions))
    sig_in = float(socd.mean())
    sig23 = float(c["pp"]["soc"][(c["days"] >= "2023-01-01") & (c["days"] <= IN_HI)].mean() * S.USD)
    out: dict[str, Any] = {"expected_vault_trades": N, "trade_rate": rate, "sigma_usd_in_sample": sig_in,
                           "sigma_usd_2023": sig23, "g1_bootstrap": {}}
    nb = N // POWER_BLOCK
    for lab, sv in (("in_sample_sigma", sig_in), ("sigma_2023", sig23)):
        for f in (1.0, 0.75, 0.5, 0.25, 0.0):
            net_all = (u - (1 - f) * u.mean()) * sv - cst
            starts = rng.integers(0, len(net_all) - POWER_BLOCK, size=(POWER_DRAWS, nb))
            idx = (starts[:, :, None] + np.arange(POWER_BLOCK)[None, None, :]).reshape(POWER_DRAWS, -1)
            sm = net_all[idx]
            t = sm.mean(axis=1) / (sm.std(axis=1, ddof=1) / math.sqrt(sm.shape[1]))
            out["g1_bootstrap"][f"{lab}_{int(f * 100)}pct"] = {
                "mean_net": float(net_all.mean()), "pass_g1": float(np.mean((sm.mean(axis=1) > 0) & (t >= T_GATE))),
                "mean_positive": float(np.mean(sm.mean(axis=1) > 0))}
    # the full gate on moving in-sample windows as long as the vault, at the observed edge
    days_in = c["days"][c["days"] <= IN_HI]
    W = vault_sessions
    verdicts = []
    for s0 in range(0, len(days_in) - W + 1, POWER_STEP):
        w = window(c, days_in[s0], days_in[s0 + W - 1])
        verdicts.append(score(w, cst, full=False)["gate"]["verdict"])
    vv = pd.Series(verdicts)
    out["full_gate_windows"] = {"windows": int(len(vv)), "step": POWER_STEP, "length_sessions": W,
                                "independent_approx": round(len(days_in) / W, 2),
                                "share": {k: float(v) for k, v in vv.value_counts(normalize=True).items()}}
    return out


# ================================================================================ freeze
_TOP = re.compile(r"^(?:import|from)[ \t]+([A-Za-z_]\w*)", re.M)
_BF = re.compile(r"^[ \t]*(?:from[ \t]+(backtest_framework[\w.]*)[ \t]+import|import[ \t]+(backtest_framework[\w.]*))", re.M)


def sha_text(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def discover(root: Path, starts: tuple[str, ...]) -> list[str]:
    """Repo modules imported at module level, recursively (static; never executed). Function-level imports are
    listed by hand in EXTRA, because they run in this runner's paths."""
    seen: set[str] = set()
    stack = list(starts)
    while stack:
        rel = stack.pop()
        if rel in seen:
            continue
        seen.add(rel)
        text = (root / rel).read_text(encoding="utf-8")
        found = [f"scripts/{n}.py" for n in _TOP.findall(text)]
        for a, b in _BF.findall(text):
            parts = (a or b).split(".")
            for k in range(1, len(parts) + 1):
                base = root / "src" / Path(*parts[:k])
                for p in (base.with_suffix(".py"), base / "__init__.py"):
                    if p.exists():
                        found.append(p.relative_to(root).as_posix())
        stack += [f for f in found if (root / f).exists() and f not in seen]
    return sorted(seen - set(starts))


EXTRA = ("scripts/stage1_d711_f2_mechanism.py", "src/backtest_framework/validation/concentration.py",
         "src/backtest_framework/validation/hurdle_p.py")


def params() -> dict[str, Any]:
    return {"cell": CELL, "leg": LEG, "k": K, "stop_sigma_rem": STOP_MULT, "vault": [VAULT_FROM, VAULT_END],
            "load_from": LOAD_FROM, "overlap": list(OVERLAP), "known_trades": KNOWN["trades"],
            "gate": {"G0": f">= {MIN_TRADES} trades", "G1": f"mean net > 0 and one-sided NW({NW_LAGS}) t >= {T_GATE}",
                     "G2": "mean net > the vault-window C2a p95 (enumerated offsets 20 .. n-20)",
                     "FAIL": "mean net <= 0", "else": "UNRESOLVED"},
            "seed": SEED, "programme_family": PROGRAMME_FAMILY}


def manifest(root: Path) -> dict[str, Any]:
    imported = sorted(set(discover(root, (RUNNER_REL,) + EXTRA)) | set(EXTRA))
    return {"runner": {"path": RUNNER_REL, "sha256": sha_text(root / RUNNER_REL)},
            "records": {p: sha_text(root / p) for p in (SPEC_REL, D735_PRE_REL, D735_RES_REL)},
            "imported_unchanged": {p: sha_text(root / p) for p in imported},
            "files": {p.relative_to(root).as_posix(): sha_text(p) for p in (D735_JSON, REHEARSAL, POWER)},
            "params": params()}


def check_freeze(doc: dict[str, Any], root: Path = REPO) -> None:
    now = manifest(root)
    bad = [k for k in ("runner", "records", "files", "params") if now[k] != doc.get(k)]
    fi, ni = doc.get("imported_unchanged", {}), now["imported_unchanged"]
    if set(fi) != set(ni):
        bad.append(f"the import set (added {sorted(set(ni) - set(fi))}, dropped {sorted(set(fi) - set(ni))})")
    bad += [f"imported {p}" for p in sorted(set(fi) & set(ni)) if fi[p] != ni[p]]
    if bad:
        raise VaultError(f"moved since the freeze: {bad}")


def imported_repo_files() -> set[str]:
    out = set()
    for m in list(sys.modules.values()):
        f = getattr(m, "__file__", None)
        if not f:
            continue
        try:
            rel = Path(f).resolve().relative_to(REPO.resolve()).as_posix()
        except ValueError:
            continue
        if rel.startswith(("scripts/", "src/")) and rel.endswith(".py"):
            out.add(rel)
    return out


# ================================================================================ modes
def write_once(path: Path, doc: dict[str, Any]) -> None:
    with open(path, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(doc, fh, indent=1, default=Z._json)
        fh.write("\n")


def rehearse(data_root: Path) -> int:
    if REHEARSAL.exists():
        raise VaultError(f"{REHEARSAL.name} exists: the rehearsal is run-once")
    t0 = time.time()
    cst = cost()
    c = in_sample(data_root)
    ka = check_known(c, cst)
    # the vault loader's path, in-sample: its own window read and panel build, ending at 2023-12-29
    rows = {r: read_window(r, data_root, LOAD_FROM, IN_HI) for r in ("NQ", LEG)}
    cv = cell(T.panel_from_raw("NQ", rows["NQ"]), T.panel_from_raw(LEG, rows[LEG]))
    n_ov = overlap_check(c, cv)
    res = score(window(c, "2016-01-04", IN_HI), cst)
    doc = {"mode": "IN-SAMPLE REHEARSAL (2016-01-04 -> 2023-12-29): the vault scorer on the in-sample window",
           "spec": SPEC_REL, "known_answer": ka, "overlap_trades_reproduced": n_ov, "score": strip(res),
           "wall_s": round(time.time() - t0, 1)}
    write_once(REHEARSAL, doc)
    P(f"[D737] rehearsal: {ka}; overlap {n_ov} trades; in-sample gate {res['gate']}; t {res['nw_t']:.2f}")
    return 0


def do_power(data_root: Path) -> int:
    if POWER.exists():
        raise VaultError(f"{POWER.name} exists: the power run is run-once")
    t0 = time.time()
    cst = cost()
    c = in_sample(data_root)
    check_known(c, cst)
    pw = power(c, cst)
    pw["wall_s"] = round(time.time() - t0, 1)
    write_once(POWER, pw)
    P(f"[D737] power: { {k: round(v['pass_g1'], 3) for k, v in pw['g1_bootstrap'].items()} }; windows {pw['full_gate_windows']}")
    return 0


def freeze() -> int:
    if FROZEN.exists():
        raise VaultError(f"{FROZEN.name} exists: the freeze is written once")
    for p in (REHEARSAL, POWER):
        if not p.exists():
            raise VaultError(f"{p.name} is missing: run --rehearse and --power first")
    from backtest_framework.validation.programme import Registry
    reg = Registry()
    fam = reg.register(PROGRAMME_FAMILY, Path(SPEC_REL).name, registered_utc="2026-10-01",
                       note="Vault line: D735's YM k1.0 1 sigma_rem on NQ, one MNQ, $4.07, 2024-01-01 -> 2026-09-18; "
                            "PASS with >= 100 trades, mean net > 0 and one-sided NW(5) t >= 1.645, and mean net above "
                            "the vault-window timing null's p95; FAIL if mean net <= 0; else UNRESOLVED")
    reg.render_md()
    doc = {"name": "FROZEN_vault_d737_nq_leads_the_dow", "record": SPEC_REL, "instruction": INSTRUCTION,
           "programme_slot": fam.slot, "programme_family": fam.name, "alpha": fam.alpha, **manifest(REPO),
           "known_answer": {"trades": KNOWN["trades"], "mean_net": known_mean()}}
    write_once(FROZEN, doc)
    P(f"[D737] FROZEN; programme slot {fam.slot} ({fam.name}); {len(doc['imported_unchanged'])} imported files hashed")
    return 0


def refuse(word: str | None) -> bool:
    return not (word and word.strip())


def vault(word: str | None, data_root: Path, accept_end: str | None) -> int:
    if refuse(word):
        P("[D737] REFUSED: --vault needs --principals-word")
        return REFUSED
    if not FROZEN.exists():
        raise VaultError("no freeze: --vault runs only on a frozen line")
    doc = json.loads(FROZEN.read_text(encoding="utf-8"))
    check_freeze(doc)
    if OUT.exists():
        raise VaultError(f"{OUT.name} exists: the vault is opened once")
    t0 = time.time()
    cst = cost()
    c_in = in_sample(data_root)
    ka = check_known(c_in, cst)
    end = accept_end or VAULT_END
    cv = vault_load(data_root, end)
    n_ov = overlap_check(c_in, cv)                           # the vault load starts 2023-09-01: the overlap ties it in
    w = window(cv, VAULT_FROM, end)
    res = score(w, cst)
    daily = res.pop("_daily")
    rho = None
    if D716_VAULT_OUT.exists():
        rho = "D716's vault output exists; its daily series is not in an aggregate file, so rho is computed in the RESULT"
    extra = imported_repo_files() - set(doc["imported_unchanged"]) - {RUNNER_REL}
    out = {"mode": "VAULT", "spec": SPEC_REL, "principals_word": word, "accept_end": accept_end, "end": end,
           "known_answer_in_sample": ka, "overlap_trades_reproduced": n_ov, "score": strip(res),
           "verdict": res["gate"]["verdict"], "rho_with_d716": rho, "unhashed_imports_seen": sorted(extra),
           "by_year_net": res["book"]["net_by_year"], "daily_net_sum": float(np.sum(daily)),
           "wall_s": round(time.time() - t0, 1)}
    write_once(OUT, out)
    P(f"[D737] VAULT: {res['gate']}; trades {res['trades']}; mean net {res['mean_net']:.2f}; t {res['nw_t']:.2f}")
    return 0


# ================================================================================ self-test (synthetic only)
def selftest() -> int:
    fails: list[str] = []

    def expect(fn: Callable[[], Any], what: str, exc: type = VaultError) -> None:
        try:
            fn()
            fails.append(f"did not raise: {what}")
        except exc:
            pass

    # 1) the gate
    cases = [((560, 12.0, 2.1, 8.0), "PASS"), ((560, 12.0, 1.5, 8.0), "UNRESOLVED"), ((560, 12.0, 2.1, 14.0), "UNRESOLVED"),
             ((560, -1.0, -0.5, 8.0), "FAIL"), ((560, 0.0, 0.0, -1.0), "FAIL"), ((80, 30.0, 4.0, 8.0), "UNRESOLVED")]
    for args, want in cases:
        if gate(*args)["verdict"] != want:
            fails.append(f"gate{args} is not {want}")
    # 2) the seal: rows after the end never survive; a short fixture refuses
    b = pd.DataFrame({"day": ["2026-09-17", "2026-09-18", "2026-09-19", "2026-09-21"], "hhmm": "09:30"})
    if window_rows(b, LOAD_FROM, VAULT_END)["day"].max() != "2026-09-18":
        fails.append("the window filter let a row after 2026-09-18 through")
    expect(lambda: vault_load(Path("."), "2026-09-19"), "a vault load past 2026-09-18")
    # 3) refusal without a word, before anything is read
    if vault(None, Path("."), None) != REFUSED or vault("  ", Path("."), None) != REFUSED:
        fails.append("--vault without the principal's word did not refuse with 2")
    # 4) the scorer on a synthetic two-root world (dates in the vault's span), with NQ leading: C2b's offset 0 holds
    rng = np.random.default_rng(1)
    nd = 260
    days = pd.bdate_range("2024-01-02", periods=nd).strftime("%Y-%m-%d").to_numpy()
    f = np.cumsum(rng.normal(0, 0.6, (nd, S.NMIN)), axis=1)
    i = np.cumsum(rng.normal(0, 0.4, (nd, S.NMIN)), axis=1)
    i += np.linspace(0, 1, S.NMIN)[None, :] * np.sign(i[:, [40]]) * 6.0      # NQ's own part continues
    C = 15000 + f + i
    Op = np.column_stack([C[:, 0], C[:, :-1]])
    pp = {"Op": Op, "H": np.maximum(Op, C) + 0.5, "L": np.minimum(Op, C) - 0.5, "C": C, "O": Op[:, 0].copy(),
          "soc": np.full(nd, 60.0)}
    XN = S.minute_x(C, pp["O"], pp["soc"])
    Y = 35000 + 2.0 * f + np.cumsum(rng.normal(0, 0.5, (nd, S.NMIN)), axis=1)
    XL = S.minute_x(Y, Y[:, 0], np.full(nd, 150.0))
    sp = S.spread(XN, XL)
    m0, D = S.trigger(sp["Z"], sp["S"], K)
    G = S.e1_tables(pp, STOP_MULT)
    d = np.flatnonzero(m0 >= 0)
    c = {"days": days, "pp": pp, "XN": XN, "XL": XL, "sp": sp, "m0": m0, "D": D, "G": G, "d": d, "g": S.g_at(G, d, m0[d], D[d])}
    try:
        res = score(window(c, days[30], days[-1]), 4.07)
        if res["trades"] < 100:
            fails.append(f"the synthetic world produced only {res['trades']} trades")
        if not res["mean_net"] > 0:
            fails.append("a planted NQ lead did not pay in the scorer")
    except VaultError as e:
        fails.append(f"the scorer raised on a synthetic world: {e}")
    # 5) the overlap comparator fires on a perturbed trade
    c2 = dict(c)
    c2["days"] = np.where(days >= days[0], np.array([f"2023-{11 + (k // 22) % 2:02d}-{1 + k % 22:02d}" for k in range(nd)]), days)
    c3 = dict(c2)
    g3 = c2["g"].copy()
    g3[0] += 1.0
    c3["g"] = g3
    try:
        overlap_check(c2, c2)
    except VaultError:
        fails.append("the overlap check raised on identical loads")
    expect(lambda: overlap_check(c2, c3), "a perturbed overlap trade")
    # 6) the freeze detects drift: a changed parameter
    doc = manifest(REPO) if REHEARSAL.exists() and POWER.exists() else None
    if doc is not None:
        doc2 = json.loads(json.dumps(doc))
        doc2["params"]["k"] = 1.5
        expect(lambda: check_freeze(doc2), "a moved parameter")
        doc3 = json.loads(json.dumps(doc))
        k0 = next(iter(doc3["imported_unchanged"]))
        doc3["imported_unchanged"][k0] = "0" * 64
        expect(lambda: check_freeze(doc3), "a moved imported file")
    if fails:
        P("SELFTEST FAILED:", fails)
        return 1
    P("SELFTEST OK: the gate's five readings; the seal filter and the past-end refusal; --vault refuses without a word "
      "(2); the scorer pays on a planted lead and C2b's offset 0 reproduces; the overlap check fires on a perturbed "
      "trade" + ("; the freeze check fires on a moved parameter and a moved import" if doc is not None else
                 " (the freeze-drift check runs once the rehearsal and power files exist)"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--rehearse", action="store_true")
    ap.add_argument("--power", action="store_true")
    ap.add_argument("--freeze", action="store_true")
    ap.add_argument("--vault", action="store_true")
    ap.add_argument("--principals-word")
    ap.add_argument("--accept-end")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    if a.rehearse:
        return rehearse(a.data_root)
    if a.power:
        return do_power(a.data_root)
    if a.freeze:
        return freeze()
    if a.vault:
        return vault(a.principals_word, a.data_root, a.accept_end)
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
