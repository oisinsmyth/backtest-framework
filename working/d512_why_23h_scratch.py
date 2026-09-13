"""Diagnostic for D512: WHY is the 23-hour range version better than the day-session one, and is the gap real at all?

A decomposition of an already-read result, not a new search. Any cell it introduces is post-hoc and cannot be promoted.

    uv run python -u working/d512_why_23h_scratch.py
"""
from __future__ import annotations
import importlib.util, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))


def _load(name, fn):
    s = importlib.util.spec_from_file_location(name, REPO / "scripts" / fn); m = importlib.util.module_from_spec(s)
    sys.modules[name] = m; s.loader.exec_module(m); return m


D508 = _load("d508c", "run_d508_stretch_ranker.py")
D509 = _load("d509c", "run_d509_quintile_primary.py")
D512 = _load("d512c", "run_d512_range_expansion.py")
D504 = _load("d504c", "d504_arm_full_history.py")

NIGHT_SEGS = list(range(0, D504.DAY_FIRST_DECIDE))            # h18..h08, the hours the arm never trades
DAY_SEGS = D512.DAY_SEGS                                       # h09..h15, the hours it does

hi, lo, cl, sd = D512.segment_hl()
a = D508.load_arm(); net = a["net"]; mask = a["mask"]; days = a["days"]


def rng_log(segs):
    with np.errstate(invalid="ignore"):
        h = np.nanmax(hi[:, segs], axis=1); l = np.nanmin(lo[:, segs], axis=1)
        return np.log(np.where((h > 0) & (l > 0), h / l, np.nan))


R = {"day": rng_log(DAY_SEGS), "night": rng_log(NIGHT_SEGS), "full": rng_log(list(range(hi.shape[1])))}
V = {k: D512.expansion(v)[mask] for k, v in R.items()}
raw = {k: v[mask] for k, v in R.items()}

print("D512 DIAGNOSTIC -- why is the 23-hour version better, and is the gap real?\n")
print(f"sessions {len(net):,}  {min(days)}..{max(days)}\n")

print("1. THE RAW RANGES -- how much of the 23-hour range is the night?")
m = np.isfinite(raw["day"]) & np.isfinite(raw["night"]) & np.isfinite(raw["full"])
print(f"   mean log range: day {raw['day'][m].mean():.5f}  night {raw['night'][m].mean():.5f}  full {raw['full'][m].mean():.5f}")
print(f"   the full range exceeds the day range on {100*np.mean(raw['full'][m] > raw['day'][m] + 1e-12):.1f}% of sessions")
print(f"   rho(day, night) {np.corrcoef(raw['day'][m], raw['night'][m])[0,1]:+.3f}   rho(day, full) {np.corrcoef(raw['day'][m], raw['full'][m])[0,1]:+.3f}   rho(night, full) {np.corrcoef(raw['night'][m], raw['full'][m])[0,1]:+.3f}")

print("\n2. THE CONDITIONERS -- are they even different objects?")
mv = np.isfinite(V["day"]) & np.isfinite(V["night"]) & np.isfinite(V["full"])
for x, y in (("day", "full"), ("day", "night"), ("night", "full")):
    print(f"   rho(V_{x}, V_{y}) {np.corrcoef(V[x][mv], V[y][mv])[0,1]:+.4f}   Spearman {D508.spearman(V[x][mv], V[y][mv]):+.4f}")

print("\n3. THE STATISTIC, INCLUDING A NIGHT-ONLY CELL (post-hoc, not promotable)")
res = {}
for k in ("day", "night", "full"):
    d, tm, bm, nt, nb = D509.qdiff(V[k], net)
    path = D509.rotation_qdiff(V[k], net); path = path[np.isfinite(path)]
    res[k] = dict(delta=d, top=tm, bot=bm, p95=float(np.quantile(path, .95)), pct=float((path <= d).mean()), path=path)
    print(f"   {k:6s} Delta {d:+7.2f}  (top {tm:+7.2f}, bottom {bm:+7.2f})  p95 {res[k]['p95']:+7.2f}  {100*res[k]['pct']:5.1f}th pct")

print("\n4. IS THE GAP REAL? rotate BOTH conditioners by the SAME offset, which preserves their correlation,")
print("   and ask how big a gap arises by chance.")
D = min(len(res["day"]["path"]), len(res["full"]["path"]))
gap_null = res["full"]["path"][:D] - res["day"]["path"][:D]
gap_obs = res["full"]["delta"] - res["day"]["delta"]
print(f"   observed gap (full - day) {gap_obs:+.2f} a session")
print(f"   null gaps: p05 {np.quantile(gap_null, .05):+.2f}  p50 {np.median(gap_null):+.2f}  p95 {np.quantile(gap_null, .95):+.2f}  sd {gap_null.std(ddof=1):.2f}")
print(f"   the observed gap sits at the {100*np.mean(gap_null <= gap_obs):.1f}th percentile of gaps that arise from rotation alone")
print(f"   |gap| >= observed on {100*np.mean(np.abs(gap_null) >= abs(gap_obs)):.1f}% of offsets")

print("\n5. HOW MANY SESSIONS ACTUALLY CHANGE QUINTILE?")
q = {}
for k in ("day", "full"):
    mm = np.isfinite(V[k]); qq = np.full(len(net), -1); qq[mm] = pd.qcut(V[k][mm], 5, labels=False, duplicates="drop"); q[k] = qq
both = (q["day"] >= 0) & (q["full"] >= 0)
same = q["day"][both] == q["full"][both]
print(f"   same quintile on {100*same.mean():.1f}% of the {both.sum():,} ranked sessions")
top_d, top_f = (q["day"] == 4) & both, (q["full"] == 4) & both
bot_d, bot_f = (q["day"] == 0) & both, (q["full"] == 0) & both
print(f"   top quintile: {top_d.sum()} day, {top_f.sum()} full, {np.sum(top_d & top_f)} shared -> {np.sum(top_f & ~top_d)} sessions the 23-hour version adds")
print(f"   bottom quintile: {bot_d.sum()} day, {bot_f.sum()} full, {np.sum(bot_d & bot_f)} shared -> {np.sum(bot_f & ~bot_d)} added")

print("\n6. WHAT DO THE SWAPPED SESSIONS CARRY? (the repo's rule: name the sessions, do not just report the statistic)")
add_top = top_f & ~top_d; drop_top = top_d & ~top_f
add_bot = bot_f & ~bot_d; drop_bot = bot_d & ~bot_f
for lab, s in (("added to top", add_top), ("dropped from top", drop_top), ("added to bottom", add_bot), ("dropped from bottom", drop_bot)):
    if s.sum():
        print(f"   {lab:20s} n {s.sum():3d}  mean net ${net[s].mean():+8.2f}  total ${net[s].sum():+9.0f}")
worst = np.argsort(net[add_bot])[:3] if add_bot.sum() else []
if add_bot.sum():
    dd = days[add_bot][worst]; vv = net[add_bot][worst]
    print(f"   the three worst sessions the 23-hour version ADDS to the bottom quintile: " + ", ".join(f"{d} ${v:+.0f}" for d, v in zip(dd, vv)))
top_sessions = np.argsort(net[add_top])[-3:] if add_top.sum() else []
if add_top.sum():
    dd = days[add_top][top_sessions]; vv = net[add_top][top_sessions]
    print(f"   the three best  sessions the 23-hour version ADDS to the top quintile:    " + ", ".join(f"{d} ${v:+.0f}" for d, v in zip(dd, vv)))

print("\n7. HOW MUCH OF THE GAP IS THOSE SWAPS? (top-quintile mean moves by the swapped sessions alone)")
nt_f = top_f.sum(); nt_d = top_d.sum()
print(f"   day top mean ${net[top_d].mean():+.2f} on {nt_d}; full top mean ${net[top_f].mean():+.2f} on {nt_f}")
print(f"   the {add_top.sum()} added sessions average ${net[add_top].mean():+.2f}; the {drop_top.sum()} dropped average ${net[drop_top].mean():+.2f}")
print(f"   bottom: day ${net[bot_d].mean():+.2f}, full ${net[bot_f].mean():+.2f}; added ${net[add_bot].mean():+.2f}, dropped ${net[drop_bot].mean():+.2f}")
