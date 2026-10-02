import json, os, sys
R = r"C:\Users\O\Desktop\Projects\Backtest Framework\.claude\worktrees\after-d674"
for f in ['fut_day1m','fut_day1m_mid','fut_opening_globex_1m','fut_opening_globex_1m_cl_ng_gc_si',
          'fut_opening_globex_1m_ho_rb_bz_hg_pl','fut_opening_globex_1m_ym_rty','fut_premarket_1m',
          'fut_index_close_1m','fut_micro_day_volume','fut_index_anchor_bars']:
    p = os.path.join(R, 'data', 'fixtures', f + '.meta.json')
    m = json.load(open(p, encoding='utf-8'))
    print('=====', f)
    keys = list(m.keys())
    print('keys:', keys[:40])
    for k in ['description','what','columns','span','window','roots','rows','n_rows','path','file','window_et','clock','session_window','source','built','notes']:
        if k in m:
            v = m[k]
            s = json.dumps(v)
            print(f'  {k}: {s[:700]}')
    print(json.dumps(m)[:1200])
    print()
import glob
for pat in ['data/fixtures/*.parquet','data/fixtures/fut_*1m*.csv.gz','data/fixtures/fut_opening*','data/*.parquet']:
    for q in glob.glob(os.path.join(R, pat)):
        print(q, os.path.getsize(q)//1_000_000, 'MB')
