"""D636's shared design for Stages R1-R3 and their POWER step: the January predicted flows (BCOM's dN from the D634
re-run; GSCI's reweight flow per $1bn at its BD4 reference day), the construction-A gate inputs (sigma_d, V_d, the
square-root impact, the cost), and the fills read from Sierra Chart 1-tick files.

Nothing here decides a verdict. Moves are read only when a caller asks for them on a given day list.

GSCI weights (D636 s.1): w_k,i = CPW_k,i * P_i / sum_j CPW_k,j * P_j over all 24 components, at the settlements of
GSCI's January holdings on BD4 of January (NG's CME calendar). The dollar weight reproduces S&P's RPDW with prices
in S&P's units (grains, softs and livestock in cents), which are also the strip's and Sierra's.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IR = REPO / "data" / "index_reweight"
CUT = "2025-03-01"
YEARS = range(2016, 2026)
LETTER = "FGHJKMNQUVXZ"
UNIVERSE = ["Natural Gas", "WTI Crude Oil", "ULS Diesel", "RBOB Gasoline", "Corn", "Soybeans", "Soybean Meal",
            "Soybean Oil", "Wheat", "HRW Wheat", "Copper", "Silver"]
BESIDE = ["Live Cattle", "Lean Hogs", "Gold"]
RIC_OF = {"Wheat": "W", "HRW Wheat": "KW", "Corn": "C", "Soybeans": "S", "Lean Hogs": "LH", "Live Cattle": "LC",
          "WTI Crude Oil": "CL", "ULS Diesel": "HO", "RBOB Gasoline": "RB", "Natural Gas": "NG", "Gold": "GC",
          "Silver": "SI"}
ICE_SRC = {"LCO": ("BRN", "ICEEU"), "LGO": ("GAS", "ICEEU"), "KC": ("KC", "ICEUS"), "SB": ("SB", "ICEUS"),
           "CT": ("CT", "ICEUS"), "CC": ("CC", "ICEUS"), "FC": ("GF", "CME")}
LME_OF = {"MAL": "aluminium", "MCU": "copper", "MNI": "nickel", "MPB": "lead", "MZN": "zinc"}
# quoted in US cents by the exchanges (and the strip and Sierra); GSCI's dollar weight needs dollars. S&P's printed
# ACRP for these is in cents under a "$" header; divided by 100 it reproduces the RPDW (SOURCES_GSCI_CFTC s.2.5)
CENTS = {"W", "KW", "C", "S", "KC", "SB", "CT", "LH", "LC", "FC"}
Y_IMPACT = 0.7
DT = np.dtype([("t", "<i8"), ("o", "<f4"), ("h", "<f4"), ("l", "<f4"), ("c", "<f4"), ("n", "<u4"), ("v", "<u4"),
               ("bv", "<u4"), ("av", "<u4")])
ORIGIN = pd.Timestamp("1899-12-30", tz="UTC")


def _load(name: str, fn: str) -> Any:
    if name in sys.modules:
        return sys.modules[name]
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn)
    assert s is not None and s.loader is not None
    m = importlib.util.module_from_spec(s)
    sys.modules[name] = m
    s.loader.exec_module(m)
    return m


G = _load("run_gate_r0", "run_gate_r0.py")
SD = _load("sierra_index_reweight_download", "sierra_index_reweight_download.py")
sys.path.insert(0, str(REPO / "scripts"))
import settlement_windows as SW  # noqa: E402


class Base:
    """Everything that does not depend on kappa: prices, the calendar, CIMs, held prices, dN_B, dN_G, volumes."""

    def __init__(self) -> None:
        reads: dict[str, Any] = {}
        self.cip = G.cips()
        cme, _ = G.load_cme(reads, fill=True)
        self.prices = {**cme, **G.load_ice(reads), **G.load_lme(reads)}
        G.assert_no_vault(self.prices)
        bdays, self.bd, self.det = G.calendar(self.prices, self.cip)
        self.bdays = [d for d in bdays if d >= "2015-01-01"]
        comps = sorted({c for y in self.cip for c, w in self.cip[y].items() if w > 0})
        self.rws = {c: G.roll_weights(c, self.prices, self.bdays, self.bd) for c in comps}
        RH = {c: G.sub_index_returns(c, self.prices, self.bdays, self.bd, self.rws[c]) for c in comps}
        self.R = {c: v[0] for c, v in RH.items()}
        self.H = {c: v[1] for c, v in RH.items()}
        self.cim = G.cims(self.prices, self.cip, self.det)
        self.r0 = json.loads((IR / "gate_r0_rerun.json").read_text(encoding="utf-8"))["dN"]
        panel = pd.read_csv(IR / "window_flow_daily.csv.gz", encoding="utf-8", dtype={"day": str})
        panel = panel[panel["day"] < CUT]
        self.vol = {s: g.set_index("day")["volume"].sort_index() for s, g in panel.groupby("sym")}
        self.cpw = pd.read_csv(IR / "gsci_cpw.csv", encoding="utf-8")
        self.rpdw = pd.read_csv(IR / "gsci_rpdw.csv", encoding="utf-8")
        self.sched = pd.read_csv(IR / "gsci_schedule.csv", encoding="utf-8").set_index("ric")
        lme = pd.concat([pd.read_csv(IR / "lme_westmetall_daily.csv.gz", encoding="utf-8", dtype={"date": str}),
                         pd.read_csv(IR / "lme_copper_westmetall_daily.csv.gz", encoding="utf-8", dtype={"date": str})])
        self.lme = {m: g[g["date"] < CUT].set_index("date") for m, g in lme.groupby("metal")}
        self.reads = reads
        self._dly: dict[str, dict[str, float]] = {}
        self._mm: dict[str, np.memmap] = {}

    # ---------------------------------------------------------------- prices
    def dly(self, sym: str) -> dict[str, float]:
        if sym not in self._dly:
            p = G.SC_DATA / f"{sym}.dly"
            d = pd.read_csv(p, skipinitialspace=True, encoding="utf-8")
            d.columns = [c.strip() for c in d.columns]
            ref = pd.to_datetime(d["Date"]).dt.strftime("%Y-%m-%d")
            self._dly[sym] = {r: float(c) for r, c in zip(ref, d["Close"]) if r < CUT and c != 0}
        return self._dly[sym]

    def settle(self, comp: str, day: str, ym: tuple[int, int]) -> float | None:
        return G.price_at(self.prices, comp, day, ym)

    def gsci_price(self, ric: str, day: str, ym: tuple[int, int]) -> float:
        comp = next((c for c, r in RIC_OF.items() if r == ric), None)
        if comp is not None:
            px = self.settle(comp, day, ym)
        elif ric in ICE_SRC:
            code, ex = ICE_SRC[ric]
            s = self.dly(f"{code}{LETTER[ym[1] - 1]}{ym[0] % 100:02d}-{ex}")
            prior = [d for d in s if d <= day][-5:]
            px = s[sorted(prior)[-1]] if prior else None
        else:
            g = self.lme[LME_OF[ric]]
            rows = g[g.index <= day].tail(5).dropna(subset=["cash_usd_t", "three_month_usd_t"])
            if rows.empty:
                px = None
            else:
                t = pd.Timestamp(rows.index[-1])
                cash, three = float(rows["cash_usd_t"].iloc[-1]), float(rows["three_month_usd_t"].iloc[-1])
                f = (G.third_wednesday(*ym) - t).days / ((t + pd.DateOffset(months=3)) - t).days
                px = cash + (three - cash) * f
        if px is None or px <= 0:
            raise RuntimeError(f"no GSCI price for {ric} {ym} on {day}")
        return float(px)

    # ---------------------------------------------------------------- the January flows
    def ref_day(self, y: int) -> str:
        ng = sorted(d for d in self.prices["Natural Gas"] if d[:7] == f"{y}-01")
        return ng[3]  # BD4 on NG's CME calendar

    def gsci_jan_flow(self, y: int) -> dict[str, Any]:
        """dN_G per $1bn for the CME components GSCI holds: 1e9 (w_new - w_old) / (P mult), P the settlement of the
        contract receiving the flow (the roll-in contract for a component GSCI rolls in January, else the held one)."""
        day = self.ref_day(y)
        px = {}
        for ric, row in self.sched.iterrows():
            lm = LETTER.index(row["m01"]) + 1
            px[ric] = self.gsci_price(str(ric), day, (y, lm))
        c = self.cpw.set_index(["year", "ric"])["cpw"]
        usd = {r: px[r] / 100.0 if r in CENTS else px[r] for r in px}
        w = {}
        for k in (y - 1, y):
            tot = sum(float(c.loc[(k, r)]) * usd[r] for r in usd)
            w[k] = {r: float(c.loc[(k, r)]) * usd[r] / tot for r in usd}
        # the known answer: the reference-day weights line up with S&P's published RPDW(y) (priced on the prior
        # year's average, so not equal)
        rp = self.rpdw[self.rpdw["target_year"] == y].set_index("ric")["rpdw_pct"] / 100
        corr = float(np.corrcoef([w[y][r] for r in rp.index], rp.values)[0, 1])
        if corr < 0.9:
            raise RuntimeError(f"GSCI {y}: reference-day weights correlate {corr:.3f} with the published RPDW")
        out = {}
        for comp, ric in RIC_OF.items():
            row = self.sched.loc[ric]
            held = (y, LETTER.index(row["m01"]) + 1)
            nxt = (y, LETTER.index(row["m02"]) + 1)
            recv = nxt if nxt != held else held
            p = self.settle(comp, day, recv) or px[ric]
            out[comp] = 1e9 * (w[y][ric] - w[y - 1][ric]) / (p * G.mult(comp))
        net = sum(w[y].values()) - sum(w[y - 1].values())
        return {"ref_day": day, "dN_G_per_bn": out, "weights_new": w[y], "weights_old": w[y - 1], "net": net,
                "corr_with_published_rpdw": corr}

    def lead_sym(self, comp: str, y: int) -> tuple[tuple[int, int], str]:
        L = G.lead_of(G.lead_table()[G.COMP[comp][2]], y, 1)
        root, ex = SD.ROOTS[G.COMP[comp][2]]
        return L, f"{root}{LETTER[L[1] - 1]}{L[0] % 100:02d}-{ex}"

    # ---------------------------------------------------------------- the gate inputs
    def sigma(self, comp: str, ym: tuple[int, int], day: str) -> float | None:
        hist = sorted(d for d in self.prices[comp] if d < day and ym in self.prices[comp][d])[-21:]
        if len(hist) < 21:
            return None
        px = np.array([self.prices[comp][d][ym] for d in hist])
        return float(np.std(np.diff(np.log(px)), ddof=1)) if (px > 0).all() else None

    def vol_d(self, sym: str, day: str) -> float | None:
        v = self.vol.get(sym)
        if v is None:
            return None
        prior = v[v.index < day].tail(20)
        return float(prior.mean()) if len(prior) >= 15 and prior.mean() > 0 else None

    def cost(self, comp: str) -> float:
        tick = 12.5 if G.COMP[comp][1] == "KE" else float(G.Future.from_specs(G.COMP[comp][1]).tick_usd)
        return 16.0 + tick

    # ---------------------------------------------------------------- ticks
    def ticks(self, sym: str) -> np.memmap | None:
        if sym not in self._mm:
            p = G.SC_DATA / f"{sym}.scid"
            if not p.exists() or p.stat().st_size <= 56:
                return None
            self._mm[sym] = np.memmap(p, dtype=DT, mode="r", offset=56)
        return self._mm[sym]

    def before(self, sym: str, ts: pd.Timestamp, floor: pd.Timestamp) -> float | None:
        """The last trade strictly before ts, and not before `floor`."""
        a = self.ticks(sym)
        if a is None or ts >= pd.Timestamp(CUT, tz="UTC"):
            return None
        us = int((ts - ORIGIN) / pd.Timedelta(microseconds=1))
        lo = int((floor - ORIGIN) / pd.Timedelta(microseconds=1))
        j = int(np.searchsorted(a["t"], us, side="left"))
        if j == 0 or int(a["t"][j - 1]) < lo:
            return None
        return float(a["c"][j - 1])


def window_utc(root: str, day: str) -> tuple[pd.Timestamp, pd.Timestamp] | None:
    try:
        w = SW.window_for(root, day)
    except (SW.UnmappedProduct, SW.UnsourcedDate):
        return None
    return (pd.Timestamp(f"{day} {w.start_ct}", tz="America/Chicago").tz_convert("UTC"),
            pd.Timestamp(f"{day} {w.end_ct}", tz="America/Chicago").tz_convert("UTC"))


def january_days(b: Base, y: int, lo: int, hi: int) -> list[str]:
    return [d for d in b.bdays if d[:7] == f"{y}-01" and lo <= b.bd[d] <= hi]


def q_daily(dN_B: float, dN_G: float, aum: float, kappa: dict[str, Any]) -> float:
    """D636 s.1: Q = 0.2 (kB dN_B + kG dN_G), or 0.2 kC (dN_B + AUM dN_G) if C0 combined."""
    if kappa["separable"]:
        return 0.2 * (kappa["kappa_B"] * dN_B + kappa["kappa_G_per_bn"] * dN_G)
    return 0.2 * kappa["kappa_C"] * (dN_B + aum * dN_G)


def r1_rows(b: Base, kappa: dict[str, Any], days_of: str = "hedge", comps: list[str] | None = None,
            with_moves: bool = False, t0_min: int = 10, headline: bool = False) -> pd.DataFrame:
    """One row per (year, component, day): Q, the gate inputs, and (if asked) the fill, exit and stress fill.
    days_of: 'hedge' (BD5-9) or 'placebo' (BD12-16); the placebo day k carries hedge day k's Q (D636 s.7)."""
    comps = comps or UNIVERSE
    rows = []
    for y in YEARS:
        gf = b.gsci_jan_flow(y)
        aum = G.AUM[y][0]
        hedge = january_days(b, y, 5, 9)
        days = hedge if days_of == "hedge" else january_days(b, y, 12, 16)
        for comp in comps:
            r = b.r0[str(y)]["rows"][comp]
            dnb = r["dN_headline_only"] if headline else r["dN"]
            dng = gf["dN_G_per_bn"].get(comp, 0.0)
            q = q_daily(dnb, dng, aum, kappa)
            ym, sym = b.lead_sym(comp, y)
            for k, d in enumerate(days):
                w = window_utc(G.COMP[comp][1], d)
                prev = b.bdays[b.bdays.index(d) - 1]
                p = b.settle(comp, prev, ym)
                sig = b.sigma(comp, ym, d)
                v = b.vol_d(sym, d)
                ok = w is not None and p is not None and sig is not None and v is not None
                imp = Y_IMPACT * sig * math.sqrt(abs(q) / v) * p * G.mult(comp) if ok else float("nan")  # type: ignore[operator]
                row = {"year": y, "comp": comp, "root": G.COMP[comp][1], "sym": sym, "k": k + 1, "day": d,
                       "Q": q, "dN_B": dnb, "dN_G": dng, "sigma": sig, "V": v, "P": p, "mult": G.mult(comp),
                       "impact_usd": imp, "cost_usd": b.cost(comp), "usable": ok,
                       "ws": w[0] if w else None, "we": w[1] if w else None}
                if with_moves and ok and q != 0:
                    t0 = w[0] - pd.Timedelta(minutes=t0_min)  # type: ignore[index]
                    floor = t0 - pd.Timedelta(hours=3)
                    fill = b.before(sym, t0 + pd.Timedelta(minutes=2), floor)
                    ex = b.before(sym, w[1], floor)  # type: ignore[index]
                    closes = [b.before(sym, t0 + pd.Timedelta(minutes=m), floor) for m in range(2, 7)]
                    closes = [c for c in closes if c is not None]
                    s = np.sign(q)
                    worst = (max(closes) if s > 0 else min(closes)) if closes else None
                    row.update({"fill": fill, "exit": ex, "stress_fill": worst,
                                "move_usd": (ex - fill) * s * G.mult(comp) if fill is not None and ex is not None else np.nan,
                                "stress_move_usd": (ex - worst) * s * G.mult(comp) if worst is not None and ex is not None else np.nan})
                rows.append(row)
    return pd.DataFrame(rows)


def gate_a(rows: pd.DataFrame, snr: float) -> pd.Series:
    """Construction A: |I| >= 3 x round-trip cost AND SNR >= 1.5 (the SNR is common to a year, D636 s.3)."""
    return rows["usable"] & (rows["impact_usd"] >= 3 * rows["cost_usd"]) & (snr >= 1.5)
