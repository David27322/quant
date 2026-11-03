"""Reproducible offline audit. No source changes and no funded-payout claims."""
from pathlib import Path
import hashlib, importlib.util, json, math, subprocess
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import numpy as np
import pandas as pd
import exchange_calendars as xc

ROOT=Path("/data"); OUT=ROOT/"analysis/fhm_audit"; OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location("baseline",ROOT/"raw/run_all_gates.py")
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
rng=np.random.default_rng(20261015)
evidence={
 "scope":"Historical data/code audit and conditional two-phase target-before-loss simulations",
 "not_claimed":["live expectancy","full prop-rule compliance","funded lifetime payouts","optimal reinvestment","recent performance after 2026-06-25"],
 "known":{"account_USD":5000,"point_value_USD_per_point_per_lot":10,"stop_points":40,"target_points":80,"lot_step":0.01,"phase_targets_USD":[400,200],"daily_limit_USD":200,"minimum_trade_days_each_phase":2,"maximum_loss_scenarios":[.08,.10]},
 "assumptions":[
  "Price timestamps follow the user-confirmed UTC-to-NY pipeline; independently reproduced for 2023 only.",
  "Fixed lot size throughout both phases; risk is relative to INITIAL $5000, not compounded.",
  "Primary pool uses original fixed strategy, 15:55 BID-open exit proxy and observed stop-gap-open adjustment; not actual fills.",
  "All-in round-trip cost scenarios 1/2/3 index points are hypothetical; not measured FundedNext costs.",
  "Same scalar cost is deducted from each closed trade; entire amount also charged up-front for intratrade equity checking.",
  "Recorded price-bar open beyond an existing stop is used as a gap proxy; all other stop/target fills are ideal.",
  "Equity MAE upper bound assumes adverse exit-bar extreme could precede target; lower/upper tested separately.",
  "One sampled trading opportunity per trading day; opportunity counts are NOT calendar days.",
  "8% and 10% STATIC total-loss floors are separate challenge scenarios, each reset for phase 2; 4% daily unchanged.",
  "Cash-calendar exclusions use exchange_calendars XNAS alias (XNYS implementation) as a sensitivity proxy, not a fully verified Nasdaq historical schedule.",
  "IID resampling assumes exchangeability; circular blocks of 20 trading opportunities preserve only local observed ordering.",
  "Simulation horizon 2520 opportunities ACROSS BOTH phases; unfinished paths reported separately, never called eventual failure.",
  "Quick Strike progression restrictions, other discretionary compliance reviews and issuance delays are NOT modeled.",
  "Latest data gap and future regime shifts are not modeled."
 ],
 "hashes":{},
}
for name in ["usa100_clean.csv","ndx_2023.csv","run_all_gates.py","first_hour_momentum.mq5"]:
 p=ROOT/"raw"/name
 evidence["hashes"][name]=hashlib.sha256(p.read_bytes()).hexdigest()

# Re-run prior reconstruction and timing tests before using exported path bounds.
subprocess.run(["python3",str(ROOT/"analysis/validate_source_timezone.py")],check=True,stdout=(OUT/"timezone_run.log").open("w"))
subprocess.run(["python3",str(ROOT/"analysis/execution_audit.py")],check=True,stdout=(OUT/"execution_run.log").open("w"))
df=m.load_data(str(ROOT/"raw/usa100_clean.csv"))
base=m.run_backtest(df)
t=pd.read_csv(ROOT/"analysis/1555_open_proxy_audit_trades.csv")
gross=t["gross_pts"].to_numpy().copy()
gap_details=[]
for i,row in t[t.stop_gap_flag].iterrows():
 g=df[df.d.astype(str)==row.date]
 px=float(g.loc[g.t==row.exit_time,"open"].iloc[0])
 gap_gross=int(row.direction)*(px-float(row.entry))
 assert gap_gross<=-40+1e-8
 gross[i]=gap_gross
 t.loc[i,"mae_lower_R"]=max(float(row.mae_lower_R),-gap_gross/40)
 t.loc[i,"mae_upper_R"]=max(float(row.mae_upper_R),-gap_gross/40)
 gap_details.append({"date":row.date,"original_stop_gross_pts":-40,"gap_proxy_gross_pts":gap_gross})
t["gross_pts_gap_proxy"]=gross
t.to_csv(OUT/"audited_trade_paths.csv",index=False)
calendar=xc.get_calendar("XNAS",start="2021-01-01",end="2026-06-26")
sessions=set(calendar.sessions.strftime("%Y-%m-%d"))
cash=t.date.isin(sessions).to_numpy()
early=set(calendar.early_closes.strftime("%Y-%m-%d"))
evidence["calendar"]={"implementation":type(calendar).__name__,"non_session_trade_dates":t.loc[~cash,"date"].tolist(),"early_close_trade_dates":t.loc[t.date.isin(early),"date"].tolist(),"dates_removed_from_original":0}
evidence["gap_proxy_adjustments"]=gap_details
evidence["timezone_validation"]=json.loads((ROOT/"analysis/source_timezone_validation.json").read_text())

# Focused data/code tests. These test Python logic / a translation, not compiled MQL5.
tests={}
synthetic=pd.DataFrame({"timestamp":pd.to_datetime(["2024-01-03 09:30","2024-01-03 10:30","2024-01-03 10:31","2024-01-03 15:55"]),
 "open":[1000,1001,1002,1002],"high":[1000,1001,1100,1002],"low":[1000,1001,950,1002],"close":[1000,1001,1002,1002]})
synthetic["t"]=synthetic.timestamp.dt.strftime("%H:%M"); synthetic["d"]=synthetic.timestamp.dt.date
tests["both_levels_same_bar_uses_stop"]=bool(np.isclose(m.run_backtest(synthetic).R.iloc[0],-1.025))
mut=synthetic.copy(); mut.loc[3,["open","high","low","close"]]=[2000,3000,100,2500]
tests["after_exit_mutation_no_change"]=bool(np.isclose(m.run_backtest(synthetic).R.iloc[0],m.run_backtest(mut).R.iloc[0]))
skip=synthetic.copy(); skip.loc[2,"t"]="10:32"
tests["missing_1031_silently_enters_next_bar_detected"]=len(m.run_backtest(skip))==1
def ea_offset(dt):
 y=dt.year
 def first_sun(month):
  d=datetime(y,month,1,tzinfo=timezone.utc)
  return 1+(6-d.weekday())%7
 start=datetime(y,3,first_sun(3)+7,7,tzinfo=timezone.utc)
 end=datetime(y,11,first_sun(11),6,tzinfo=timezone.utc)
 return -4 if start<=dt<end else -5
checks=[]
for y in range(2021,2027):
 for dt in pd.date_range(f"{y}-01-01",f"{y}-12-31 23:00",freq="h",tz="UTC"):
  checks.append(ea_offset(dt.to_pydatetime())==int(dt.to_pydatetime().astimezone(ZoneInfo("America/New_York")).utcoffset().total_seconds()/3600))
tests["EA_DST_translation_matches_zoneinfo_hourly_2021_2026"]=all(checks)
tests["DST_hourly_test_cases"]=len(checks)
tests["source_2023_exact_match"]=evidence["timezone_validation"]["exact_match"]
tests["baseline_R_independent_sum"]=math.isclose(math.fsum(base.net_pts)/40,float(base.R.sum()),abs_tol=1e-9)
evidence["tests"]=tests

def stats(r):
 r=np.asarray(r,float)
 return {"n":len(r),"mean_R":float(r.mean()),"total_R":float(r.sum()),
         "PF":float(r[r>0].sum()/-r[r<0].sum()),"sd_R":float(r.std(ddof=1))}
stats_rows=[]
for name,pts in [("original",base.net_pts.to_numpy()+1),("1555_open_proxy",t.gross_pts.to_numpy()),("1555_open_and_gap_proxy",gross),("cash_calendar_proxy",gross[cash])]:
 for cost in [1,2,3]:
  stats_rows.append({"pool":name,"cost_points":cost,**stats((pts-cost)/40)})
pd.DataFrame(stats_rows).to_csv(OUT/"historical_sensitivities.csv",index=False)
evidence["historical_sensitivities"]=stats_rows
yr=[]
for year in range(2021,2027):
 mask=t.date.str.startswith(str(year)).to_numpy()
 yr.append({"year":year,"partial_year":year==2026,**stats((gross[mask]-2)/40)})
pd.DataFrame(yr).to_csv(OUT/"yearly_2point_proxy.csv",index=False)
evidence["yearly_2point_proxy"]=yr

# Mark subminute ambiguity; do not call minute bars Quick-Strike compliant.
quick=(t.exit_bar_index==0)&(gross-1>0)
evidence["quick_strike"]={"profitable_entry_bar_exits":int(quick.sum()),"candidate_dates":t.loc[quick,"date"].tolist(),"claim":"Only candidates under exact minute-open entry, not actual sub-30s durations; no compliance guarantee."}

# Empirical block-bootstrap edge range, without pretending this captures selection bias.
edge=[]
for b in [1,5,20,60]:
 means=[]
 for rep in range(2000):
  starts=rng.integers(0,len(gross),size=math.ceil(len(gross)/b))
  ix=((starts[:,None]+np.arange(b))%len(gross)).ravel()[:len(gross)]
  means.append(float(((gross[ix]-2)/40).mean()))
 edge.append({"block_length":b,"bootstrap_reps":2000,"mean_R_q05":float(np.quantile(means,.05)),"mean_R_q95":float(np.quantile(means,.95))})
evidence["edge_bootstrap_sensitivity"]=edge

pools={"primary":np.column_stack([gross,40*t.mae_lower_R,40*t.mae_upper_R]),
       "cash":np.column_stack([gross,40*t.mae_lower_R,40*t.mae_upper_R])[cash]}
for name,a in pools.items(): np.savetxt(OUT/f"pool_{name}.txt",a,fmt="%.12g")
np.savetxt(OUT/"pool_win.txt",[[80,0,0]])
np.savetxt(OUT/"pool_loss.txt",[[-40,40,40]])
np.savetxt(OUT/"pool_equity.txt",[[80,600,600]]) # Positive close, intratrade breach.
cases=[]; counter=0
def add(id,pool,cost,lot,dd,block=20,horizon=2520,n=20000,upper=1,meta=None):
 global counter
 counter+=1
 row=dict(id=id,pool=pool,cost=cost,lot=lot,dd=dd,block=block,horizon=horizon,n=n,seed=2026101500+counter,upper=upper)
 if meta: row.update(meta)
 cases.append(row)
add("test_win","win",0,.1,.08,n=100,horizon=50)
add("test_loss","loss",0,.1,.08,n=100,horizon=50)
add("test_equity","equity",0,.1,.08,n=100,horizon=50)
lots=[.02,.03,.04,.05,.06,.08,.09,.12]
for cost in [1,2,3]:
 for dd in [.08,.10]:
  for lot in lots:
   for block in [1,20]:
    add(f"main_c{cost}_d{int(dd*100)}_l{int(round(lot*100)):02}_b{block}","primary",cost,lot,dd,block)
for lot in [.03,.08,.09]:
 for dd in [.08,.10]:
  add(f"cash_l{int(lot*100):02}_d{int(dd*100)}","cash",2,lot,dd)
  add(f"lower_l{int(lot*100):02}_d{int(dd*100)}","primary",2,lot,dd,upper=0)
  add(f"short_l{int(lot*100):02}_d{int(dd*100)}","primary",2,lot,dd,horizon=1200)
# Nested bootstrap: uncertainty sensitivity at two candidate sizes, 2-point cost.
# Outer circular blocks resample the historical pool; inner block paths use that pool.
for rep in range(80):
 b=20; starts=rng.integers(0,len(gross),size=math.ceil(len(gross)/b))
 ix=((starts[:,None]+np.arange(b))%len(gross)).ravel()[:len(gross)]
 name=f"boot{rep:03}"; np.savetxt(OUT/f"pool_{name}.txt",pools["primary"][ix],fmt="%.12g")
 for lot in [.03,.08]:
  for dd in [.08,.10]:
   add(f"boot_r{rep:03}_l{int(lot*100):02}_d{int(dd*100)}",name,2,lot,dd,n=1500,meta={"bootstrap_rep":rep})
pd.DataFrame(cases).to_csv(OUT/"simulation_cases.csv",index=False)
with (OUT/"cases.txt").open("w") as f:
 for c in cases:
  f.write(f"{c['id']} {OUT}/pool_{c['pool']}.txt {c['cost']} {c['lot']} {c['dd']} {c['block']} {c['horizon']} {c['n']} {c['seed']} {c['upper']}\n")
subprocess.run(["g++","-O3","-std=c++17",str(ROOT/"analysis/fhm_mc.cpp"),"-o",str(OUT/"fhm_mc")],check=True)
subprocess.run([str(OUT/"fhm_mc"),str(OUT/"cases.txt"),str(OUT/"simulation_results.csv")],check=True)
res=pd.read_csv(OUT/"simulation_results.csv")
assert (res["pass"]+res.overall_breach+res.daily_breach+res.unfinished==res.n).all()
assert (res.phase1_pass>=res["pass"]).all()
assert int(res.loc[res.id=="test_win","pass"].iloc[0])==100
assert int(res.loc[res.id=="test_loss","pass"].iloc[0])==0
assert int(res.loc[res.id=="test_equity","pass"].iloc[0])==0
# All-win at .1 lot: +$80 per trade; 5 phase-1 days + 3 phase-2 days.
assert float(res.loc[res.id=="test_win","median_days"].iloc[0])==8
merged=pd.DataFrame(cases).merge(res,on=["id","n"],validate="one_to_one")
merged.to_csv(OUT/"all_simulations.csv",index=False)
main=merged[merged.id.str.startswith("main_")].copy()
main["nominal_initial_risk_percent"]=main.lot*8
main.to_csv(OUT/"main_simulations.csv",index=False)
boot=merged[merged.id.str.startswith("boot_")]
unc=[]
for (lot,dd),g in boot.groupby(["lot","dd"]):
 unc.append({"lot":lot,"dd":dd,"outer_reps":len(g),"inner_paths_per_rep":1500,
             "p_q05":float(g.p_pass.quantile(.05)),"p_median":float(g.p_pass.median()),"p_q95":float(g.p_pass.quantile(.95))})
evidence["bootstrap_probability_sensitivity"]=unc
evidence["selected_main"]=main[(main.cost==2)&(main.block==20)].to_dict("records")
evidence["sensitivity_cases"]=merged[merged.id.str.startswith(("cash_","lower_","short_"))].to_dict("records")
evidence["simulation_validation"]={"conservation_checks":True,"deterministic_win_loss_equity_cases":True,"cases":len(res),"paths":int(res.n.sum()),"source":"fhm_mc.cpp compiled with g++ -O3 -std=c++17"}
evidence["visual_plan"]=[
 {"comparison":"Modeled target-before-loss probability by fixed lot, 8/10% loss floors and 1/2pt costs","grain":"simulation scenario","population":"primary 2021-2026 trade pool, blocks20,2520 horizon","unit":"percent","disposition":"chart","reason":"Shows cost and sizing dependence; not a live pass probability"},
 {"comparison":"Successful-path time and unresolved cases","grain":"scenario","population":"same simulation paths","unit":"opportunities","disposition":"table","reason":"Selected exact values complement probability curve; full CSV available"},
 {"comparison":"Calendar, gap and MAE sensitivity","grain":"scenario","population":"declared alternative pools","unit":"R and probability","disposition":"prose","reason":"Audit robustness rather than another dashboard"},
 {"comparison":"Yearly results","grain":"year","population":"primary proxy,2pt","unit":"R","disposition":"table","reason":"Preserve all years including partial2026 without extrapolating recent decay"}
]
chart={"version":1,"form":"multiline","title":"Lower fixed lots raise modeled survival—not speed",
 "aside":"Conditional two-phase target-before-loss estimates · 20-trade blocks · 2,520-opportunity cap · costs unmeasured",
 "labels":[f"{lot:.2f}" for lot in lots],"axis":{"zero":True},"series":[],
 "colorMap":{"8% floor · 1pt cost":"blue","10% floor · 1pt cost":"teal","8% floor · 2pt cost":"orange","10% floor · 2pt cost":"purple"}}
for cost,dd,label in [(1,.08,"8% floor · 1pt cost"),(1,.10,"10% floor · 1pt cost"),(2,.08,"8% floor · 2pt cost"),(2,.10,"10% floor · 2pt cost")]:
 g=main[(main.cost==cost)&(main.dd==dd)&(main.block==20)].sort_values("lot")
 chart["series"].append({"label":label,"valueKind":"percent","role":"subject","data":(g.p_pass*100).tolist()})
(OUT/"probability_chart.json").write_text(json.dumps(chart,indent=2))
(OUT/"evidence.json").write_text(json.dumps(evidence,indent=2,default=str))
print("VALIDATED",evidence["simulation_validation"])
print("HISTORICAL",json.dumps(stats_rows))
print("MAIN",main[(main.cost==2)&(main.block==20)][["lot","dd","p_pass","median_days","unfinished","n"]].to_string(index=False))
print("BOOTSTRAP",json.dumps(unc))
print("YEARLY",json.dumps(yr))