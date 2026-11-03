"""Read-only reproduction of the supplied baseline; no sizing optimization."""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

root = Path("/data")
spec = importlib.util.spec_from_file_location("original", root / "raw/run_all_gates.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
df = m.load_data(str(root / "raw/usa100_clean.csv"))
trades = m.run_backtest(df)
trades.to_csv(root / "analysis/baseline_trades_original.csv", index=False)
issues = {
    "next_bar_not_1031": [],
    "missing_1555": [],
    "missing_open_or_signal": [],
}
for day, g in df.groupby("d"):
    times = g["t"].to_numpy()
    sig = np.flatnonzero(times == "10:30")
    if not len(sig) or not (times == "09:30").any():
        issues["missing_open_or_signal"].append(str(day))
        continue
    i = sig[0] + 1
    if i >= len(times) or times[i] != "10:31":
        issues["next_bar_not_1031"].append(str(day))
    if not (times == "15:55").any():
        issues["missing_1555"].append(str(day))

oh = df[["open", "high", "low", "close"]]
bad_ohlc = (
    (oh["high"] < oh[["open", "close", "low"]].max(axis=1))
    | (oh["low"] > oh[["open", "close", "high"]].min(axis=1))
).sum()
independent_total = math.fsum(float(x) / m.STOP_POINTS for x in trades["net_pts"])
assert math.isclose(independent_total, float(trades["R"].sum()), abs_tol=1e-9)
out = {
    "scope": "Original baseline only; cost assumption 1 point, timestamps interpreted unchanged",
    "rows": len(df),
    "first_timestamp": str(df["timestamp"].min()),
    "last_timestamp": str(df["timestamp"].max()),
    "duplicate_timestamps": int(df["timestamp"].duplicated().sum()),
    "missing_values": int(oh.isna().sum().sum()),
    "bad_ohlc": int(bad_ohlc),
    "nonpositive_prices": int((oh <= 0).any(axis=1).sum()),
    "weekend_rows": int((df["timestamp"].dt.dayofweek >= 5).sum()),
    "outside_0930_1600_rows": int(((df["t"] < "09:30") | (df["t"] > "16:00")).sum()),
    "timing_issue_counts": {k: len(v) for k, v in issues.items()},
    "timing_issue_examples": {k: v[:5] for k, v in issues.items()},
    "baseline": m._edge_stats(trades),
    "exit_counts": trades["exit_type"].value_counts().to_dict(),
    "independent_total_R_check": independent_total,
    "original_gate2_pass": m.gate2(trades)[0],
    "original_gate3_rerun": False,
}
(root / "analysis/audit_evidence.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))