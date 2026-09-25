"""D625: does the TAS price say which way the settlement flow went?

The spec is `docs/decisions/D625-PRE-REG-the-TAS-premium-as-a-signed-stand-in-for-window-flow.md`, committed alone
in `158b2d2` before this file existed. D624's runner (`validate_flow_estimate.py`) supplies the loaders, K1, the
truth (int64-cast, on ts_recv) and the NG/CL traded-contract rule, so both studies share one tested
implementation.

    python -W error::RuntimeWarning scripts/validate_tas_premium.py --siblings   # §5 steps 1-2 on HO/RB, with K1, C1, C2
    python -W error::RuntimeWarning scripts/validate_tas_premium.py --gate       # §5 step 3 on CL/NG, once, after the top-up
    python scripts/validate_tas_premium.py --check | --selftest

It uses the SYSTEM interpreter (databento).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "data" / "ledger_tas_premium_validation.json"
SIB_TAS_JOBS = REPO / "data" / "ledger_sibling_tas_pull_jobs.json"
TAUS = ("13:50:00", "14:00:00", "14:10:00")
TAU_GATE = "14:10:00"
BAR, NEAR_MISS, MIN_SESSIONS, TIE, CTRL_MAX = 0.70, 0.65, 15, 0.01, 0.60
SEED = 625
MEASURES = ("T1", "T2", "T3")
RE_TAS = re.compile(r"^(HOT|RBT|CLT|NGT)([FGHJKMNQUVXZ])(\d{1,2})$")
#: Changes made after the first run. None yet.
DEVIATIONS: list[str] = []


def _load_v() -> Any:
    name = "validate_flow_estimate"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    m = importlib.util.module_from_spec(spec)
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


V = _load_v()


class D625Error(RuntimeError):
    pass


# ------------------------------------------------------------------ data
CACHE = REPO / "temp" / "d625_cache"


def cached_load(files: list[Path], pattern: re.Pattern[str], t_from: str, t_to: str) -> pd.DataFrame:
    """V.load, cached in temp/ and keyed on every source file's name, size and mtime and on the arguments, so a
    changed or re-downloaded file can never be served stale. It is only a cache: deleting temp/ loses nothing."""
    import hashlib
    key = hashlib.sha256(json.dumps([[f.name, f.stat().st_size, f.stat().st_mtime_ns] for f in files]
                                    + [pattern.pattern, t_from, t_to]).encode()).hexdigest()[:24]
    path = CACHE / f"{key}.pkl"
    if path.exists():
        return pd.read_pickle(path)
    df = V.load(files, pattern, t_from, t_to)
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_pickle(path)
    return df


def tas_span(files: list[Path], t_to: str) -> pd.DataFrame:
    """TAS rows from the session open (18:00 ET the evening before, re-dated to the session) to t_to."""
    eve = cached_load(files, RE_TAS, "18:00:00", "24:00:00")
    eve["day"] = (pd.to_datetime(eve["day"]) + pd.Timedelta(days=1)).dt.strftime("%Y-%m-%d")
    return pd.concat([eve, cached_load(files, RE_TAS, "00:00:00", t_to)]).reset_index(drop=True)


def k1_tas(bars: pd.DataFrame, trades: pd.DataFrame) -> dict[str, Any]:
    """D625 §6: TAS bar volume equals summed trade size, per contract-second, over the whole span."""
    b = bars.groupby(["symbol", "sec"])["volume"].sum()
    t = trades.groupby(["symbol", "sec"])["size"].sum()
    j = pd.concat([b.rename("bar"), t.rename("trade")], axis=1).fillna(0)
    ok = float((j["bar"] == j["trade"]).mean())
    out = {"seconds": int(len(j)), "share_equal": round(ok, 6), "bar_volume": int(j["bar"].sum()),
           "trade_volume": int(j["trade"].sum())}
    if ok < 0.999:
        raise D625Error(f"K1 (TAS) failed: {ok:.4%} of seconds equal {out}")
    return out


# ------------------------------------------------------------------ measures (§2)
def measures(tb: pd.DataFrame) -> dict[str, float]:
    """T1, T2, T3 on ONE TAS contract's bars in time order."""
    c = tb["close"].to_numpy(float)
    v = tb["volume"].to_numpy(float)
    if v.sum() == 0:
        return {m: 0.0 for m in MEASURES}
    t3, _fb = V.estimate(tb, "E1")
    return {"T1": float((c * v).sum() / v.sum()), "T2": float((v * np.sign(c)).sum()), "T3": float(t3.sum())}


def _ym_key(sym: str, day: str) -> tuple[int, int]:
    return V._ym(sym[:2] + sym[3:], day)  # HOTX6 -> HOX6: the TAS month is the outright month


# ------------------------------------------------------------------ per session
def sessions(out_bars: pd.DataFrame, out_trades: pd.DataFrame, tas_bars: pd.DataFrame, tas_trades: pd.DataFrame,
             root: str, rule: str) -> pd.DataFrame:
    rows = []
    ob = out_bars[out_bars["symbol"].str[:2] == root]
    ot = out_trades[out_trades["symbol"].str[:2] == root]
    tbr = tas_bars[tas_bars["symbol"].str[:2] == root]
    ttr = tas_trades[tas_trades["symbol"].str[:2] == root]
    for day, bd in ob.groupby("day"):
        win = bd[(bd["clock"] >= V.W0) & (bd["clock"] < V.W1)]
        if win.empty:
            continue
        if rule == "most_active":
            sym = str(win.groupby("symbol")["volume"].sum().idxmax())
        else:
            want = V.traded_contract_rule(root, str(day))
            cand = [s for s in win["symbol"].unique() if V._ym(str(s), str(day)) == want]
            if not cand:
                continue
            sym = str(cand[0])
        ym = V._ym(sym, str(day))
        td = ot[(ot["day"] == day) & (ot["symbol"] == sym)]
        tw = td[(td["clock"] >= V.W0) & (td["clock"] < V.W1)]
        if len(tw) < V.MIN_TRUE_TRADES:
            rows.append({"day": day, "excluded": f"{len(tw)} true trades in the window"})
            continue
        tsyms = [s for s in tbr.loc[tbr["day"] == day, "symbol"].unique() if _ym_key(str(s), str(day)) == ym]
        if not tsyms:
            rows.append({"day": day, "excluded": f"no TAS bar for {sym}'s month"})
            continue
        tsym = str(tsyms[0])
        tb = tbr[(tbr["day"] == day) & (tbr["symbol"] == tsym)].sort_values("sec")
        tt = ttr[(ttr["day"] == day) & (ttr["symbol"] == tsym)]
        row: dict[str, Any] = {"day": day, "symbol": sym, "tas": tsym, "truth_W": V.truth(tw),
                               "tas_truth_W": V.truth(tt)}
        for m, x in measures(tb).items():
            row[f"W_{m}"] = x
        for tau in TAUS:
            k = tau[:5]
            row[f"truth_P_{k}"] = V.truth(td[(td["clock"] >= V.PRE_FROM) & (td["clock"] < tau)])
            pre = tb[(tb["clock"] < tau) | (tb["clock"] >= "18:00:00")]
            for m, x in measures(pre).items():
                row[f"P{k}_{m}"] = x
        rows.append(row)
    return pd.DataFrame(rows)


def _usable(df: pd.DataFrame) -> pd.DataFrame:
    return df[df["excluded"].isna()] if "excluded" in df.columns else df


def agreement(meas: pd.Series, truth: pd.Series) -> dict[str, Any]:
    """§3: zero measure = miss; zero truth dropped and counted."""
    keep = truth != 0
    m, t = meas[keep], truth[keep]
    n = int(len(m))
    if n == 0:
        return {"n": 0, "agreement": None}
    hit = (np.sign(m) == np.sign(t)) & (m != 0)
    abst = int((m == 0).sum())
    nz = m != 0
    r = float(np.corrcoef(m, t)[0, 1]) if n >= 4 and m.std() > 0 and t.std() > 0 else None
    return {"n": n, "agreement": round(float(hit.mean()), 4), "truth_zero_dropped": int((~keep).sum()),
            "abstentions": abst, "agreement_excl_abstentions": round(float(hit[nz].mean()), 4) if nz.any() else None,
            "pearson_r": None if r is None else round(r, 4)}


def _roles(df: pd.DataFrame) -> dict[str, tuple[str, str]]:
    """role -> (measure column prefix, truth column)."""
    k = TAU_GATE[:5]
    return {"W": ("W_", "truth_W"), "P": (f"P{k}_", f"truth_P_{k}")}


def _verdict(x: float | None, n: int, agree: bool) -> str:
    if x is None or n < MIN_SESSIONS:
        return "UNRESOLVED (fewer than 15 usable sessions)"
    if not agree:
        return "NOT USED (siblings did not agree)"
    if x >= BAR:
        return "PASS"
    return "UNRESOLVED (near miss)" if x >= NEAR_MISS else "FAIL"


# ------------------------------------------------------------------ phases
def _sibling_frames() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ot = cached_load(V._files(V.SIB_JOBS, "siblings-trades"), V.RE_OUT, V.PRE_FROM, V.W1)
    ob = cached_load(V._files(V.SIB_JOBS, "siblings-ohlcv1s"), V.RE_OUT, V.W0, V.W1)
    tt = tas_span(V._files(SIB_TAS_JOBS, "siblings-tas-trades"), V.W1)
    tb = tas_span(V._files(SIB_TAS_JOBS, "siblings-tas-ohlcv1s"), V.W1)
    return ot, ob, tt, tb


def kappa(meas: pd.Series, truth: pd.Series) -> dict[str, Any]:
    """Cohen's kappa of sign(meas) against sign(truth). Truth zeros are dropped; a zero measure is its own category,
    and so is always a miss."""
    keep = truth != 0
    m, t = np.sign(meas[keep]), np.sign(truth[keep])
    n = int(len(m))
    if n == 0:
        return {"n": 0, "kappa": None}
    po = float(((m == t) & (m != 0)).mean())
    pe = float((m > 0).mean() * (t > 0).mean() + (m < 0).mean() * (t < 0).mean())
    k = (po - pe) / (1 - pe) if pe < 1 else None
    return {"n": n, "agreement": round(po, 4), "chance": round(pe, 4), "kappa": None if k is None else round(k, 4),
            "truth_plus_share": round(float((t > 0).mean()), 4), "measure_plus_share": round(float((m > 0).mean()), 4),
            "measure_zero_share": round(float((m == 0).mean()), 4)}


def diagnose() -> dict[str, Any]:
    """POST HOC, written after C1 fired on the first sibling run (2026-09-25). This is not D625's statistic and it
    never replaces a verdict. Per root, half, role and measure: the sign base rates, the raw agreement, the chance
    agreement from the base rates, and Cohen's kappa, for the pre-registered sign (+) AND the reversed sign (-). The
    reversed sign is reported because the first inspection saw it. It is the hypothesis that D626 tests on data
    D625 never read."""
    ot, ob, tt, tb = _sibling_frames()
    out: dict[str, Any] = {"note": diagnose.__doc__}
    for root in ("HO", "RB"):
        df = _usable(sessions(ob, ot, tb, tt, root, "most_active").assign(excluded=lambda d: d.get("excluded")))
        for half, (a, b) in (("first", V.FIRST_HALF), ("second", V.SECOND_HALF)):
            h = df[(df["day"] >= a) & (df["day"] <= b)]
            for role, (pfx, tcol) in _roles(h).items():
                for m in MEASURES:
                    out.setdefault(root, {}).setdefault(half, {}).setdefault(role, {})[m] = {
                        "pre_registered_sign": kappa(h[pfx + m], h[tcol]),
                        "reversed_sign": kappa(-h[pfx + m], h[tcol])}
    return out


def siblings() -> dict[str, Any]:
    ot, ob, tt, tb = _sibling_frames()
    out: dict[str, Any] = {"k1_tas": k1_tas(tb, tt)}
    per = {root: sessions(ob, ot, tb, tt, root, "most_active") for root in ("HO", "RB")}
    for root in per:
        if "excluded" not in per[root].columns:
            per[root]["excluded"] = None
    half = {h: {r: _usable(per[r][(per[r]["day"] >= a) & (per[r]["day"] <= b)]) for r in per}
            for h, (a, b) in (("first", V.FIRST_HALF), ("second", V.SECOND_HALF))}
    rng = np.random.default_rng(SEED)
    for role, (pfx, tcol) in _roles(per["HO"]).items():
        sel = {m: {r: agreement(half["first"][r][pfx + m], half["first"][r][tcol]) for r in per} for m in MEASURES}
        mean = {m: float(np.mean([sel[m][r]["agreement"] for r in per])) for m in MEASURES}
        top = max(mean.values())
        chosen = next(m for m in MEASURES if mean[m] >= top - TIE)
        agree = {r: agreement(half["second"][r][pfx + chosen], half["second"][r][tcol]) for r in per}
        verdicts = {r: _verdict(agree[r]["agreement"], MIN_SESSIONS, True) for r in per}
        agrees = all(v == "PASS" for v in verdicts.values())
        controls = {}
        for r in per:
            u = half["second"][r].reset_index(drop=True)
            shifted = agreement(u[pfx + chosen].iloc[:-1].reset_index(drop=True), u[tcol].iloc[1:].reset_index(drop=True))
            rand = agreement(pd.Series(rng.choice([-1.0, 1.0], size=len(u))), u[tcol])
            if shifted["agreement"] is None or shifted["agreement"] > CTRL_MAX:
                raise D625Error(f"C1 failed ({role}, {r}): day-shifted agreement {shifted['agreement']}")
            if rand["agreement"] is None or rand["agreement"] > CTRL_MAX:
                raise D625Error(f"C2 failed ({role}, {r}): random-sign agreement {rand['agreement']}")
            controls[r] = {"c1_day_shift": shifted, "c2_random_sign": rand}
        extra: dict[str, Any] = {}
        if role == "W":
            extra["vs_true_tas_flow"] = {r: agreement(half["second"][r][pfx + chosen], half["second"][r]["tas_truth_W"])
                                         for r in per}
        else:
            extra["other_taus"] = {tau[:5]: {r: agreement(half["second"][r][f"P{tau[:5]}_{chosen}"],
                                                          half["second"][r][f"truth_P_{tau[:5]}"]) for r in per}
                                   for tau in TAUS if tau != TAU_GATE}
        out[role] = {"selection_first_half": {"per_measure": sel, "mean": {m: round(x, 4) for m, x in mean.items()},
                                              "chosen": chosen},
                     "agreement_second_half": agree, "sibling_verdicts": verdicts, "siblings_agree": bool(agrees),
                     "controls": controls, **extra,
                     "all_measures_second_half_for_the_record": {m: {r: agreement(half["second"][r][pfx + m],
                                                                                 half["second"][r][tcol])
                                                                     for r in per} for m in MEASURES}}
    out["sessions"] = {r: {"usable": int(len(_usable(per[r]))),
                           "excluded": per[r][per[r]["excluded"].notna()][["day", "excluded"]].to_dict("records")}
                       for r in per}
    return out


def gate() -> dict[str, Any]:
    if not V.TOPUP_JOBS.exists():
        raise D625Error(f"{V.TOPUP_JOBS.name} is absent: the gate is read once, after the top-up")
    doc = json.loads(OUT.read_text(encoding="utf-8"))
    sib = doc.get("siblings")
    if not sib:
        raise D625Error("the sibling phase must run first")
    tr_files = V._files(V.FREE_JOBS, "trades-post-vault") + V._files(V.TOPUP_JOBS, "topup-trades")
    bar_files = V._files(V.TOPUP_JOBS, "topup-ohlcv1s")
    ot = V.load(tr_files, V.RE_OUT, V.PRE_FROM, V.W1)
    ob = V.load(bar_files, V.RE_OUT, V.W0, V.W1)
    tt, tb = tas_span(tr_files, V.W1), tas_span(bar_files, V.W1)
    for df in (ot, ob):
        V.vault_guard(df, ("CL", "NG"))
    for df in (tt, tb):
        V.vault_guard(df.assign(symbol=df["symbol"].str[:2]), ("CL", "NG"))
    out: dict[str, Any] = {"k1_tas": k1_tas(tb, tt), "roots": {}}
    for root in ("CL", "NG"):
        df = sessions(ob, ot, tb, tt, root, "rule")
        u = _usable(df) if "excluded" in df.columns else df
        res: dict[str, Any] = {}
        for role, (pfx, tcol) in _roles(df).items():
            chosen = sib[role]["selection_first_half"]["chosen"]
            a = agreement(u[pfx + chosen], u[tcol]) if len(u) else {"n": 0, "agreement": None}
            res[role] = {"measure": chosen, **a,
                         "verdict": _verdict(a["agreement"], a["n"], sib[role]["siblings_agree"])}
        out["roots"][root] = {**res, "sessions": df.to_dict("records")}
    return out


def selftest() -> None:
    tb = pd.DataFrame({"close": [0.0, 1.0, 1.0, -1.0], "open": [0.0, 1.0, 1.0, -1.0], "volume": [10, 5, 5, 4],
                       "clock": ["14:00:00", "14:00:01", "14:00:02", "14:00:03"]})
    m = measures(tb)
    if not (abs(m["T1"] - (5 + 5 - 4) / 24) < 1e-12 and m["T2"] == 6.0 and m["T3"] == 6.0):
        raise D625Error(f"selftest: measures gave {m}")
    a = agreement(pd.Series([1.0, -2.0, 0.0, 3.0]), pd.Series([5.0, -1.0, 2.0, 0.0]))
    if a["n"] != 3 or a["agreement"] != round(2 / 3, 4) or a["abstentions"] != 1 or a["truth_zero_dropped"] != 1:
        raise D625Error(f"selftest: agreement gave {a}")
    if _ym_key("HOTX6", "2026-09-22") != (2026, 11):
        raise D625Error("selftest: TAS month mapping wrong")
    bars = pd.DataFrame({"symbol": "HOTX6", "sec": [1, 2], "volume": [3, 4]})
    try:
        k1_tas(bars, pd.DataFrame({"symbol": "HOTX6", "sec": [1, 3], "size": [3, 4]}))
    except D625Error:
        pass
    else:
        raise D625Error("selftest: K1 (TAS) did not fire on misaligned seconds")
    print("[selftest] T1/T2/T3 and sign agreement give their known answers; zero is a miss; K1 fires")


def _dump(doc: dict[str, Any]) -> str:
    return json.dumps(doc, indent=1, sort_keys=True, default=str) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    for f in ("--siblings", "--gate", "--check", "--selftest", "--diagnose"):
        ap.add_argument(f, action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        selftest()
        return 0
    if a.diagnose:
        d = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
            "spec": "D625; docs/decisions/D625-PRE-REG-the-TAS-premium-as-a-signed-stand-in-for-window-flow.md (158b2d2)"}
        d["post_hoc_diagnostic"] = diagnose()
        try:
            siblings()
        except D625Error as exc:  # the pre-registered path, unchanged; its raise is the recorded outcome
            d["siblings_preregistered_outcome"] = f"RAISED: {exc}"
        d["deviations"] = DEVIATIONS
        OUT.write_text(_dump(d), encoding="utf-8", newline="\n")
        for root in ("HO", "RB"):
            for half in ("first", "second"):
                x = d["post_hoc_diagnostic"][root][half]["W"]["T1"]
                print(root, half, "W T1: + sign", x["pre_registered_sign"], "| reversed", x["reversed_sign"])
        print("pre-registered sibling phase:", d.get("siblings_preregistered_outcome", "completed"))
        return 0
    doc: dict[str, Any] = json.loads(OUT.read_text(encoding="utf-8")) if OUT.exists() else {
        "spec": "D625; docs/decisions/D625-PRE-REG-the-TAS-premium-as-a-signed-stand-in-for-window-flow.md (158b2d2)"}
    build = {"siblings": siblings, "gate": gate}
    if a.check:
        rebuilt = dict(doc)
        for ph in build:
            if ph in doc:
                rebuilt[ph] = build[ph]()
        if "post_hoc_diagnostic" in doc:
            rebuilt["post_hoc_diagnostic"] = diagnose()
            try:
                siblings()
            except D625Error as exc:
                rebuilt["siblings_preregistered_outcome"] = f"RAISED: {exc}"
        if _dump(rebuilt) != OUT.read_text(encoding="utf-8"):
            raise D625Error(f"{OUT.name} does not reproduce")
        print(f"[check] {OUT.name} reproduces byte for byte")
        return 0
    phase = "siblings" if a.siblings else "gate" if a.gate else None
    if phase is None:
        ap.print_help()
        return 2
    doc[phase] = build[phase]()
    doc["deviations"] = DEVIATIONS
    OUT.write_text(_dump(doc), encoding="utf-8", newline="\n")
    p = doc[phase]
    if phase == "siblings":
        print("K1 TAS", p["k1_tas"])
        for role in ("W", "P"):
            s = p[role]
            print(role, "selection means", s["selection_first_half"]["mean"], "-> chosen", s["selection_first_half"]["chosen"])
            print("  second half", {r: (x["agreement"], x["n"], x["pearson_r"]) for r, x in s["agreement_second_half"].items()},
                  "| siblings agree:", s["siblings_agree"])
    else:
        for r, d in p["roots"].items():
            print(r, {role: (d[role]["agreement"], d[role]["n"], d[role]["verdict"]) for role in ("W", "P")})
    return 0


if __name__ == "__main__":
    sys.exit(main())
