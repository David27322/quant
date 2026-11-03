"""Additional dependence checks, independent reconciliation and delivery outputs."""
from pathlib import Path
import json, math, subprocess
import numpy as np
import pandas as pd

O=Path("/data/analysis/fhm_audit")
e=json.loads((O/"evidence.json").read_text())
allres=pd.read_csv(O/"all_simulations.csv")
allres=allres[~allres.id.str.startswith("extra_")].copy()
cases=[]
for lot in [.03,.06,.08,.09]:
 for dd in [.08,.10]:
  for block in [5,60]:
   cases.append(dict(id=f"extra_l{round(lot*100):02}_d{round(dd*100)}_b{block}",pool="primary",cost=2,lot=lot,dd=dd,block=block,horizon=2520,n=20000,seed=555000+len(cases),upper=1))
with (O/"extra_cases.txt").open("w") as f:
 for c in cases:
  f.write(f"{c['id']} {O}/pool_primary.txt 2 {c['lot']} {c['dd']} {c['block']} 2520 20000 {c['seed']} 1\n")
subprocess.run([str(O/"fhm_mc"),str(O/"extra_cases.txt"),str(O/"extra_results.csv")],check=True)
extra=pd.DataFrame(cases).merge(pd.read_csv(O/"extra_results.csv"),on=["id","n"])
assert (extra["pass"]+extra.overall_breach+extra.daily_breach+extra.unfinished==extra.n).all()
allres=pd.concat([allres,extra],ignore_index=True)
allres.to_csv(O/"all_simulations.csv",index=False)
ind=json.loads((O/"independent_numpy_check.json").read_text())
cpp=allres[allres.id=="main_c2_d10_l08_b1"].iloc[0]
combined_se=math.sqrt(float(cpp.mc_se)**2+ind["p_pass"]*(1-ind["p_pass"])/ind["n"])
ind["cpp_p_pass"]=float(cpp.p_pass)
ind["difference_standard_errors"]=abs(ind["p_pass"]-float(cpp.p_pass))/combined_se
assert ind["difference_standard_errors"]<4
e["independent_simulation_check"]=ind
e["additional_dependence_cases"]=extra.to_dict("records")
e["simulation_validation"]["cases"]=len(allres)
e["simulation_validation"]["paths"]=int(allres.n.sum())

paths=pd.read_csv(O/"audited_trade_paths.csv")
g=paths.gross_pts_gap_proxy.to_numpy()
r=(g-2)/40
positive=math.fsum(float(x) for x in r if x>0)
net=math.fsum(r)
e["hypothetical_news_haircut_sensitivity"]={
 "scenario":"If 60% is deducted from a subset of recorded NET winning P&L and losses are unchanged; no claim about actual FundedNext adjusted ledger or event exposure.",
 "cost_points":2,"net_R":net,"positive_net_R":positive,
 "break_even_share_of_positive_net_PnL_affected":net/(.6*positive),
 "historical_calendar_matched":False}
recent=paths[paths.date.str.startswith("2026")]
e["recent_sample"]={
 "n":len(recent),"through":"2026-06-25",
 "1pt_total_R":math.fsum((recent.gross_pts_gap_proxy.to_numpy()-1)/40),
 "2pt_total_R":math.fsum((recent.gross_pts_gap_proxy.to_numpy()-2)/40),
 "claim":"Negative available partial2026 sample; neither independent untouched OOS nor conclusive proof of decay."}

ea_path=Path("/data/raw/first_hour_momentum.mq5")
ea=ea_path.read_text()
audit=[
 {"severity":"paid-use blocker","finding":"PositionModify/PositionClose boolean results are treated as execution confirmation without checking successful server retcodes.","evidence":"SetExactBracket and ForceFlatAt1555; MQL5 documentation explicitly distinguishes basic request validation from server execution.","status":"Static code finding; not a reproduced broker failure."},
 {"severity":"paid-use blocker","finding":"After reported entry success but missing fill/position, code clears pending and returns without setting traded_today; a timer tick can retry during10:31 without a fresh live-position/order reconciliation.","evidence":"EnterAt1031 actual<=0 || !FindOurPosition path; ProcessClock can invoke again.","status":"Potential duplicate-entry race; not demonstrated live."},
 {"severity":"sizing blocker","finding":"No account-equity/daily/remaining-floor guard or target/floor sizing caps are implemented.","evidence":"InpLots is fixed and normalized; no equity-limit checks before Buy/Sell.","status":"Confirmed absent; prior plan's floor_cap policy is NOT in this EA."},
 {"severity":"state/logging","finding":"Persistent state keys contain symbol+magic but not account login/server; stale expected_exit is not cleared for a new position.","evidence":"KeyPrefix,LoadState,OnTradeTransaction.","status":"Potential stale state/misleading audit logs after account switches/restarts."},
 {"severity":"measurement","finding":"CSV lacks executed volume, commission/swap/fees, millisecond execution timing, and entry/exit bid+ask snapshots.","evidence":"WriteLog header and arguments.","status":"Trade-history export remains necessary; log alone cannot establish all-in execution costs."},
 {"severity":"timing","finding":"Entry attempts can occur throughout the10:31 minute, including recovery/retry; exact-open backtest is not equivalent to arbitrary within-minute fills.","evidence":"ProcessClock and EnterAt1031.","status":"Already intentional recovery comment; latency must be measured."},
 {"severity":"calendar","finding":"EA does not enforce verified Nasdaq cash sessions/early closes.","evidence":"Clock-time based ProcessClock only.","status":"Any session filter or early-close policy is a proposed strategy/execution change requiring consent."},
 {"severity":"limits","finding":"Static review/Python DST translation cannot establish compiled MT5 behavior, broker acceptance, restart recovery or network outage safety.","status":"Needs MetaEditor compile plus demo tests."}
]
e["EA_static_audit"]=audit
(O/"EA_static_audit.md").write_text("# EA static audit — original unchanged\n\n"+"\n\n".join(f"## {a['severity']}\n{a['finding']}\n\n{a.get('evidence','')}\n\n{a['status']}" for a in audit))
e["limitations_not_run"]=[
 "No MT5/MetaEditor compilation or live/broker-runtime tests in this Linux sandbox.",
 "No measured FundedNext transaction costs or news-calendar-matched funded PnL.",
 "No Quick Strike compliance model because exact subminute fills are unavailable.",
 "No purchased-account go-ahead or sizing/reinvestment optimum.",
 "No newer market data retrieved; original data and EA unmodified."
]

# Primary chart exposes resampling sensitivity rather than choosing the favorable method.
lots=[.02,.03,.04,.05,.06,.08,.09,.12]
spec={"version":1,"form":"multiline",
 "title":"Modeled odds change with lot size and resampling method",
 "aside":"Fixed lot on horizontal axis · 2pt assumed cost · 8%/10% static loss allowance · target/loss model only, not full compliance",
 "labels":[f"{v:.2f}" for v in lots],"axis":{"zero":True},"series":[],
 "colorMap":{"8% allowance · IID":"blue","8% allowance · 20-trade blocks":"teal","10% allowance · IID":"orange","10% allowance · 20-trade blocks":"purple"}}
for dd,block,label in [(.08,1,"8% allowance · IID"),(.08,20,"8% allowance · 20-trade blocks"),(.10,1,"10% allowance · IID"),(.10,20,"10% allowance · 20-trade blocks")]:
 q=allres[(allres.id.str.startswith("main_"))&(allres.cost==2)&(allres.dd==dd)&(allres.block==block)].sort_values("lot")
 spec["series"].append({"label":label,"valueKind":"percent","role":("subject" if not spec["series"] else "aux"),"data":(q.p_pass*100).tolist()})
(O/"probability_chart.json").write_text(json.dumps(spec,indent=2))
yr=e["yearly_2point_proxy"]
labels=[str(v["year"])+(" YTD" if v["partial_year"] else "") for v in yr]
year_spec={"version":1,"form":"categorical-bars","orientation":"vertical","mode":"grouped",
 "title":"The available 2026 sample is negative",
 "aside":"Mean net R per trade · assumed2pt cost · exit/gap proxies · 2026:124 trades throughJune25; not confirmed decay",
 "labels":labels,"axis":{"zero":True},
 "series":[{"label":"Mean net R/trade","valueKind":"number","role":"subject","data":[v["mean_R"] for v in yr]}],
 "colorMap":{label:("green" if row["mean_R"]>=0 else "red") for label,row in zip(labels,yr)}}
(O/"year_chart.json").write_text(json.dumps(year_spec,indent=2))
e["visual_plan"]=[
 {"comparison":"Available-year meanR","grain":"year","population":"primary proxy cost2,2026partial","unit":"R/trade","disposition":"chart","reason":"Recent negative sample changes the purchase decision; per-trade units avoid unequal-period total comparisons."},
 {"comparison":"Sizing,drawdown and resampling sensitivity","grain":"scenario","population":"fullhistoricalpool,cost2,2520horizon","unit":"modeledprobability","disposition":"chart","reason":"Do not hide the large IID/block-method difference."},
 {"comparison":"Completion time,coststress,calendar/MAE and bootstrap uncertainty","grain":"scenario","population":"explicitcasepopulations","unit":"opportunities/percent","disposition":"table","reason":"Exact values support the two charts without another dashboard."}
]
# Selected table contains IID and20-block estimates and successful-path medians.
selected=[]
for lot in [.03,.05,.06,.08,.09]:
 for dd in [.08,.10]:
  q=allres[(allres.id.str.startswith("main_"))&(allres.cost==2)&(allres.lot==lot)&(allres.dd==dd)]
  selected.append({"lot":lot,"nominal_initial_risk_percent":lot*8,"dd":dd,
   "iid_p":float(q.loc[q.block==1,"p_pass"].iloc[0]),
   "block20_p":float(q.loc[q.block==20,"p_pass"].iloc[0]),
   "iid_success_median":float(q.loc[q.block==1,"median_days"].iloc[0]),
   "block20_success_median":float(q.loc[q.block==20,"median_days"].iloc[0])})
e["delivery_table"]=selected
pd.DataFrame(selected).to_csv(O/"selected_scenarios.csv",index=False)
(O/"evidence.json").write_text(json.dumps(e,indent=2,default=str))
print("CROSSCHECK",json.dumps(ind))
print("ADDITIONAL",extra[["lot","dd","block","p_pass"]].to_string(index=False))
print("RECENT",e["recent_sample"])
print("NEWS_STRESS",e["hypothetical_news_haircut_sensitivity"])
print("SELECTED",pd.DataFrame(selected).to_string(index=False))