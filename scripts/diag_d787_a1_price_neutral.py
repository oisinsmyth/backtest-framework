"""D787 A1: the price-neutral re-check of signal strength for D776 and L4 (in-sample, already read; the principal:
"Price-neutral re-check, then decide"). Definitions fixed before the look:
- L4: m = |c| / its own trailing q80 threshold (cthr), i.e. how far past its own gate; the gate is a rank of the
  prior 250 sessions' |c|, so m is free of the price level;
- D776: m = |x| / the sd of the same 08:29 -> 08:34 move over the 60 prior weekday sessions (at least 40).
Strength is D787's (the expanding percentile among earlier trades, >= 30); the profile is D787's book_profile, plus the
correlation of strength with the calendar year (the price-level check).

    uv run --no-sync python scripts/diag_d787_a1_price_neutral.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts"))
import diag_d786_abstention_oracle as A  # noqa: E402
import diag_d787_signal_strength as S7  # noqa: E402

OUT = REPO / "data" / "diag_d787_a1_price_neutral.json"
SIG_X_N, SIG_X_MIN = 60, 40


def books() -> dict[str, pd.DataFrame]:
    import stage0_d775_cpi_nfp_fade as S775
    import stage0_d778_auction_fade_trend_filter as D8
    bn = S775._load_file((S775.ROOTS["NQ"][0], ("NQ",)))
    Sx = S775.sessions(bn, "NQ")
    sig_x = Sx["x"].where(Sx["ok"]).shift(1).rolling(SIG_X_N, min_periods=SIG_X_MIN).std()
    U, _ = S775.classify(Sx, S775.release_days())
    R = U[U["is_rel"]]
    S7.need(len(R) == 186 and round(float(R["gross"].mean()), 2) == 34.88, "D776's known answer")
    d776 = pd.DataFrame({"gross": R["gross"], "net": R["gross"] - S775.ROOTS["NQ"][2], "m_points": R["x"].abs(),
                         "m": R["x"].abs() / sig_x.reindex(R.index)})
    D = D8.frame(D8._load_file(("fut_opening_globex_1m_ym_rty.csv.gz", ("RTY",))), "RTY")
    B = D[D["base"]]
    S7.need(len(B) == 280 and round(float(B["gross"].mean()), 2) == 15.84, "L4's known answer")
    l4 = pd.DataFrame({"gross": B["gross"], "net": B["gross"] - 3.76, "m_points": B["c"].abs(), "m": B["c"].abs() / B["cthr"]})
    out = {}
    for k, y in (("D776", d776), ("L4", l4)):
        y.index = y.index.astype(str)
        y = y[(y.index >= A.LO) & (y.index <= A.HI)].sort_index()
        out[k] = y[y["m"].notna()]
    return out


def main() -> int:
    stq = A.state_frame(A.daily_closes("NQ"), A.MULT["NQ"])
    res = {"spec": "D787 A1 (docs/decisions/D787-DIAG-RESULT-signal-strength-sorts-the-size-triggered-books.md)", "books": {}}
    for b, y in books().items():
        res["books"][b] = {}
        for form, col in (("points (D787)", "m_points"), ("price-neutral", "m")):
            z = y.copy()
            z["strength"] = S7.strength(z[col].to_numpy(float))
            z["year"] = z.index.str[:4]
            S7.audit(z.assign(m=z[col]), b)
            vol = A.at_lag(stq, z.index, A.LAG[b])["volpct"]
            p = S7.book_profile(z, vol)
            ok = z["strength"].notna()
            p["corr_strength_year"] = round(float(np.corrcoef(z.loc[ok, "strength"], z.loc[ok, "year"].astype(int))[0, 1]), 3)
            res["books"][b][form] = p
            s, e = p["strong_vs_weak"], p["strong_vs_weak_ex_2020_2022"]
            print(f"{b:5s} {form:14s} | strong {s['strong']['n']} {s['strong']['mean_net']} weak {s['weak']['n']} {s['weak']['mean_net']} "
                  f"z {s['z']} | ex20/22 {e['strong']['mean_net']} / {e['weak']['mean_net']} z {e['z']} | corr(year) "
                  f"{p['corr_strength_year']} | weak by year {p['weak_half_by_year']}")
    OUT.write_text(json.dumps(res, indent=1, default=str) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
