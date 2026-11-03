"""Execution sensitivity only. Originals untouched; not a live-fill simulation.

ASSUMPTIONS: supplied timestamps are NY minute-start labels; ideal stop/target
fills, original 1-point additive cost, stop-first ties, no ask series.
MAE bounds apply only to this ideal bid-price model, not actual account equity.
"""
import importlib.util
import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path("/data")
s = importlib.util.spec_from_file_location("baseline", ROOT / "raw/run_all_gates.py")
m = importlib.util.module_from_spec(s)
s.loader.exec_module(m)
df = m.load_data(str(ROOT / "raw/usa100_clean.csv"))


def simulate(g, mode):
    times = g["t"].to_numpy()
    prices = g[["open", "high", "low", "close"]].to_numpy(float)
    oi = np.flatnonzero(times == "09:30")[0]
    si = np.flatnonzero(times == "10:30")[0]
    ei = si + 1
    fi = np.flatnonzero(times == "15:55")[0]
    diff = prices[si, 0] - prices[oi, 0]
    if diff == 0:
        return None
    d = 1 if diff > 0 else -1
    entry = round(prices[ei, 0] / m.TICK_SIZE) * m.TICK_SIZE
    stop = entry - d * m.STOP_POINTS
    target = entry + d * m.STOP_POINTS * m.TARGET_R
    last = fi if mode == "original_close" else fi - 1
    prior_mae = 0.0
    gap_through_stop = False
    both_hit = False
    for k in range(ei, last + 1):
        op, hi, lo, cl = prices[k]
        adverse = max(0.0, entry - lo if d == 1 else hi - entry)
        stop_hit = lo <= stop if d == 1 else hi >= stop
        target_hit = hi >= target if d == 1 else lo <= target
        if stop_hit:
            px, kind = stop, "stop"
            lower = upper = m.STOP_POINTS
            gap_through_stop = (op < stop if d == 1 else op > stop)
            both_hit = bool(target_hit)
            break
        if target_hit:
            px, kind = target, "target"
            lower = max(prior_mae, max(0.0, d * (entry - op)))
            upper = max(prior_mae, adverse)
            break
        prior_mae = max(prior_mae, adverse)
    else:
        k = fi
        px = prices[fi, 3] if mode == "original_close" else prices[fi, 0]
        kind = "eod"
        lower = upper = max(prior_mae, max(0.0, d * (entry - px)))
    gross = d * (px - entry)
    # Nominal ideal-stop bounds; flag gaps separately rather than invent a fill.
    lower = min(lower, m.STOP_POINTS)
    upper = min(upper, m.STOP_POINTS)
    return dict(
        date=str(g["d"].iloc[0]), direction=d, entry=entry,
        exit_type=kind, exit_time=times[k], gross_pts=gross,
        net_pts=gross - m.COST_POINTS_ROUND_TRIP,
        R=(gross - m.COST_POINTS_ROUND_TRIP) / m.STOP_POINTS,
        mae_lower_R=lower / m.STOP_POINTS,
        mae_upper_R=upper / m.STOP_POINTS,
        exit_bar_index=int(k - ei),
        stop_gap_flag=bool(gap_through_stop), both_levels_in_exit_bar=both_hit,
    )


rows = {mode: [] for mode in ("original_close", "1555_open_proxy")}
for _, g in df.groupby("d", sort=True):
    for mode in rows:
        row = simulate(g, mode)
        if row:
            rows[mode].append(row)
tables = {mode: pd.DataFrame(r) for mode, r in rows.items()}
original = m.run_backtest(df)
reconstructed = tables["original_close"]
np.testing.assert_allclose(reconstructed["R"], original["R"], atol=1e-12)
assert reconstructed["exit_type"].tolist() == original["exit_type"].tolist()
assert reconstructed["direction"].tolist() == original["direction"].tolist()
for mode, tab in tables.items():
    tab.to_csv(ROOT / f"analysis/{mode}_audit_trades.csv", index=False)
    assert (tab["mae_lower_R"] <= tab["mae_upper_R"] + 1e-12).all()
    assert math.isclose(math.fsum(tab["net_pts"]) / 40, tab["R"].sum(), abs_tol=1e-9)
delta = tables["1555_open_proxy"]["R"] - reconstructed["R"]
out = {
    "assumptions": [
        "NY minute-start labels, not independently verified against raw ticks",
        "Original 1-point additive round-trip cost remains unmeasured",
        "Ideal fixed stop/target fills and original stop-first tie policy",
        "15:55 open is a bid-price proxy, not the actual EA's fill",
        "MAE bounds are ideal bid-model bounds; ask, fees, gaps not modeled",
    ],
    "baseline_reconstruction_matches_original": True,
    "trades": len(original),
    "original_total_R": float(reconstructed["R"].sum()),
    "1555_open_proxy_total_R": float(tables["1555_open_proxy"]["R"].sum()),
    "delta_total_R": float(delta.sum()),
    "changed_trade_outcomes": int((delta.abs() > 1e-10).sum()),
    "original_stop_gap_flags": int(reconstructed["stop_gap_flag"].sum()),
    "original_both_levels_in_exit_bar": int(reconstructed["both_levels_in_exit_bar"].sum()),
    "original_profitable_entry_bar_exits": int(
        ((reconstructed["R"] > 0) & (reconstructed["exit_bar_index"] == 0)).sum()
    ),
    "quick_strike_status": "Sub-minute duration cannot be verified using M1 OHLC",
    "firm_equity_pass_simulation_run": False,
}
(ROOT / "analysis/execution_audit_evidence.json").write_text(json.dumps(out, indent=2))
print(json.dumps(out, indent=2))