import json
d=json.load(open("data/d290_entry_test.json")); R=d["results"]
D=json.load(open("data/d290_stage1.json")); AX=D["axes"]
SK=json.load(open("data/d290_skip_all.json"))
skipv={r["c"]:r for r in SK["rows"]}
rows=[]
for c,v in R.items():
    N=str(D["results"][c]["observed"]["spread"][0])
    k=str(D["results"][c]["observed"]["spread"][1])
    b=v.get(N)
    if not b: continue
    on,idr,tot=b["overnight_k1"],b["intraday_k1"],b["total_k1"]
    ce=b["close_entry"].get(k); oe=b["open_entry"].get(k)
    t=v["terciles_k1"]
    w=(t.get("wide") or {}).get(N); m=(t.get("mid") or {}).get(N)
    rows.append(dict(c=c,ax=AX[c],N=N,k=k,on=on,idr=idr,tot=tot,ce=ce,oe=oe,
                     wide=w,mid=m,skip=skipv.get(c,{}).get("verdict")))
rows.sort(key=lambda r: -(abs(r["tot"][1]) if r["tot"] else 0))
print(f"{'ax':2s} {'candidate':16s} {'N':>3s} | {'k=1 tot':>13s} {'overnight':>13s} "
      f"{'intraday':>13s} | {'on share':>8s} | {'wide':>8s} {'mid':>8s} {'w/m':>6s} | skip")
for r in rows[:24]:
    f=lambda x: f"{x[0]:+7.1f} t{x[1]:+4.1f}" if x else f"{'--':>13s}"
    sh=(r["on"][0]/r["tot"][0]) if (r["on"] and r["tot"] and r["tot"][0]) else None
    wm=(r["wide"][0]/r["mid"][0]) if (r["wide"] and r["mid"] and r["mid"][0]) else None
    print(f"{r['ax']:2s} {r['c']:16s} {r['N']:>3s} | {f(r['tot'])} {f(r['on'])} {f(r['idr'])} | "
          f"{(f'{sh:+7.0%}' if sh is not None else '   --  '):>8s} | "
          f"{(f'{r[chr(119)+chr(105)+chr(100)+chr(101)][0]:+8.1f}' if r['wide'] else '      --'):>8s} "
          f"{(f'{r[chr(109)+chr(105)+chr(100)][0]:+8.1f}' if r['mid'] else '      --'):>8s} "
          f"{(f'{wm:+6.1f}' if wm is not None else '    --'):>6s} | {r['skip']}")
print(f"\nSPREAD wide/mid = {d['tercile_half_spread_bp']['wide']/d['tercile_half_spread_bp']['mid']:.1f}x"
      f"  (a pure bounce edge should scale by about this)")
print("\nOPEN-ENTRY at each candidate's own peak k")
print(f"{'ax':2s} {'candidate':16s} {'N':>3s} {'k':>3s} | {'close entry':>13s} {'open entry':>13s} | {'kept':>6s}")
for r in sorted(rows,key=lambda r:-(r['ce'][1] if r['ce'] else -9))[:16]:
    f=lambda x: f"{x[0]:+7.1f} t{x[1]:+4.1f}" if x else f"{'--':>13s}"
    kp=(r['oe'][0]/r['ce'][0]) if (r['oe'] and r['ce'] and r['ce'][0]) else None
    print(f"{r['ax']:2s} {r['c']:16s} {r['N']:>3s} {r['k']:>3s} | {f(r['ce'])} {f(r['oe'])} | "
          f"{(f'{kp:+6.0%}' if kp is not None else '    --'):>6s}")
