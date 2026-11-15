"""Regional PV average costs and demand-weighted, de-discounted balance duals."""
import re
import subprocess
import sys
import tempfile
from pathlib import Path
import numpy as np
import pandas as pd


def costs(repo, folder, book, scenario):
    sys.path.insert(0, str(repo))
    from extract_jicama_lmp import load_dsd, period_weight
    def is_server_tech(t):
        return t.startswith(("server_", "dc_")) or t.endswith("_dc")
    pct = {'no_servers': 0, 'unregulated': 0, 'covered_50': 50, 'covered_100': 100}[scenario]
    db = repo / 'three_pillars' / (f'conus_26z_elote_pct{pct}_conv_template_geo_3360h.sqlite' if pct else 'conus_26z_lychee_3360h.sqlite')
    corr = repo / ('manzana/output_cost_dumps/'+folder+'_truncation.csv' if pct else 'manzana/'+('conus_lulo_no_dc_duals_truncation.csv' if scenario=='no_servers' else 'conus_lulo_geo_baseline_truncation.csv'))
    if not corr.exists():
        corr = Path(tempfile.gettempdir()) / (folder+'_dashboard_truncation.csv')
        subprocess.run([sys.executable,str(repo/'manzana/correct_myopic_capital_cost.py'),str(db),'--cost-csv',str(book.parent/'output_cost.csv'),'--view-depth','1','--step-size','1','--csv',str(corr)],check=True,stdout=subprocess.DEVNULL)
    c=pd.read_excel(book,sheet_name='Costs'); adj=pd.read_csv(corr)
    a=pd.read_excel(book,sheet_name='Activity_distribution')
    weights={y:period_weight(db,y)[0] for y in (2027,2030,2035,2040)}
    rates={}
    for side,tech in [('public','elec_distribution'),('server','server_distribution')]:
        mask=c.Technology.map(is_server_tech)==(side=='server')
        amask=adj.tech.map(is_server_tech)==(side=='server')
        money=c[mask].groupby('Region').Cost.sum().add(adj[amask].groupby('region').delta_d_invest.sum(),fill_value=0)
        energy=a[a.Technology==tech].groupby('Region')[[*weights]].sum()
        pv=sum(energy[y]*w for y,w in weights.items())
        rates[side]=money/pv.replace(0,np.nan)
    if scenario=='no_servers': rates['server']=pd.Series(dtype=float)
    elif pct==0: rates['server']=rates['public'].copy()
    else: rates['server']=rates['server']*(pct/100)+rates['public']*(1-pct/100)
    rx=re.compile(r"commodity_balance_constraint\[([A-Za-z0-9]+),(\d+),(p\d+),'(\d+)',(electricity|server_electricity)\]")
    path=book.parent/'commodity_duals.csv.gz'
    if not path.exists(): path=book.parent/'commodity_duals.csv'
    sums={}
    dsds={y:load_dsd(db,y) for y in weights}
    for chunk in pd.read_csv(path,chunksize=500000):
        chunk=chunk[chunk.constraint_name.str.endswith((',electricity]',',server_electricity]'))]
        for row in chunk.itertuples():
            m=rx.fullmatch(row.constraint_name)
            if not m: continue
            r,y,s,t,comm=m.groups();y=int(y)
            if y not in weights or not row.scenario.endswith('-'+str(y)):continue
            side='public' if comm=='electricity' else 'server'
            demand='DEMAND_ELC' if side=='public' else 'DEMAND_SERVERS_45V'
            w=dsds[y].get(demand,{}).get((r,s,int(t)))
            if w is None:continue
            k=(r,y,side);num,den=sums.get(k,(0,0));sums[k]=(num+w*row.dual,den+w)
    marginal={k:n/d/weights[k[1]] for k,(n,d) in sums.items() if d>0}
    out={}
    for r in set(a.Region):
        for y in weights:
            pub=marginal.get((r,y,'public'),np.nan)
            srv=marginal.get((r,y,'server'),np.nan)
            if scenario=='no_servers':srv=np.nan
            elif pct==0:srv=pub
            vals=[rates['public'].get(r,np.nan),rates['server'].get(r,np.nan),pub,srv]
            if r=='NYCW':vals=[np.nan]*4
            out[r,y]=['' if not np.isfinite(v) else round(v,5) for v in vals]
    print('Exported costs:',scenario,flush=True)
    return out
