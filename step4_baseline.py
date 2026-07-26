"""
step4_baseline.py — Step 4: Baseline backtest, all three ORB variants
======================================================================
Runs V1, V3, V4 on the full cleaned dataset.
Prints a summary metrics table.
Flags any variant with < 100 trades (per guardrail).

Usage:
    python step4_baseline.py

Output:
    Console table + saves results to step4_results.csv
"""

import os, sys
import backtrader as bt

from orb_common   import NQData, make_cerebro, print_results
from orb_v1_classic import ORB_V1_Classic
from orb_v3_vwap    import ORB_V3_VWAP
from orb_v4_atr     import ORB_V4_ATR, run_v4

DATA_DIR   = os.path.join(os.path.dirname(__file__), "data_clean")
CSV_1MIN   = os.path.join(DATA_DIR, "NQ_1min_rth.csv")
CASH       = 100_000.0
RISK_PCT   = 0.01


def extract_metrics(strat, label, start_val, end_val):
    sh = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    tr = strat.analyzers.trades.get_analysis()

    total   = tr.get("total",  {}).get("total",  0)
    won     = tr.get("won",    {}).get("total",  0)
    pnl_net = tr.get("pnl",   {}).get("net",    {}).get("total", 0.0)
    avg_win = tr.get("won",   {}).get("pnl",    {}).get("average", 0.0)
    avg_los = tr.get("lost",  {}).get("pnl",    {}).get("average", 0.0)

    win_rate  = (won / total * 100) if total > 0 else 0.0
    sharpe    = sh.get("sharperatio", None)
    max_dd_pct= dd.get("max", {}).get("drawdown",  0.0)
    max_dd_usd= dd.get("max", {}).get("moneydown", 0.0)
    ret_pct   = (end_val / start_val - 1) * 100

    return {
        "variant":    label,
        "trades":     total,
        "win_rate":   round(win_rate,  1),
        "net_pnl":    round(pnl_net,   0),
        "return_pct": round(ret_pct,   2),
        "sharpe":     round(sharpe, 3) if sharpe else None,
        "max_dd_pct": round(max_dd_pct, 2),
        "max_dd_usd": round(max_dd_usd, 0),
        "avg_win":    round(avg_win, 2),
        "avg_loss":   round(avg_los, 2),
    }


def run_variant(label, cerebro_factory_fn):
    print(f"\n{'='*55}")
    print(f"Running {label} ...")
    start_val = cerebro_factory_fn.broker.getvalue()
    results   = cerebro_factory_fn.run()
    end_val   = cerebro_factory_fn.broker.getvalue()
    return results[0], start_val, end_val


def main():
    if not os.path.exists(CSV_1MIN):
        sys.exit(f"ERROR: {CSV_1MIN} not found. Run step0_data_prep.py first.")

    all_metrics = []

    # --- V1 ---
    c1 = make_cerebro(CSV_1MIN, cash=CASH, risk_pct=RISK_PCT)
    c1.addstrategy(ORB_V1_Classic, verbose=False)
    s1, sv1, ev1 = run_variant("V1 Classic 30min ORB", c1)
    m1 = extract_metrics(s1, "V1 Classic", sv1, ev1)
    all_metrics.append(m1)
    print_results(s1, "V1 Classic")

    # --- V3 ---
    c3 = make_cerebro(CSV_1MIN, cash=CASH, risk_pct=RISK_PCT)
    c3.addstrategy(ORB_V3_VWAP, verbose=False)
    s3, sv3, ev3 = run_variant("V3 VWAP-filtered 15min ORB", c3)
    m3 = extract_metrics(s3, "V3 VWAP", sv3, ev3)
    all_metrics.append(m3)
    print_results(s3, "V3 VWAP")

    # --- V4 ---
    c4 = run_v4(CSV_1MIN, cash=CASH, risk_pct=RISK_PCT, verbose=False)
    s4, sv4, ev4 = run_variant("V4 ATR-gated 30min ORB", c4)
    m4 = extract_metrics(s4, "V4 ATR", sv4, ev4)
    all_metrics.append(m4)
    print_results(s4, "V4 ATR")

    # --- Summary table ---
    print(f"\n{'='*55}")
    print("STEP 4 — BASELINE SUMMARY")
    print(f"{'='*55}")
    hdr = (f"{'Variant':<18} {'Trades':>7} {'WinR%':>6} "
           f"{'NetP&L':>9} {'Ret%':>7} {'Sharpe':>7} "
           f"{'MaxDD%':>7} {'MaxDD$':>9}")
    print(hdr)
    print("-"*55)

    for m in all_metrics:
        flag = " *** <100 TRADES — DISCARD" if m["trades"] < 100 else ""
        sh   = f"{m['sharpe']:.3f}" if m["sharpe"] else "  n/a"
        print(f"{m['variant']:<18} {m['trades']:>7} {m['win_rate']:>6.1f} "
              f"{m['net_pnl']:>9,.0f} {m['return_pct']:>7.2f} {sh:>7} "
              f"{m['max_dd_pct']:>7.2f} {m['max_dd_usd']:>9,.0f}"
              f"{flag}")

    print(f"\n{'='*55}")
    print("GUARDRAIL CHECK (< 100 trades = discard)")
    for m in all_metrics:
        status = "PASS" if m["trades"] >= 100 else "DISCARD"
        print(f"  {m['variant']:<18}  {m['trades']} trades  → {status}")

    # --- Save to CSV ---
    import csv as csv_mod
    out_path = os.path.join(os.path.dirname(__file__), "step4_results.csv")
    fields = list(all_metrics[0].keys())
    with open(out_path, "w", newline="") as f:
        w = csv_mod.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(all_metrics)
    print(f"\nResults saved → {out_path}")
    print("Next: paste summary above into chat → Step 5 (combination grid).")


if __name__ == "__main__":
    main()
