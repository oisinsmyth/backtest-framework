"""D460 -- THE SWING ENVELOPE: the construction rebuilt from the principal's hand-drawn lines.

    uv run python scripts/d460_swing_envelope.py --score               sweep the dials against the hand set
    uv run python scripts/d460_swing_envelope.py --score --line "..."  one line, the full card
    uv run python scripts/d460_swing_envelope.py --proof               audits

WHAT THE HAND LINES ARE (data/d451_hand_drawn_lines.json, 140 lines, drawn one bar at a time
with the future hidden): envelopes a few per cent OUTSIDE the wicks (median 4.4%), through the
neighbourhood of two swing points, drawn the bar after the second swing (lag median 1), FIXED
once drawn (no re-tilt: updates are a new line through the same first anchor), kept a median 26
bars through wick pierces of up to 3.5-7%, and ended three ways: a close through the line
(45%, median 4.4% deep), replacement by a new line the same bar (40%), or drift -- price 26%
from the line with no touch for ~22 bars (15%).

THE CONSTRUCTION, causal, one pass:
  swings     a zigzag on the wicks: a swing low is confirmed the bar the high has risen `r` per
             cent above the running low, a swing high the bar the low has fallen `r` below the
             running high; alternating. The confirmation bar is the earliest bar a line through
             the swing can be drawn.
  birth      when a swing of a kind confirms, the candidate first anchors are the last `K`
             earlier swings of that kind; the OLDEST whose line through the new swing contains
             every wick between them (allowing the margin) is taken; the line is that pivot line
             shifted `m` per cent outward. If none contains, the previous swing is used.
  update     if a line of that kind is live and the new line differs, the live one ends
             (REPLACED) and the new one is born the same bar.
  ends       BREAK: `bbars` consecutive closes beyond the drawn line by more than `b` per cent
             (a support line can only be broken downward, a resistance line upward -- the
             trend side is inherent). DRIFT: no wick within `p` per cent of the drawn line for
             `T` bars AND the close farther than `D` per cent from it.
  restart    nothing special: the next swing of the kind confirms, and the K-swing lookback
             reaches across the break by construction.
Five things the other constructions had are absent because the hand lines show none of them:
touch counts, touch density, width bounds, parallelism, minimum length, and the per-bar refit.

The record per name is a list of {kind, x1, p1, x2, p2, at, until} -- the hand set's own schema,
so the same scorer reads both, and a page can replay either.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
LIVE = REPO / "temp" / "d399_live_bars.json"
HAND = REPO / "data" / "d451_hand_drawn_lines.json"
CARD = REPO / "data" / "d451_hand_scorecard.json"
OUT = REPO / "data" / "d460_swing_scorecard.json"

DEFAULTS = dict(r=0.10, r2=0.04, m=0.04, K=4, b=0.02, bbars=1, p=0.02, T=20, D=0.25, u=0.04)
SETTINGS_LINE = "r=10 r2=4 m=4 K=4 b=2 bbars=1 p=2 T=20 D=25 u=4"
# TWO SCALES (`r`, `r2`). Measured on the hand set: the FIRST anchor is a major swing (the extreme
# of +-7 bars at the median, 13% reversed off by the draw bar), the SECOND a minor one (+-3 bars,
# 5% reversed, drawn the bar after it forms). One zigzag cannot give both, so two run side by
# side: the major (`r`) supplies the first-anchor candidates, the minor (`r2`) the second anchor
# and the draw bar.
# `u`, THE UPDATE SLACK. The first version redrew the line on every new swing of the kind (925 of
# 1,060 lines "replaced" on the panels against the principal's 47 of 140): a new swing that sits
# INSIDE the live envelope is not a reason to redraw. A line is now replaced only when the new
# swing pierces the drawn line, or sits farther than `u` per cent inside it (the line has gone
# loose). u = 100 means "only on a pierce".
KINDS = ("support", "resistance")
PPY = 252.0


def parse_line(line):
    P = dict(DEFAULTS)
    for tok in line.split():
        k, v = tok.split("=", 1)
        if k in ("r", "r2", "m", "b", "p", "D", "u"):
            P[k] = float(v) / 100
        elif k in ("K", "bbars", "T"):
            P[k] = int(v)
    return P


def _load(name, filename):
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / filename)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ----------------------------------------------------------------------------- the construction
class Zig:
    """A causal zigzag on the wicks: alternating swings, each confirmed the bar price has
    reversed `r` (log) off the running extreme. `step(t)` returns ("support", bar, log low) or
    ("resistance", bar, log high) when a swing confirms at t, else None."""

    def __init__(self, lo, hi, r, a0):
        self.lo, self.hi, self.r = lo, hi, r
        self.dirn, self.ext_p, self.ext_t = 0, None, None
        self.lo_p, self.lo_t, self.hi_p, self.hi_t = lo[a0], a0, hi[a0], a0

    def step(self, t):
        lo, hi, r = self.lo, self.hi, self.r
        if self.dirn == 0:
            if hi[t] > self.hi_p:
                self.hi_p, self.hi_t = hi[t], t
            if lo[t] < self.lo_p:
                self.lo_p, self.lo_t = lo[t], t
            if hi[t] - self.lo_p >= r:
                out = ("support", self.lo_t, self.lo_p); self.dirn, self.ext_p, self.ext_t = 1, hi[t], t
                return out
            if self.hi_p - lo[t] >= r:
                out = ("resistance", self.hi_t, self.hi_p); self.dirn, self.ext_p, self.ext_t = -1, lo[t], t
                return out
            return None
        if self.dirn == 1:                                    # up leg: tracking the running high
            if hi[t] > self.ext_p:
                self.ext_p, self.ext_t = hi[t], t
            if self.ext_p - lo[t] >= r:
                out = ("resistance", self.ext_t, self.ext_p); self.dirn, self.ext_p, self.ext_t = -1, lo[t], t
                return out
            return None
        if lo[t] < self.ext_p:                                # down leg: tracking the running low
            self.ext_p, self.ext_t = lo[t], t
        if hi[t] - self.ext_p >= r:
            out = ("support", self.ext_t, self.ext_p); self.dirn, self.ext_p, self.ext_t = 1, hi[t], t
            return out
        return None


def swing_lines(lo, hi, cl, P, a0=0, a1=None):
    """lo, hi, cl in LOG price. Returns the list of line records, in birth order."""
    n = lo.size if a1 is None else a1
    r, r2, m, K, b, bbars, p, T, D, u = (P[k] for k in ("r", "r2", "m", "K", "b", "bbars", "p", "T", "D", "u"))
    lm, ldeep = math.log1p(m), math.log1p(b)
    lp, lD, lu = math.log1p(p), math.log1p(D), math.log1p(u)
    major = {"support": [], "resistance": []}           # (bar, log price): first-anchor candidates
    live = {"support": None, "resistance": None}         # the line record shown now
    state = {"support": None, "resistance": None}        # per live line: [break count, bars since touch]
    recs = []
    zmaj, zmin = Zig(lo, hi, math.log1p(r), a0), Zig(lo, hi, math.log1p(r2), a0)

    def draw(kind, t, new_b, new_p):
        """Birth of a line of `kind` on the MINOR swing just confirmed at bar t."""
        sign = 1.0 if kind == "support" else -1.0           # containment side
        ext = lo if kind == "support" else hi
        cur = live[kind]
        if cur is not None:
            # keep the live line while the new swing sits inside its envelope and not too far in
            gc = (math.log(cur["p2"]) - math.log(cur["p1"])) / (cur["x2"] - cur["x1"])
            drawn_here = math.log(cur["p1"]) + gc * (new_b - cur["x1"]) - sign * lm
            inside = sign * (new_p - drawn_here)
            if 0.0 <= inside <= lu:
                return
        cands = [s for s in major[kind] if s[0] < new_b][-K:]  # the last K MAJOR swings before it
        chosen = None
        for old_b, old_p in cands:                            # oldest first
            g = (new_p - old_p) / (new_b - old_b)
            seg = ext[old_b:new_b + 1]
            line = old_p + g * np.arange(0, new_b - old_b + 1)
            if np.all(sign * (seg - line) >= -lm):           # every wick inside, margin allowed
                chosen = (old_b, old_p)
                break
        if chosen is None:
            return
        old_b, old_p = chosen
        rec = dict(kind=kind, x1=int(old_b), p1=float(math.exp(old_p)), x2=int(new_b),
                   p2=float(math.exp(new_p)), at=int(t))
        cur = live[kind]
        if cur is not None:
            if cur["x1"] == rec["x1"] and cur["x2"] == rec["x2"]:
                return                                       # the same line: nothing to do
            cur["until"] = int(t)
            cur["why"] = "REPLACED"
        live[kind] = rec
        state[kind] = [0, 0]
        recs.append(rec)

    for t in range(a0, n):
        # ---- swings at two scales; a major swing is also a minor one, so the minor draws
        sw = zmaj.step(t)
        if sw is not None:
            major[sw[0]].append((sw[1], sw[2]))
        sw = zmin.step(t)
        if sw is not None:
            draw(sw[0], t, sw[1], sw[2])
        # ---- the live lines: break and drift, read at the close of t (lines born this bar are exempt)
        for kind in KINDS:
            rec = live[kind]
            if rec is None or rec["at"] == t:
                continue
            g = (math.log(rec["p2"]) - math.log(rec["p1"])) / (rec["x2"] - rec["x1"])
            drawn = math.log(rec["p1"]) + g * (t - rec["x1"]) + (-lm if kind == "support" else lm)
            st = state[kind]
            if kind == "support":
                through, dist, near = drawn - cl[t], cl[t] - drawn, abs(lo[t] - drawn) <= lp
            else:
                through, dist, near = cl[t] - drawn, drawn - cl[t], abs(hi[t] - drawn) <= lp
            st[0] = st[0] + 1 if through > ldeep else 0
            st[1] = 0 if near else st[1] + 1
            if st[0] >= bbars:
                rec["until"], rec["why"] = int(t), "BREAK"
                live[kind], state[kind] = None, None
            elif st[1] >= T and dist > lD:
                rec["until"], rec["why"] = int(t), "DRIFT"
                live[kind], state[kind] = None, None
    return recs


def records_to_N(recs, m, n, cl_raw):
    """The per-bar view the scorer and the trader read: drawn, gradient and DRAWN level (with
    the margin) per kind."""
    lm = math.log1p(m)
    G = {kd: np.full(n, np.nan) for kd in KINDS}
    L = {kd: np.full(n, np.nan) for kd in KINDS}
    for rec in recs:
        kd = rec["kind"]
        g = (math.log(rec["p2"]) - math.log(rec["p1"])) / (rec["x2"] - rec["x1"])
        e = min(rec.get("until", n), n)
        i = np.arange(rec["at"], e)
        if i.size == 0:
            continue
        G[kd][i] = g
        L[kd][i] = math.log(rec["p1"]) + g * (i - rec["x1"]) + (-lm if kd == "support" else lm)
    drawn = {kd: np.isfinite(L[kd]) for kd in KINDS}
    return dict(m=n, cl=cl_raw, G=G, L=L, drawn=drawn)


# ----------------------------------------------------------------------------- audits
def audit_prefix(lo, hi, cl, P, probes):
    """[F] the record up to bar t is unchanged when the series is cut at t."""
    full = swing_lines(lo, hi, cl, P)

    def upto(recs, t):
        out = []
        for r in recs:
            if r["at"] <= t:
                out.append((r["kind"], r["x1"], r["x2"], r["at"], min(r.get("until", 10 ** 9), t + 1) if r.get("until", 10 ** 9) <= t else None))
        return out

    for t in probes:
        cut = swing_lines(lo[:t + 1], hi[:t + 1], cl[:t + 1], P)
        if upto(full, t) != upto(cut, t):
            raise AssertionError(f"[F] the record up to bar {t} changed when the series was cut there")
    return len(probes)


def audit_ends(lo, hi, cl, recs, P):
    """[E] every BREAK end has the close through the drawn line by more than b on its end bar;
    every DRIFT end has no wick within p of the line for T bars. Reads the record only."""
    lm, ldeep, lp = math.log1p(P["m"]), math.log1p(P["b"]), math.log1p(P["p"])
    nb, nd = 0, 0
    for r in recs:
        if "until" not in r:
            continue
        g = (math.log(r["p2"]) - math.log(r["p1"])) / (r["x2"] - r["x1"])
        e = r["until"]
        line = math.log(r["p1"]) + g * (e - r["x1"]) + (-lm if r["kind"] == "support" else lm)
        if r["why"] == "BREAK":
            through = (line - cl[e]) if r["kind"] == "support" else (cl[e] - line)
            if not through > ldeep:
                raise AssertionError(f"[E] a BREAK end at {e} without the close through the line")
            nb += 1
        elif r["why"] == "DRIFT":
            ext = lo if r["kind"] == "support" else hi
            for t in range(e - P["T"] + 1, e + 1):
                lt = math.log(r["p1"]) + g * (t - r["x1"]) + (-lm if r["kind"] == "support" else lm)
                if abs(ext[t] - lt) <= lp:
                    raise AssertionError(f"[E] a DRIFT end at {e} with a touch at {t}")
            nd += 1
    return nb, nd


# ----------------------------------------------------------------------------- scoring
def score_hand(P, names, SC):
    H = json.loads(HAND.read_text(encoding="utf-8"))
    acc = SC.fresh()
    counts = dict(lines=0, BREAK=0, REPLACED=0, DRIFT=0, live=0)
    for k, rec in H.items():
        nm = names[k]
        lo, hi, cl = (np.log(np.array(nm[q], float)) for q in ("l", "h", "c"))
        recs = swing_lines(lo, hi, cl, P)
        N = records_to_N(recs, P["m"], lo.size, np.array(nm["c"], float))
        SC.score(N, rec, acc)
        for r0 in recs:
            if rec["start"] <= r0["at"] < rec["start"] + rec["n"]:
                counts["lines"] += 1
                counts[r0.get("why", "live")] += 1
    return SC.table(acc), counts


def composite(rows):
    """Distance from the principal's own numbers, smaller is better: recall toward 0.78, sign
    toward 0.90, |dgrad| toward 40 %/yr, lag toward 1 bar, overstay toward 0.20 -- averaged over
    the two kinds, each term scaled to its target's natural unit."""
    d = 0.0
    for kd in KINDS:
        r = rows[kd]
        d += abs(r["recall"] - 0.78) / 0.78 + abs(r["sign"] - 0.90) / 0.90 + abs(r["dgrad_med"] - 40) / 40 \
            + abs(r["lag_med"] - 1) / 10 + abs(r["overstay"] - 0.20) / 0.20
    return d / 2


def fmt(name, rows):
    out = []
    for kd, r in rows.items():
        out.append(f"  {name:<14s} {kd:<11s} {100 * r['recall']:>6.0f}% {100 * r['precision']:>6.0f}% "
                   f"{100 * r['sign']:>4.0f}% {r['dgrad_med']:>7.0f}% {r['dlevel_med']:>6.1f}% "
                   f"{r['lag_med']:>5.0f} {100 * r['matched']:>7.0f}% {100 * r['overstay']:>8.0f}%")
    return "\n".join(out)


HEADER = (f"  {'':<14s} {'kind':<11s} {'recall':>7s} {'precis':>7s} {'sign':>5s} {'|dgrad|':>8s} {'|dlvl|':>7s} "
          f"{'lag':>5s} {'matched':>8s} {'overstay':>9s}")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score", action="store_true")
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--line", default="")
    ap.add_argument("--sweep", action="store_true", help="the dial grid, ranked by the composite")
    a = ap.parse_args()
    SC = _load("d451sc", "d451_score_hand_lines.py")
    d = json.loads(LIVE.read_text())
    names = {nm["symbol"] + "-" + str(nm["start"]): nm for nm in d["names"]}

    if a.proof:
        nm = d["names"][0]
        lo, hi, cl = (np.log(np.array(nm[q], float)) for q in ("l", "h", "c"))
        P = parse_line(a.line or SETTINGS_LINE)
        recs = swing_lines(lo, hi, cl, P)
        pr = [int(v) for v in np.linspace(80, lo.size - 2, 7)]
        audit_prefix(lo, hi, cl, P, pr)
        print(f"  [F] the record up to each of {len(pr)} cut points is unchanged when the series is cut there  OK")
        nb, nd = audit_ends(lo, hi, cl, recs, P)
        print(f"  [E] {nb} BREAK ends each have the close through the line by > b; {nd} DRIFT ends each have no touch for T bars  OK")
        # [X] the ends audit must reject a record whose break did not happen
        bad = [dict(r0) for r0 in recs]
        for r0 in bad:
            if r0.get("why") == "BREAK":
                r0["until"] = r0["at"] + 1
                break
        try:
            audit_ends(lo, hi, cl, bad, P)
            raise SystemExit("[X] the ends audit accepted a moved break")
        except AssertionError:
            print(f"  [X] the ends audit rejects a break moved to a bar without one  OK")
        print(f"  {len(recs)} lines on {nm['symbol']}'s full history; "
              f"{sum(1 for r0 in recs if r0.get('why') == 'BREAK')} break, "
              f"{sum(1 for r0 in recs if r0.get('why') == 'REPLACED')} replaced, "
              f"{sum(1 for r0 in recs if r0.get('why') == 'DRIFT')} drift, "
              f"{sum(1 for r0 in recs if 'until' not in r0)} live")
        return 0

    if a.sweep:
        t0 = time.time()
        grid = []
        for r in (8, 10, 12, 15):
            for r2 in (3, 4, 5):
                for m in (2, 4):
                    for b in (2, 4):
                        for u in (4, 100):
                            grid.append(f"r={r} r2={r2} m={m} K=4 b={b} bbars=1 p=2 T=20 D=25 u={u}")
        res = []
        for line in grid:
            rows, counts = score_hand(parse_line(line), names, SC)
            res.append((composite(rows), line, rows, counts))
        res.sort(key=lambda z: z[0])
        print(f"  {len(grid)} lines scored in {time.time() - t0:.0f}s; the ten nearest the principal's numbers:")
        print(HEADER)
        for c, line, rows, counts in res[:10]:
            print(f"  composite {c:.3f}  {line}  ({counts['lines']} lines: {counts['BREAK']} break, {counts['REPLACED']} replaced, {counts['DRIFT']} drift)")
            print(fmt("SWING", rows))
        OUT.write_text(json.dumps(dict(what="D460 swing envelope: dial sweep scored against the hand-drawn lines",
                                       ranked=[dict(composite=c, line=line, rows=rows, counts=counts) for c, line, rows, counts in res]), indent=1))
        print(f"  written {OUT.relative_to(REPO)}")
        return 0

    line = a.line or SETTINGS_LINE
    rows, counts = score_hand(parse_line(line), names, SC)
    card = json.loads(CARD.read_text(encoding="utf-8"))["score"]
    print(f"  {line}  ({counts['lines']} lines on the panels: {counts['BREAK']} break, {counts['REPLACED']} replaced, {counts['DRIFT']} drift, {counts['live']} live)")
    print(HEADER)
    for name in ("PIVOT", "GROW", "HYST", "HYST-WIDE"):
        print(fmt(name, card[name]))
    print(fmt("SWING", rows))
    print(f"  composite distance from the principal's numbers: SWING {composite(rows):.3f}  |  "
          + "  ".join(f"{nme} {composite(card[nme]):.3f}" for nme in ("PIVOT", "GROW", "HYST", "HYST-WIDE")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
