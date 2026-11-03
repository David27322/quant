"""Independent NumPy Monte Carlo check of one C++ IID scenario."""
from pathlib import Path
import json
import numpy as np
import pandas as pd

out=Path("/data/analysis/fhm_audit")
pool=np.loadtxt(out/"pool_primary.txt")
rng=np.random.default_rng(998877)
n=20000; pnl=np.zeros(n); phase=np.zeros(n,dtype=int)
days=np.zeros(n,dtype=int); alive=np.ones(n,dtype=bool)
won=np.zeros(n,dtype=bool); completion=np.full(n,-1)
for k in range(1,2521):
    a=np.flatnonzero(alive)
    if not len(a): break
    sample=pool[rng.integers(0,len(pool),size=len(a))]
    days[a]+=1
    adverse_loss=(sample[:,2]+2)*.8
    breach=(adverse_loss>=200)|(pnl[a]-adverse_loss<=-500)
    alive[a[breach]]=False
    b=a[~breach]; valid=sample[~breach]
    pnl[b]+=(valid[:,0]-2)*.8
    # An extra direct balance-floor check is retained, independent of MAE bounds.
    hit_floor=pnl[b]<=-500
    alive[b[hit_floor]]=False
    b=b[~hit_floor]
    target=np.where(phase[b]==0,400,200)
    hit=(pnl[b]>=target)&(days[b]>=2)
    winners=b[hit]
    final=winners[phase[winners]==1]
    won[final]=True;alive[final]=False;completion[final]=k
    reset=winners[phase[winners]==0]
    phase[reset]=1;pnl[reset]=0;days[reset]=0
p=float(won.mean())
check={"engine":"Independent NumPy path simulation, separate RNG",
       "scenario":"IID, lot0.08, cost2pt, static10%, MAE upper,2520 total opportunities",
       "n":n,"p_pass":p,"unfinished":int(alive.sum()),
       "successful_median_opportunities":float(np.median(completion[won]))}
(out/"independent_numpy_check.json").write_text(json.dumps(check,indent=2))
print(json.dumps(check,indent=2))