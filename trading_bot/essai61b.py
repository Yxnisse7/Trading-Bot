"""Essai 61, complément (non pré-enregistré) : copie AlxCooks avec frais pump.fun seuls, ventes copiées au même pourcentage."""
import numpy as np, pandas as pd
from .essai38 import FEE, NET_FEE, STAKE, MAX_HOLD, PF_DIR, stats
from .essai60 import run, AXIOM
d=np.load(PF_DIR/"early.npz"); TS,P,VS,VT,start=d["ts"],d["p"],d["vs"],d["vt"],d["start"]; grad,mints=d["grad"],d["mints"]
idx={m:i for i,m in enumerate(mints)}
al=pd.read_parquet(PF_DIR/"streamer_all.parquet")
def arr(t): s,e=start[t],start[t+1]; return TS[s:e],P[s:e],VS[s:e],VT[s:e]
def copy_pct(t, rows, delay, fee):
    ts,p,vs,vt=arr(t); b=rows.ts.iloc[0]
    j=np.searchsorted(ts,b+delay); 
    if j>=len(ts) or ts[j]>=grad[t]: return None
    deadline=min(ts[j]+MAX_HOLD,grad[t]); hi=np.searchsorted(ts,deadline,side="right")
    his=0.0; x=STAKE*(1-fee); held=x/(p[j]*(1+x/vs[j])); out=0.0; tx=1
    for _,r in rows.iterrows():
        if r.is_buy: his+=r.token_amount; continue
        if his<=0 or held<=0: continue
        frac=min(r.token_amount/his,1.0); his-=r.token_amount
        if r.ts+delay>deadline: break
        e=max(min(np.searchsorted(ts,r.ts+delay),hi-1),j); q=held*frac if frac<0.999 else held
        out+=q*p[e]/(1+q/vt[e])*(1-fee); held-=q; tx+=1
    if held>0:
        e=hi-1; out+=held*p[e]/(1+held/vt[e])*(1-fee); tx+=1
    cost=STAKE+NET_FEE; return 100*(out-(tx-1)*NET_FEE-cost)/cost
res={}
for delay in (1,3,10):
  for name,fee in (("pumpfun",FEE),("axiom",FEE+AXIOM)):
    x1,xp=[],[]
    for m,rows in al.groupby("mint",sort=False):
        t=idx.get(m)
        if t is None: continue
        rows=rows.sort_values("ts"); b=rows.ts.iloc[0]; ts=arr(t)[0]
        j=np.searchsorted(ts,b+delay)
        if j>=len(ts) or ts[j]>=grad[t]: continue
        sells=rows[~rows.is_buy]; s=None if sells.empty else sells.ts.iloc[0]
        x1.append(run(*arr(t),j,grad[t],"at",None if s is None else s+delay-2.0,fee))
        v=copy_pct(t,rows,delay,fee)
        if v is not None: xp.append(v)
    for k,v in (("tout_a_sa_1re_vente",x1),("meme_pourcentage",xp)):
        st=stats(np.array(v)); print(delay,name,k,st["n"],st["moy"],st["pf"],st["perdants_pct"])
