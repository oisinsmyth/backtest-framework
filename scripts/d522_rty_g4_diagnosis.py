"""D522 -- every number in the record: why RTY failed G4, and how narrow the amendment is.

Four questions, in the order they were actually asked:

  1. is the disagreement CONCENTRATED, or spread across the sample?
  2. is the FUTURES side wrong? (check it against `fut_sessions_hourly`, an independent builder over
     the same archive) -- or the EQUITY side? (the equity fixture ships a `suspect` flag the gate
     ignores)
  3. what happened on the offending morning, and is it market-wide?
  4. how selective is the amendment -- how many sessions does "no continuous open" exclude, on every
     root, and what does excluding them do?

    python scripts/d522_rty_g4_diagnosis.py            # -> data/d522_rty_g4_diagnosis.json

Reads committed fixtures only. No archive, no databento, either interpreter.
"""
from __future__ import annotations
import json, sys, time
from pathlib import Path
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import build_fut_index_1m as ix  # noqa: E402

OUT = REPO / "data" / "d522_rty_g4_diagnosis.json"
DAY = "2020-03-16"
ROOT = "RTY"


def legs(eq, sess, root):
    """The two sides of G4 for one root, exactly as the gate builds them."""
    e = eq[eq["symbol"] == ix.ETF[root]]
    ed = pd.DataFrame({"eo": e[e["hhmm"] == "09:30"].groupby("day")["open"].first(),
                       "ec": e[e["hhmm"] == "15:45"].groupby("day")["close"].last(),
                       "susp_o": e[e["hhmm"] == "09:30"].groupby("day")["suspect"].max(),
                       "susp_c": e[e["hhmm"] == "15:45"].groupby("day")["suspect"].max()}).dropna(subset=["eo", "ec"])
    f = sess[sess["root"] == root].set_index("day")[["p0930", "p1600", "contract", "bars"]].dropna(subset=["p0930", "p1600"])
    j = f.join(ed, how="inner")
    j["oc_f"] = j["p1600"] / j["p0930"] - 1
    j["oc_e"] = j["ec"] / j["eo"] - 1
    j["gap"] = j["oc_f"] - j["oc_e"]
    return j


def main():
    t0 = time.time()
    r = dict(run_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
    eq = pd.read_csv(ix.EQ_FIX, dtype={"timestamp": str, "symbol": str})
    eq["day"] = eq["timestamp"].str[:10]; eq["hhmm"] = eq["timestamp"].str[11:16]
    sess = pd.read_csv(ix.FIX / "fut_index_sessions.csv.gz", dtype={"day": str, "contract": str})
    bars = {root: pd.read_csv(ix.fixture_path(root), dtype={"day": str, "hhmm": str, "contract": str}) for root in ix.ROOTS}

    print("== 1. is the RTY disagreement concentrated?")
    j = legs(eq, sess, ROOT)
    base = float(np.corrcoef(j["oc_f"], j["oc_e"])[0, 1])
    assert abs(base - 0.9898535763214892) < 1e-12, f"this is not the gate's own number: {base}"
    order = j["gap"].abs().sort_values(ascending=False).index
    drops = {}
    for n in (1, 2, 3, 5, 10, 20, 50):
        k = j.drop(index=order[:n])
        drops[n] = float(np.corrcoef(k["oc_f"], k["oc_e"])[0, 1])
        print(f"   drop the {n:>2} worst -> {drops[n]:.6f}")
    worst = [dict(day=d, contract=j.loc[d, "contract"], futures_pct=round(100 * j.loc[d, "oc_f"], 3),
                  etf_pct=round(100 * j.loc[d, "oc_e"], 3), gap_pct=round(100 * j.loc[d, "gap"], 3),
                  bars=int(j.loc[d, "bars"])) for d in order[:5]]
    r["concentration"] = dict(corr_all_days=base, matched_days=int(len(j)), corr_after_dropping=drops,
                              worst_five=worst, ratio_worst_to_second=round(abs(j.loc[order[0], "gap"] / j.loc[order[1], "gap"]), 2))
    print(f"   the worst day is {r['concentration']['ratio_worst_to_second']}x the second")

    print("== 2. which side is wrong?")
    h = pd.read_csv(ix.FIX / "fut_sessions_hourly.csv.gz", dtype={"root": str, "day": str},
                    usecols=["root", "day", "h09_o", "h09_n", "h15_c"])
    h = h[h["root"] == ROOT].set_index("day")
    h["oc_h"] = h["h15_c"] / h["h09_o"] - 1
    m = j.join(h[["oc_h"]], how="inner").dropna(subset=["oc_h"])
    d = (m["oc_f"] - m["oc_h"]).abs()
    # the two builders' CLOSE leg is the same object; their OPEN leg is not -- h09_o is the 09:00 hour's
    # open, so it normally sits a point or two from p0930. An EXACT match is therefore informative: it
    # says the contract did not move between 09:00 and 09:30.
    q = j.join(h[["h09_o", "h09_n", "h15_c"]], how="inner").dropna(subset=["h09_o"])
    same_open = (q["h09_o"] - q["p0930"]).abs()
    r["independent_builder"] = dict(
        days=int(len(m)), corr_1m_vs_hourly=float(np.corrcoef(m["oc_f"], m["oc_h"])[0, 1]),
        abs_diff_p50=float(d.median()), abs_diff_p99=float(d.quantile(0.99)),
        close_leg_exact_days=int((q["h15_c"] - q["p1600"]).abs().eq(0).sum()), shared_days=int(len(q)),
        open_leg_abs_diff_p50=float(same_open.median()), open_leg_abs_diff_p90=float(same_open.quantile(0.9)),
        open_leg_exact_days=int(same_open.eq(0).sum()),
        on_the_day=dict(one_minute=round(100 * float(j.loc[DAY, "oc_f"]), 3),
                        hourly=round(100 * float(h.loc[DAY, "oc_h"]), 3),
                        h09_open=float(q.loc[DAY, "h09_o"]), p0930=float(q.loc[DAY, "p0930"]),
                        h09_minute_bars=int(q.loc[DAY, "h09_n"]), h09_minute_bars_p50=float(q["h09_n"].median())))
    print(f"   close leg identical on {r['independent_builder']['close_leg_exact_days']}/{len(q)} days; "
          f"open leg differs by p50 {same_open.median():.2f} pts and matches EXACTLY on {int(same_open.eq(0).sum())} days")
    print(f"   on {DAY} the 09:00 open and the 09:30 open are both {q.loc[DAY,'h09_o']}, on {int(q.loc[DAY,'h09_n'])} minute bars "
          f"against a median {q['h09_n'].median():.0f} -- the contract did not move for half an hour")
    r["equity_suspect_flag"] = dict(days_flagged=int(((j["susp_o"] > 0) | (j["susp_c"] > 0)).sum()), of_days=int(len(j)))
    print(f"   1m vs hourly on {DAY}: {r['independent_builder']['on_the_day']}; median |diff| {d.median():.2e}")
    print(f"   equity bars flagged suspect: {r['equity_suspect_flag']['days_flagged']} of {len(j)}")

    print(f"== 3. what happened on {DAY}?")
    morning, wide = {}, {}
    for root in ix.ROOTS:
        b = bars[root]; dd = b[b["day"] == DAY].sort_values("hhmm")
        if not len(dd):
            continue
        missing = [m_ for m_ in ix.OPEN_MIN if m_ not in set(dd["hhmm"])]
        morning[root] = dict(bars=int(len(dd)), first=dd["hhmm"].iat[0], missing_in_open_window=missing,
                             first_print=dict(hhmm=dd["hhmm"].iat[0], open=float(dd["open"].iat[0]), high=float(dd["high"].iat[0]),
                                              low=float(dd["low"].iat[0]), close=float(dd["close"].iat[0]), volume=int(dd["volume"].iat[0])),
                             reopen=dict(hhmm=dd["hhmm"].iat[1], open=float(dd["open"].iat[1]), low=float(dd["low"].iat[1]), volume=int(dd["volume"].iat[1])) if len(dd) > 1 else None)
        jj = legs(eq, sess, root)
        if DAY in jj.index:
            wide[root] = dict(futures_pct=round(100 * float(jj.loc[DAY, "oc_f"]), 2), etf_pct=round(100 * float(jj.loc[DAY, "oc_e"]), 2),
                              gap_pct=round(100 * float(jj.loc[DAY, "gap"]), 2))
        print(f"   {root:<4} {morning[root]['bars']} bars, first print {morning[root]['first_print']}, "
              f"missing {len(missing)} of the open window; gap {wide.get(root, {}).get('gap_pct')} pts")
    thin = {}
    for root in ix.ROOTS:
        e = eq[(eq["symbol"] == ix.ETF[root]) & (eq["hhmm"] == "09:30")].sort_values("day").reset_index(drop=True)
        med = e["volume"].rolling(60, min_periods=20).median().shift(1)
        row = e[e["day"] == DAY]
        thin[ix.ETF[root]] = dict(volume=int(row["volume"].iat[0]), trailing_median=float(med[row.index[0]]),
                                  ratio=round(float(row["volume"].iat[0]) / float(med[row.index[0]]), 4))
        print(f"   {ix.ETF[root]} 09:30 bar volume is {thin[ix.ETF[root]]['ratio']:.3f} of its trailing median")
    r["the_session"] = dict(day=DAY, futures_morning=morning, all_roots=wide, etf_opening_bar_thinness=thin)

    print("== 4. how selective is the amendment?")
    per = {}
    for root in ix.ROOTS:
        holed = ix.discontinuous_open(bars[root])
        jj = legs(eq, sess, root)
        keep = ~jj.index.isin(holed)
        full = float(np.corrcoef(jj["oc_f"], jj["oc_e"])[0, 1])
        cut = float(np.corrcoef(jj["oc_f"][keep], jj["oc_e"][keep])[0, 1])
        per[root] = dict(sessions=int(bars[root]["day"].nunique()), flagged=sorted(holed),
                         matched_days=int(len(jj)), excluded_from_g4=sorted(set(jj.index) & holed),
                         corr_all_days=full, corr_continuous_open=cut, bar=ix.G4_OC[root],
                         passes_before=bool(full >= ix.G4_OC[root]), passes_after=bool(cut >= ix.G4_OC[root]))
        print(f"   {root:<4} flags {len(holed)} of {per[root]['sessions']:,} sessions ({100*len(holed)/per[root]['sessions']:.2f}%): "
              f"{full:.6f} ({'pass' if per[root]['passes_before'] else 'FAIL'}) -> {cut:.6f} ({'pass' if per[root]['passes_after'] else 'FAIL'})")
    r["amendment"] = dict(open_window=[ix.OPEN_MIN[0], ix.OPEN_MIN[-1]], max_excluded=ix.G4_MAX_EXCLUDED, per_root=per,
                          flagged_on_all_four=sorted(set.intersection(*(set(per[x]["flagged"]) for x in ix.ROOTS))))
    print(f"   flagged on all four roots at once: {r['amendment']['flagged_on_all_four']}")

    OUT.write_text(json.dumps(r, indent=1, default=float))
    print(f"\nwrote {OUT.relative_to(REPO)} in {time.time()-t0:.0f}s")


if __name__ == "__main__":
    main()
