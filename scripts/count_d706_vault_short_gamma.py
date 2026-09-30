"""D706 PREMISE COUNT -- how many short-gamma sessions (G_SUM < 0) the unseen slices hold, and what power that gives
the short-gamma direction line (D699's V1, D700's 15-minute channel, D704's gate) on them. The principal,
2026-09-30: "Count short-gamma days".

    uv run python scripts/count_d706_vault_short_gamma.py --run --data-root "<main checkout>/data"

WHAT IS READ ON OR AFTER 2024-01-01 (the conditioner only; asserted in code):
  SqueezeMetrics GEX (DIX.csv: date, gex), the ES options open interest and prior settlements
  (fut_es_options_eod.csv.gz, D688's columns), the ES settlement strip (fut_settle_strip.csv.gz, root ES), and the ES
  session calendar (fut_index_sessions.csv.gz: root, day, bars). NO ES bar, NO intraday price, NO return. The G_ES
  gamma needs the prior settlement prices of the future and the options (D581's Black-76 at the prior settlement); that
  is the whole of the price information read, and no statistic of it is reported.
SLICES: CLEAN 2024-01-01 -> 2025-02-28 (D689 counted it: the count is reproduced exactly as the guard) and VAULT
2025-03-01 -> 2026-09-18 (sessions exist to 2026-09-09; later sessions are counted as uncountable).
OUTPUT: counts only (sessions, both books present, short by G_SUM / SPX / ES book, the composition, by month) and the
power table computed from the published in-sample statistics. Statistics only, no per-date GEX (SqueezeMetrics, under
the permission of 2026-09-28).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import stage0_d688_gamma_close as S                 # noqa: E402  (importing defines, never runs)

OUT = REPO / "data" / "d706_vault_short_gamma_count.json"
SLICES = {"clean_2024_01_2025_02": ("2024-01-01", "2025-02-28"), "vault_2025_03_2026_09": ("2025-03-01", "2026-09-18")}
LOOKBACK = "2023-11-01"
Z05 = 1.6448536269514722
EFFECTS = (1.0, 0.5, 0.25)


def P(*a, **k):
    print(*a, **k, flush=True)


_W: dict = {}


def _init(fx, strip_es, tcal, refs, lo, hi):
    _W.update(m=S.d581(Path(fx)), fx=Path(fx), strip=strip_es, tcal=tcal, refs=refs, lo=lo, hi=hi)


def _work(mine):
    mine = set(mine)
    parts = []
    for ch in pd.read_csv(_W["fx"] / "fut_es_options_eod.csv.gz", usecols=S.OPT_COLS, dtype=S.OPT_DTYPE, chunksize=S.CHUNK, encoding="utf-8"):
        ch = ch[ch["session"].isin(mine)]
        if len(ch):
            parts.append(ch)
    if not parts:
        return pd.DataFrame(columns=["G_ES"])
    opts = pd.concat(parts, ignore_index=True)
    if ((opts["session"] < _W["lo"]) | (opts["session"] > _W["hi"])).any():
        raise S.GateError("[SEAL] an option row outside the slice reached the reader")
    if not S.oi_keyed(opts, 0):
        raise S.GateError("[LAG] an option row's OI was published after 10:00 of its session")
    return S.es_book_prior(opts, _W["strip"], _W["tcal"], _W["refs"], _W["m"])


def count_slice(data_root: Path, lo: str, hi: str, tcal: np.ndarray, log=P) -> dict:
    fx = data_root / "fixtures"
    st = pd.read_csv(fx / "fut_settle_strip.csv.gz", dtype={"root": str, "contract": str, "ref": str}, encoding="utf-8")
    st = st[(st["root"] == "ES") & (st["ref"] >= LOOKBACK) & (st["ref"] <= hi)].reset_index(drop=True)
    dix = pd.read_csv(data_root / "raw" / "squeezemetrics" / "DIX.csv", usecols=["date", "gex"], dtype={"date": str}, encoding="utf-8")
    dix = dix[(dix["date"] >= LOOKBACK) & (dix["date"] <= hi)].sort_values("date").reset_index(drop=True)
    days = np.array([d for d in tcal if lo <= d <= hi])
    refs = np.array(sorted(st["ref"].unique()))
    strides = [days[i::S.N_WORKERS].tolist() for i in range(S.N_WORKERS)]
    with ProcessPoolExecutor(max_workers=S.N_WORKERS, initializer=_init, initargs=(str(fx), st, tcal, refs, lo, hi)) as ex:
        book = pd.concat(list(ex.map(_work, strides))).sort_index()
    dd = dix["date"].to_numpy().astype(str)
    j = np.searchsorted(dd, days) - 1                                   # the last GEX row strictly before d
    g_spx = pd.Series(np.where(j >= 0, dix["gex"].to_numpy(float)[np.maximum(j, 0)], np.nan), index=days)
    g_es = book["G_ES"].reindex(days) if "G_ES" in book else pd.Series(np.nan, index=days)
    g = g_spx + g_es
    ok = np.isfinite(g.to_numpy())
    sp, es = g_spx.to_numpy(), g_es.to_numpy()
    mon = pd.Series(days).str[:7].to_numpy()
    out = {"calendar_sessions": int(len(days)), "sessions_with_both_books": int(ok.sum()),
           "short_gamma_sessions": {"G_SUM": int((g[ok] < 0).sum()), "G_SPX": int((g_spx[ok] < 0).sum()), "G_ES": int((g_es[ok] < 0).sum())},
           "composition_of_G_SUM_short": {"spx_short_es_short": int((ok & (sp < 0) & (es < 0) & (g.to_numpy() < 0)).sum()),
                                          "spx_long_es_short": int((ok & (sp >= 0) & (es < 0) & (g.to_numpy() < 0)).sum()),
                                          "spx_short_es_long": int((ok & (sp < 0) & (es >= 0) & (g.to_numpy() < 0)).sum())},
           "short_gamma_by_month_G_SUM": {mm: int(((g < 0).to_numpy() & (mon == mm)).sum()) for mm in sorted(set(mon))},
           "first_last_session": [str(days[0]), str(days[-1])] if len(days) else None}
    return out


def insample_composition(data_root: Path, log=P) -> dict:
    """The same counts on D699's in-sample panel (2016-01-05 -> 2023-12-29), from D688's panel reproduced."""
    import stage0_d699_gamma_macd_long as V
    D, PM, pidx = V.panel(data_root, log)
    sp, es = D["G_SPX"].to_numpy(float), D["G_ES"].to_numpy(float)
    g = sp + es
    return {"sessions": int(len(D)), "G_SUM_short": int((g < 0).sum()), "G_SPX_short": int((sp < 0).sum()), "G_ES_short": int((es < 0).sum()),
            "composition_of_G_SUM_short": {"spx_short_es_short": int(((sp < 0) & (es < 0)).sum()), "spx_long_es_short": int(((sp >= 0) & (es < 0) & (g < 0)).sum()),
                                           "spx_short_es_long": int(((sp < 0) & (es >= 0) & (g < 0)).sum())}}


def power(n_short_vault: int) -> dict:
    """Expected t on the vault from each component's published in-sample statistic: per-unit signal-to-noise = t_in /
    sqrt(n_in) (the in-sample t is NW or day-clustered, so the SNR carries that adjustment), units in the vault =
    (n_in / short days in-sample) x short days in the vault, expected t = effect x SNR x sqrt(n_vault); the one-sided
    5% pass probability is Phi(E t - 1.645)."""
    d699 = json.loads((REPO / "data" / "d699_gamma_macd_long.json").read_text(encoding="utf-8"))
    d700 = json.loads((REPO / "data" / "d700_channel_clock_profile.json").read_text(encoding="utf-8"))
    d704 = json.loads((REPO / "data" / "d704_no_push_gate_on_v1.json").read_text(encoding="utf-8"))
    short_in = d699["tradable_short_gamma_sessions"]
    v1 = d699["variants"]["V1_HIST"]
    ch = d700["clocks"]["15"]["profile"]["short_gamma"]["+60m"]
    up = d704["S_B"]["upper_half"]
    comp = {
        "V1_net_gt_0": (v1["2_book"]["trades"], v1["2_book"]["nw_t_mean_net"]),
        "V1_beats_drift": (v1["2_book"]["trades"], v1["3_drift_control"]["nw_t_excess"]),
        "V1_gated_upper_half_beats_drift": (up["trades"], up["edge_per_noise"] * math.sqrt(up["trades"])),
        "channel_15m_beats_drift_60m": (ch["n"], ch["t_excess"]),
    }
    Phi = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    out = {}
    for k, (n_in, t_in) in comp.items():
        snr = t_in / math.sqrt(n_in)
        n_v = n_in / short_in * n_short_vault
        out[k] = {"in_sample_units": int(n_in), "in_sample_t": float(t_in), "snr_per_unit": snr, "expected_units_in_vault": n_v,
                  "by_effect": {str(e): {"expected_t": e * snr * math.sqrt(n_v), "p_pass_one_sided_5pc": Phi(e * snr * math.sqrt(n_v) - Z05)} for e in EFFECTS}}
    a, b = out["V1_beats_drift"], out["channel_15m_beats_drift_60m"]
    out["V1_plus_channel_15m_independent_stouffer"] = {"by_effect": {str(e): {"expected_t": (a["by_effect"][str(e)]["expected_t"] + b["by_effect"][str(e)]["expected_t"]) / math.sqrt(2)} for e in EFFECTS}}
    for e in EFFECTS:
        q = out["V1_plus_channel_15m_independent_stouffer"]["by_effect"][str(e)]
        q["p_pass_one_sided_5pc"] = Phi(q["expected_t"] - Z05)
    out["in_sample_short_gamma_sessions"] = short_in
    return out


def run(data_root: Path, log=P) -> int:
    t0 = time.time()
    sess = pd.read_csv(data_root / "fixtures" / "fut_index_sessions.csv.gz", usecols=["root", "day", "bars"], dtype={"root": str, "day": str}, encoding="utf-8")
    tcal = np.array(sorted(sess[sess["root"] == "ES"]["day"].unique()))
    res = {"spec": "D706 PREMISE COUNT (conditioner only; no ES bar, intraday price or return read on or after 2024-01-01)", "slices": {}}
    for nm, (lo, hi) in SLICES.items():
        res["slices"][nm] = count_slice(data_root, lo, hi, tcal, log)
        c = res["slices"][nm]
        log(f"  {nm}: {c['calendar_sessions']} sessions {c['first_last_session']}, {c['sessions_with_both_books']} with both books; short gamma G_SUM {c['short_gamma_sessions']['G_SUM']} "
            f"(SPX {c['short_gamma_sessions']['G_SPX']}, ES book {c['short_gamma_sessions']['G_ES']}); composition {c['composition_of_G_SUM_short']}")
    ref = json.loads((REPO / "data" / "d689_short_gamma_continuation.json").read_text(encoding="utf-8"))["premise"]["short_gamma_sessions"]["G_SUM"]
    got = res["slices"]["clean_2024_01_2025_02"]["short_gamma_sessions"]["G_SUM"]
    if got != ref:
        raise S.GateError(f"[REPRO] the clean slice counts {got} short-gamma sessions; D689 counted {ref}")
    log(f"  D689's clean-slice count REPRODUCED: {got}")
    res["in_sample"] = insample_composition(data_root, log)
    log(f"  in-sample: {res['in_sample']}")
    res["power_vault"] = power(res["slices"]["vault_2025_03_2026_09"]["short_gamma_sessions"]["G_SUM"])
    res["power_clean_plus_vault"] = power(got + res["slices"]["vault_2025_03_2026_09"]["short_gamma_sessions"]["G_SUM"])
    for lab in ("power_vault", "power_clean_plus_vault"):
        for k, v in res[lab].items():
            if isinstance(v, dict):
                log(f"  {lab} {k}: " + " | ".join(f"effect {e}: E t {q['expected_t']:.2f}, P(pass) {q['p_pass_one_sided_5pc']:.2f}" for e, q in v["by_effect"].items()))
    res["timing_s"] = round(time.time() - t0, 1)
    OUT.write_text(json.dumps(res, indent=1, default=lambda o_: o_.item() if hasattr(o_, "item") else str(o_)), encoding="utf-8")
    log(f"  wrote {OUT.relative_to(REPO)} in {res['timing_s']} s")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--data-root", type=Path, default=REPO / "data")
    a = ap.parse_args()
    sys.exit(run(a.data_root) if a.run else 1)
