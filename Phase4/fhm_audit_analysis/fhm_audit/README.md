# FHM offline audit — conditional results, not a purchase recommendation

Completed: baseline reproduction, 2023 source reconstruction, exit/gap/MAE audit, static EA safety review, synthetic unit checks, challenge target/loss simulation and dependence/bootstrap sensitivities.

Data: 1,412 historical trades ending 2026-06-25. Other-year source files not independently reconstructed. 453 cases and 3,080,300 simulated paths do NOT increase the historical sample size.

Key warning: available2026 sample has124 trades and -14.7495R at ASSUMED2pt costs using exit/gap proxies. Full history stays positive. This is not confirmed signal decay or a new independent out-of-sample study.

Simulation assumptions and limitations: see evidence.json. Costs1/2/3pt are hypothetical. Fixed lots, initial$5000, static8/10% total loss, daily4%, targets8%+4%, minimum2days each phase; 2520 opportunities across both phases. Completion times are conditional on successful paths. Unfinished paths are separate from breached paths. No full Quick Strike/discretionary compliance, historical news-adjusted funded PnL, measured fills, or latest data. No funded payout/reinvestment forecast. EA unchanged and NOT compiled or broker-tested.

The 5th-95th bootstrap percentiles are sensitivity summaries, NOT calibrated live-probability confidence bounds. IID/block models assume aspects of the historical return process persist. Cost changes and regime drift can dominate Monte Carlo sampling error.

Reproduce on a Linux workspace rooted at/data:
1. Supply your original CSVs at/data/raw/usa100_clean.csv and/data/raw/ndx_2023.csv. Their SHA256 hashes are in evidence.json. The ZIP intentionally does not duplicate these large user-owned files.
2. Install NumPy,pandas and exchange-calendars==4.13.2; g++ is required. Version details in evidence.json.
3. python3 /data/analysis/run_fhm_audit.py
4. python3 /data/analysis/check_fhm_independent.py
5. python3 /data/analysis/finalize_fhm_audit.py

Original raw strategy code/EA are included, unmodified. New scripts and C++ engine are separate. Saved output pools,seeds,cases,results,trades and independent check are included. The Linux binary and chart-review screenshots are excluded from the ZIP. HTML charts are included separately as well as in this package.

Read EA_static_audit.md before running automation. Fixes require a separate implementation/compile/demo-validation step; static audit does not demonstrate a broker failure.
