"""D729: the volatility-unit year-concentration report, applied in-sample to the four vault-queued lines (D716 NQ F2,
D680 NQ compression C1, D723 NG Stage A, D649 NG projected-profit MNG) and to D722's reference lines. INFORMATIONAL:
it binds nothing. As declared in docs/decisions/D729-METHOD-the-volatility-unit-year-concentration-report.md (ca6aa49f).

    uv run python scripts/report_d729_vol_unit_concentration.py --selftest
    uv run python scripts/report_d729_vol_unit_concentration.py --run      # run-once: refuses if the output exists

Per trade: r = the trade's return (gross $ / ($ per point x price), or bp / 1e4); scale = sigma20, the front
contract's same-contract daily settlement log-return sd over the 20 settling sessions before the session (>= 15).
Each line is read only through its own in-sample function; settlements are read below each root's limit (NQ and NG
2025-03-01, ES and HO 2024-01-01). Writes data/report_d729_vol_unit_concentration.json (aggregates only).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))
from backtest_framework.validation.concentration import year_concentration  # noqa: E402

STRIP = REPO / "data" / "fixtures" / "fut_settle_strip.csv.gz"
FRONT = REPO / "data" / "fixtures" / "fut_curve_front_next.csv.gz"
OUT_V1 = REPO / "data" / "report_d729_vol_unit_concentration.json"    # v1: superseded, kept as evidence (see the record)
OUT = REPO / "data" / "report_d729_vol_unit_concentration_v2.json"
LIMIT = {"NQ": "2025-03-01", "NG": "2025-03-01", "ES": "2024-01-01", "HO": "2024-01-01"}
WIN, MINP = 20, 15
NG_USD_PP = 10_000.0        # one full NG contract: 10,000 MMBtu, $ per $1/MMBtu


class D729Error(AssertionError):
    pass


def need(c: bool, msg: str) -> None:
    if not c:
        raise D729Error(msg)


# ------------------------------------------------------------------------------------------------ the scale
def read_root(root: str, plant: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Front per ref and the root's strip, both filtered below the root's limit as they are read."""
    lim = LIMIT[root]
    fr = [c[(c["root"] == root) & (c["ref"] < lim)][["ref", "front", "front_settle"]]
          for c in pd.read_csv(FRONT, usecols=["root", "ref", "front", "front_settle"], dtype={"ref": str, "front": str},
                               chunksize=1_000_000, encoding="utf-8")]
    st = [c[(c["root"] == root) & (c["ref"] < lim)][["contract", "ref", "settle"]]
          for c in pd.read_csv(STRIP, usecols=["root", "contract", "ref", "settle"], dtype={"ref": str, "contract": str},
                               chunksize=2_000_000, encoding="utf-8")]
    f, s = pd.concat(fr, ignore_index=True), pd.concat(st, ignore_index=True)
    if plant:
        f = pd.concat([f, f.iloc[[-1]].assign(ref=lim)], ignore_index=True)
    need(not (f["ref"] >= lim).any() and not (s["ref"] >= lim).any(), f"[SEAL] {root}: a settlement dated >= {lim}")
    f = f.dropna(subset=["front", "front_settle"])
    f = f[f["front_settle"] > 0].sort_values("ref").reset_index(drop=True)
    s = s[s["settle"] > 0]
    return f, s


def scale_table(root: str, plant: bool = False, same_day: bool = False) -> pd.DataFrame:
    """Per settling ref: the front's same-contract log return from the previous settling ref, then sigma20 and the
    front settlement as known at the NEXT session (shifted one ref)."""
    f, s = read_root(root, plant)
    px = s.set_index(["contract", "ref"])["settle"]
    refs = f["ref"].to_numpy()
    prev = np.r_[[None], refs[:-1]]
    p0 = px.reindex(list(zip(f["front"], prev))).to_numpy(float)
    ret = np.log(f["front_settle"].to_numpy(float) / p0)
    t = pd.DataFrame({"ref": refs, "ret": ret, "settle": f["front_settle"].to_numpy(float)})
    sd = t["ret"].rolling(WIN, min_periods=MINP).std()
    t["sigma20_known_after"] = sd
    k = 0 if same_day else 1
    t["sigma20"] = sd.shift(k)          # the value usable on the session after `ref`
    t["p_prev"] = t["settle"].shift(k)
    return t


def lookup(t: pd.DataFrame, sessions) -> tuple[np.ndarray, np.ndarray]:
    """For each session: the last row of t with ref < session, then its sigma20/p_prev shifted to that next session.
    Implemented as: the row of the first ref >= session carries the values known before it."""
    refs = t["ref"].to_numpy()
    sess = np.asarray(sessions, dtype=str)
    i = np.searchsorted(refs, sess, side="left")
    need((i < len(refs)).all(), "[SCALE] a session beyond the root's settlements")
    # t's shifted columns at row i hold the values from row i-1, i.e. the last ref strictly before refs[i];
    # if the session is itself a settling ref, refs[i] == session and row i-1 is the prior ref: correct.
    # if the session is not a ref (holiday mismatch), refs[i] > session and row i-1 is still the last ref < session.
    return t["sigma20"].to_numpy()[i], t["p_prev"].to_numpy()[i]


def lookup_loop(t: pd.DataFrame, sessions) -> np.ndarray:
    """Second implementation of sigma20 by plain loop over returns strictly before the session (never calls lookup)."""
    refs, ret = list(t["ref"]), list(t["ret"])
    out = []
    for d in sessions:
        r = [x for rf, x in zip(refs, ret) if rf < d]
        w = [x for x in r[-WIN:] if np.isfinite(x)]
        out.append(float(np.std(w, ddof=1)) if len(w) >= MINP else float("nan"))
    return np.array(out)


# ------------------------------------------------------------------------------------------------ the lines
def d722_lines() -> pd.DataFrame:
    import diag_d722_lines as DL
    return DL.load_lines()


def rows_d722(df: pd.DataFrame, line: str) -> tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """(sessions, gross $, $ per unit return = usd_pp x entry price, root)."""
    x = df[df["line"] == line]
    mult = x["usd_pp"].to_numpy(float) * x["entry_price"].to_numpy(float)
    return x["session"].to_numpy(str), x["gross_usd"].to_numpy(float), mult, str(x["root"].iloc[0])


def rows_d680() -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    import vault_d680_nq_compression as V
    tr, _sessions, _R = V.in_sample()
    ka = V.known_answer(tr)
    win = np.isfinite(tr["t671"].to_numpy(float)) & np.isfinite(tr["ctier"].to_numpy(float))
    c1 = win & (tr["ctier"].to_numpy(float) < 1 / 3)
    need(int(c1.sum()) == ka["trades"], "[D680] the C1 mask differs from the known answer's")
    x = tr[c1]
    need((x["session"].astype(str) < "2025-03-01").all(), "[SEAL] D680 holds a vault session")
    mult = 2.0 * x["entry"].to_numpy(float)                 # one MNQ: $2 a point, so $ per unit return = 2 x price
    return x["session"].astype(str).to_numpy(), x["gross"].to_numpy(float) / 1e4 * mult, mult, ka


def ng_table() -> tuple[pd.DataFrame, dict]:
    import vault_d723_ng_stage_a as V
    tab, _d = V.in_sample()
    got = V.answer(tab)
    V.check_known(got)
    need((tab["day"] < "2025-03-01").all(), "[SEAL] the NG table holds a vault day")
    return tab, got


def rows_d723(tab: pd.DataFrame, P: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    m = tab["traded"].to_numpy()
    return tab["day"].to_numpy(str)[m], tab["g"].to_numpy(float)[m], NG_USD_PP * P[m]


def rows_d649(tab: pd.DataFrame, P: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray, dict]:
    import ledger_vault_pp_ng as L
    t = L.in_sample()
    ka = L.known_answer(t)
    need(t["day"].tolist() == tab["day"].tolist() and np.array_equal(t["g"].to_numpy(), tab["g"].to_numpy()),
         "[D649] D649's in-sample table differs from D723's")
    take = L.select(np.array([]), np.array([]), t["traded"].to_numpy(), t["absI_usd"].to_numpy(), t["g"].to_numpy())
    need(int(take.sum()) == ka["trades"], "[D649] the take count differs from the known answer")
    return t["day"].to_numpy(str)[take], t["g"].to_numpy(float)[take], NG_USD_PP * P[take], ka


# ------------------------------------------------------------------------------------------------ run
def report(sessions, g_usd, mult, sig) -> dict:
    """The declared report: gross in DOLLARS against the dollar scale mult x sigma20 (so u = r / sigma20). The
    return-unit shares (gross / mult: the price level removed, the volatility not) are reported beside."""
    sc = mult * sig
    ok = np.isfinite(g_usd) & np.isfinite(sc) & (sc > 0)
    rep = year_concentration(sessions[ok], g_usd[ok], sc[ok])
    rep["return_units_beside"] = year_concentration(sessions[ok], g_usd[ok] / mult[ok])
    rep["n_without_scale"] = int((~ok).sum())
    rep["mean_gross_usd"] = float(np.mean(g_usd[ok]))
    return rep


def study() -> dict:
    t0 = time.time()
    tables = {root: scale_table(root) for root in ("NQ", "NG", "ES", "HO")}
    out = {"spec": "docs/decisions/D729-METHOD-the-volatility-unit-year-concentration-report.md (ca6aa49f)",
           "informational": True, "scale": f"sigma20: same-contract front settlement log returns, {WIN} settling sessions "
                                             f"before the session (>= {MINP})", "queued": {}, "reference": {}}
    df = d722_lines()
    s, g, mult, root = rows_d722(df, "L2")
    sig, _ = lookup(tables[root], s)
    out["queued"]["D716 NQ F2 book B (slot 7)"] = report(s, g, mult, sig)
    s, g, mult, ka = rows_d680()
    sig, _ = lookup(tables["NQ"], s)
    out["queued"]["D680 NQ compression C1 (slot 9)"] = {**report(s, g, mult, sig), "known_answer": ka}
    tab, got = ng_table()
    sig_all, p_all = lookup(tables["NG"], tab["day"].to_numpy(str))
    s, g, mult = rows_d723(tab, p_all)
    sig = lookup(tables["NG"], s)[0]
    out["queued"]["D723 NG Stage A (slot 3)"] = {**report(s, g, mult, sig), "known_answer": got}
    s, g, mult, ka = rows_d649(tab, p_all)
    sig = lookup(tables["NG"], s)[0]
    out["queued"]["D649 NG projected-profit MNG (slot 8)"] = {**report(s, g, mult, sig), "known_answer": ka}
    for line, name in (("L1", "ES F2 (D707, withdrawn)"), ("L3", "D699 V1 (closed)"), ("L4", "HO F2 (D719, closed)"),
                       ("K1", "the MACD arm (admitted)")):
        s, g, mult, root = rows_d722(df, line)
        sig, _ = lookup(tables[root], s)
        out["reference"][name] = report(s, g, mult, sig)
    out["wall_s"] = round(time.time() - t0, 1)
    return out


def jsonable(o):
    if isinstance(o, dict):
        return {str(k): jsonable(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [jsonable(v) for v in o]
    if isinstance(o, (np.floating, float)):
        return None if not math.isfinite(float(o)) else float(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.bool_):
        return bool(o)
    return o


def run() -> int:
    need(not OUT.exists(), f"[RUN] {OUT.name} exists: --run is run-once")
    res = study()
    with open(OUT, "x", encoding="utf-8", newline="\n") as fh:
        json.dump(jsonable(res), fh, indent=1)
        fh.write("\n")
    for grp in ("queued", "reference"):
        for name, rep in res[grp].items():
            g, u = rep["gross"], rep["vol_units"]
            gs = "undefined" if g["max_share"] is None else f"{g['max_year']} {g['max_share']:.0%}"
            us = "undefined" if u["max_share"] is None else f"{u['max_year']} {u['max_share']:.0%}"
            rr = rep["return_units_beside"]["gross"]
            rs = "undefined" if rr["max_share"] is None else f"{rr['max_year']} {rr['max_share']:.0%}"
            print(f"{grp:9s} {name:42s} n {rep['n']:5d}  $: {gs:14s} ret: {rs:14s} vol: {us:14s} {rep['label']}"
                  f"  (no scale {rep['n_without_scale']})")
    print(f"wrote {OUT.relative_to(REPO)} in {res['wall_s']} s")
    return 0


def selftest() -> int:
    t0 = time.time()
    fired = []

    def expect(fn, what):
        try:
            fn()
        except D729Error as e:
            print(f"  RAISES  {what}: {str(e)[:120]}")
            fired.append(what)
            return
        raise SystemExit(f"SELFTEST FAILED: did not raise: {what}")

    expect(lambda: read_root("NQ", plant=True), "seal: a planted settlement at the root's limit")
    t = scale_table("NQ")
    sess = sorted(t["ref"].iloc[100::97].tolist())[:40] + ["2019-07-04", "2020-12-25"]    # refs and two non-refs
    a, _ = lookup(t, sess)
    b = lookup_loop(t, sess)
    need(np.allclose(a, b, rtol=1e-12, atol=0, equal_nan=True), "[LAG] lookup disagrees with the loop")
    print(f"  PASS    sigma20 lookup == loop on {len(sess)} sessions (incl. 2 non-settlement days)")
    ts = scale_table("NQ", same_day=True)
    expect(lambda: need(np.allclose(lookup(ts, sess)[0], b, rtol=1e-12, atol=0, equal_nan=True),
                        "[LAG] a same-day sigma20 disagrees with the loop"), "lag: sigma20 including the session itself")
    need(int((t["ret"].abs() > 0.5).sum()) == 0, "[SCALE] a |return| > 50 %: a roll leaked into the returns")
    print("  PASS    no roll-sized return in NQ's same-contract series")
    print(f"SELFTEST PASS: {len(fired)} canaries raised; {time.time() - t0:.1f} s")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--selftest", action="store_true")
    g.add_argument("--run", action="store_true")
    a = ap.parse_args()
    return selftest() if a.selftest else run()


if __name__ == "__main__":
    sys.exit(main())
