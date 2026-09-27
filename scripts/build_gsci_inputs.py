"""GSCI inputs for D635 (Gate C0): the published reference percentage dollar weights (RPDW) by year, and GSCI's
designated-contract schedule, parsed from data/index_reweight/SOURCES_GSCI_CFTC.md §2.3 and §2.5 (every value there
is sourced; nothing is typed here).

Outputs:
  data/index_reweight/gsci_rpdw.csv      target_year, ric, rpdw_pct, source   (2016 and 2018-2026 as published;
                                         2017 = the mean of 2016 and 2018, D635 §3, source "declared mean")
  data/index_reweight/gsci_schedule.csv  ric, cme_root, m01..m12  (the contract letter held at each month's start)
Checks (raise): every published year sums to 100 within 0.1; the schedule has 12 letters per row; every CME root D635
observes maps to one RIC or is declared absent (ZL, ZM, HG).

    uv run python scripts/build_gsci_inputs.py
"""
from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
SRC = REPO / "data" / "index_reweight" / "SOURCES_GSCI_CFTC.md"
OUT_W = REPO / "data" / "index_reweight" / "gsci_rpdw.csv"
OUT_S = REPO / "data" / "index_reweight" / "gsci_schedule.csv"
RIC_TO_CME = {"W": "ZW", "KW": "KE", "C": "ZC", "S": "ZS", "LH": "HE", "LC": "LE", "CL": "CL", "HO": "HO",
              "RB": "RB", "NG": "NG", "GC": "GC", "SI": "SI"}
NOT_IN_GSCI = ("ZL", "ZM", "HG")  # GSCI holds no soybean oil, no soybean meal, and LME (not COMEX) copper


def section(text: str, head: str) -> list[str]:
    i = text.index(head)
    j = text.find("\n### ", i + len(head))
    return text[i:j if j > 0 else None].splitlines()


def main() -> int:
    text = SRC.read_text(encoding="utf-8")
    # §2.5: the RPDW table
    rows = [ln for ln in section(text, "### 2.5") if ln.startswith("| ") and not ln.startswith("| RIC") and "---" not in ln]
    head = next(ln for ln in section(text, "### 2.5") if ln.startswith("| RIC"))
    years = [int(re.match(r"\s*(\d{4})", c).group(1)) for c in head.strip("|").split("|")[1:]]  # type: ignore[union-attr]
    recs = []
    for ln in rows:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        ric = cells[0]
        for y, c in zip(years, cells[1:]):
            v = float(re.sub(r"[^\d.]", "", c))
            recs.append({"target_year": y, "ric": ric, "rpdw_pct": v, "source": "SOURCES_GSCI_CFTC.md s.2.5"})
    w = pd.DataFrame(recs)
    for y, g in w.groupby("target_year"):
        if abs(g["rpdw_pct"].sum() - 100) > 0.1:
            raise RuntimeError(f"GSCI RPDW {y} sums to {g['rpdw_pct'].sum()}")
    a = w[w["target_year"] == 2016].set_index("ric")["rpdw_pct"]
    b = w[w["target_year"] == 2018].set_index("ric")["rpdw_pct"]
    m = (a + b) / 2
    m = m / m.sum() * 100
    w = pd.concat([w, pd.DataFrame({"target_year": 2017, "ric": m.index, "rpdw_pct": m.values,
                                    "source": "declared mean of 2016 and 2018 (D635 s.3); 2017 not published"})])
    w = w.sort_values(["target_year", "ric"]).reset_index(drop=True)
    w.to_csv(OUT_W, index=False, encoding="utf-8", lineterminator="\n")
    # §2.3: the schedule
    srows = [ln for ln in section(text, "### 2.3") if ln.startswith("| ") and "---" not in ln and not ln.startswith("| fac.")]
    sched = []
    for ln in srows:
        cells = [c.strip() for c in ln.strip("|").split("|")]
        rics, months = cells[2].split(), cells[3:15]
        if len(months) != 12 or not all(re.fullmatch(r"[FGHJKMNQUVXZ]", x) for x in months):
            raise RuntimeError(f"schedule row {cells[:3]} does not hold 12 month letters")
        for ric in rics:
            sched.append({"ric": ric, "cme_root": RIC_TO_CME.get(ric, ""), **{f"m{i + 1:02d}": x for i, x in enumerate(months)}})
    s = pd.DataFrame(sched)
    got = set(s["cme_root"]) - {""}
    if got != set(RIC_TO_CME.values()):
        raise RuntimeError(f"CME roots in the schedule {sorted(got)} != {sorted(set(RIC_TO_CME.values()))}")
    s.to_csv(OUT_S, index=False, encoding="utf-8", lineterminator="\n")
    print(f"RPDW: {w['target_year'].nunique()} years x {w['ric'].nunique()} RICs; schedule: {len(s)} rows; "
          f"no GSCI term for {NOT_IN_GSCI}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
