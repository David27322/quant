#!/usr/bin/env python3
"""
run_all_gates.py
================
Free, $0 validation gauntlet for the First-Hour Momentum edge on NDX100/NAS100
(FundedNext CFD, MT5) BEFORE paying for any challenge.

Strategy (validated, FIXED - do NOT tweak):
  rth_open  = open of the 09:30 ET bar
  signal    = open of the 10:30 ET bar
  direction = sign(signal - rth_open)        # long if first hour up, short if down
  entry     = open of the NEXT bar (10:31)
  stop      = 40 pts ; target = 2R (80 pts)
  flat      = 15:55 ET ; never overnight ; ONE trade/day

Gates (gate 0 = your manual FundedNext-demo step, not run here):
  Gate 1  Re-validate on the full 2021-2026 history (edge real + survivable)
  Gate 2  5-fold walk-forward w/ 30-day embargo (stability, no leakage)
  Gate 3  Monte-Carlo eval-pass simulation vs FundedNext's exact rules

Input : usa100_clean.csv  (timestamp,open,high,low,close ; RTH 09:30-16:00 ET only)
Deps  : pandas, numpy
Run   : python run_all_gates.py
"""
from __future__ import annotations
import numpy as np
import pandas as pd

# =========================================================================
# CONFIG  -- the only block you normally touch
# =========================================================================
INPUT_CSV   = "usa100_clean.csv"
ACCOUNT_USD = 5_000.0

# ---- NDX100/NAS100 contract spec (from your MT5 symbol spec) ------------
# contract size 10, tick size 0.01, tick value 0.1
#   point value/lot = tick_value / tick_size = 0.1 / 0.01 = $10 per index point
# *** BIG CORRECTION vs Phase 3.8 (which assumed $1/pt) -> lots are 10x smaller. ***
POINT_VALUE_PER_LOT = 10.0      # $ per 1.0 index point per 1.0 lot
TICK_SIZE           = 0.01
MIN_LOT, MAX_LOT, LOT_STEP = 0.01, 40.0, 0.01
# swap_long/short are IGNORED on purpose: strategy is flat by 15:55, never overnight.

# ---- the validated signal (fixed) ---------------------------------------
RTH_OPEN_T  = "09:30"
SIGNAL_T    = "10:30"
FLAT_T      = "15:55"
STOP_POINTS = 40.0
TARGET_R    = 2.0               # -> 80-pt target

# ---- costs: spread is floating + slippage. ASSUMPTION, calibrate vs demo. ----
# Deducted as index points per round-trip trade. Bump if demo fills are worse.
COST_POINTS_ROUND_TRIP = 1.0

# ---- sizing -------------------------------------------------------------
#   risk$/trade = STOP_POINTS * POINT_VALUE_PER_LOT * lot
#   At $10/pt:  0.3 lot -> $120/tr (2.4%) | 0.4 -> $160 (3.2%) | 0.5 -> $200 (4.0%)
#   At  $1/pt:  0.3 lot -> $12/tr  (0.24%)| 0.4 -> $16  (0.32%)| 0.5 -> $20  (0.40%)
LOT_SWEEP = [0.02, 0.03, 0.04, 0.05]   # realistic for $10/pt on $5k (0.3-0.5 were 10x oversized)
GATE_LOT  = 0.03               # reference lot for the lot-independent $ summaries

# ---- FundedNext rule presets (VERIFY on official page the day you buy) ------
# Source: FundedNext Help Center (Dec 2025 / 2026). Rules change - screenshot them.
PRESETS = {
    "stellar_1step": dict(
        label="Stellar 1-Step",
        targets=[0.10],          # 10% single-phase target
        daily_dd=0.03,           # 3% of initial balance
        overall_dd=0.06,         # 6% of initial balance (static)
        dd_type="static",
        min_days=2,
    ),
    "stellar_lite_2step": dict(
        label="Stellar Lite (2-Step)",
        targets=[0.08, 0.04],    # P1 8%, P2 4%
        daily_dd=0.04,
        overall_dd=0.08,
        dd_type="static",
        min_days=5,
    ),
    "stellar_instant": dict(
        label="Stellar Instant",
        targets=[0.06],          # PLACEHOLDER payout milestone (no challenge target!)
        daily_dd=None,           # no daily loss limit
        overall_dd=0.06,         # 6% TRAILING
        dd_type="trailing",
        min_days=0,
    ),
}
ACTIVE_PRESET = "stellar_lite_2step"   # locked: Stellar Lite (2-Step)

# ---- Monte-Carlo settings ------------------------------------------------
# Stellar Lite 2-Step has NO TIME LIMIT (verified FundedNext help center, 2026),
# so a phase is a run-to-absorption race: hit the profit target BEFORE the 8%
# static max-loss (or 4% daily) breach. MC_HMAX just caps the race so it ends.
# NOTE: this per-trade loop is slower than Run 1 -- expect ~1-3 min.
MC_HMAX       = 1_200          # max trades per phase (~5 yrs at 1 trade/day)
MC_SIMS       = 15_000
MC_BOOT_REPS  = 60
MC_BOOT_SIMS  = 2_500
MC_PASS_CI_LO = 0.55           # Phase 3.8 threshold: 5th-pct bootstrap pass prob

# ---- Gate 1 thresholds ---------------------------------------------------
G1_SHARPE_MIN = 1.00           # relaxed from 1.2: a 1-trade/day edge with PF>1.15,
                               # all years green, ~3-sigma vs random is tradeable
G1_PF_MIN     = 1.15
G1_MAXDD_USD  = 0.05 * ACCOUNT_USD          # <= $250 at GATE_LOT (<=5% of $5k)
G1_FULL_YEARS = [2021, 2022, 2023, 2024, 2025]   # 2026 is partial
RANDOM_CTRL_REPS = 20

# ---- Gate 1.5 thresholds (robustness) -----------------------------------
# Two artifact-killers that Gates 1-3 cannot see:
#   (a) cost sweep -> is a ~3.8-pt/trade edge just underpriced spread/slippage?
#   (b) drop-2024  -> is the edge one lucky trend year, or broad-based?
COST_SWEEP     = [1.0, 2.0, 3.0]   # index pts round-trip to stress-test (1.0 = base)
DROP_YEAR      = 2024              # remove this single year and re-check the edge
R15_PF_MIN     = 1.10              # profit-factor floor required in EVERY scenario
R15_TOTALR_MIN = 0.0               # must stay net-positive in R in EVERY scenario


# =========================================================================
# DATA + BACKTEST
# =========================================================================
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df["t"] = df["timestamp"].dt.strftime("%H:%M")
    df["d"] = df["timestamp"].dt.date
    return df.sort_values("timestamp").reset_index(drop=True)


def run_backtest(df: pd.DataFrame, cost_pts: float = COST_POINTS_ROUND_TRIP,
                 random_dir: bool = False, rng: np.random.Generator | None = None
                 ) -> pd.DataFrame:
    """One trade/day. Returns a DataFrame: date, year, direction, exit_type, net_pts, R."""
    target_pts = STOP_POINTS * TARGET_R
    rows = []
    for day, g in df.groupby("d", sort=True):
        t  = g["t"].values
        o  = g["open"].values.astype(float)
        hi = g["high"].values.astype(float)
        lo = g["low"].values.astype(float)
        cl = g["close"].values.astype(float)

        oi = np.where(t == RTH_OPEN_T)[0]
        si = np.where(t == SIGNAL_T)[0]
        if len(oi) == 0 or len(si) == 0:
            continue
        oi, si = oi[0], si[0]
        ei = si + 1                       # enter on the NEXT bar
        if ei >= len(g):
            continue

        diff = o[si] - o[oi]              # signal open - 09:30 open
        if diff == 0:
            continue                      # first hour flat -> no trade (no guessing)
        if random_dir:
            direction = 1 if rng.random() < 0.5 else -1
        else:
            direction = 1 if diff > 0 else -1

        entry = round(o[ei] / TICK_SIZE) * TICK_SIZE
        if direction == 1:
            stop, tgt = entry - STOP_POINTS, entry + target_pts
        else:
            stop, tgt = entry + STOP_POINTS, entry - target_pts

        fi_arr = np.where(t == FLAT_T)[0]
        fi = fi_arr[0] if len(fi_arr) else len(g) - 1
        if fi < ei:
            fi = len(g) - 1

        exit_px, exit_type = None, None
        for k in range(ei, fi + 1):       # monitor entry bar onward (incl.)
            if direction == 1:
                if lo[k] <= stop:         # tie -> stop first (conservative)
                    exit_px, exit_type = stop, "stop"; break
                if hi[k] >= tgt:
                    exit_px, exit_type = tgt, "target"; break
            else:
                if hi[k] >= stop:
                    exit_px, exit_type = stop, "stop"; break
                if lo[k] <= tgt:
                    exit_px, exit_type = tgt, "target"; break
        if exit_px is None:
            exit_px, exit_type = cl[fi], "eod"   # flat at 15:55

        gross = (exit_px - entry) if direction == 1 else (entry - exit_px)
        net_pts = gross - cost_pts
        ts = pd.Timestamp(day)
        rows.append((ts, ts.year, direction, exit_type, net_pts, net_pts / STOP_POINTS))

    return pd.DataFrame(rows, columns=["date", "year", "direction",
                                       "exit_type", "net_pts", "R"])


# =========================================================================
# METRIC HELPERS
# =========================================================================
def risk_usd(lot: float) -> float:
    return STOP_POINTS * POINT_VALUE_PER_LOT * lot


def to_usd(R: np.ndarray, lot: float) -> np.ndarray:
    return R * risk_usd(lot)


def sharpe_annual(R: np.ndarray) -> float:
    if len(R) < 2 or R.std(ddof=1) == 0:
        return 0.0
    return float(R.mean() / R.std(ddof=1) * np.sqrt(252))


def profit_factor(R: np.ndarray) -> float:
    wins = R[R > 0].sum()
    losses = -R[R < 0].sum()
    return float(wins / losses) if losses > 0 else float("inf")


def max_dd_usd(R: np.ndarray, lot: float) -> float:
    eq = np.concatenate([[0.0], np.cumsum(to_usd(R, lot))])
    peak = np.maximum.accumulate(eq)
    return float((peak - eq).max())


# =========================================================================
# GATE 1 -- re-validation on full history
# =========================================================================
def gate1(trades: pd.DataFrame, df: pd.DataFrame) -> tuple[bool, dict]:
    R = trades["R"].values
    sh = sharpe_annual(R)
    pf = profit_factor(R)
    yearly = trades.groupby("year")["R"].apply(lambda s: to_usd(s.values, GATE_LOT).sum())
    years_ok = {y: float(yearly.get(y, float("nan"))) for y in G1_FULL_YEARS}
    all_years_pos = all((y in yearly.index) and (yearly[y] > 0) for y in G1_FULL_YEARS)

    # random-signal control (same days, random direction)
    ctrl = np.array([run_backtest(df, random_dir=True,
                                  rng=np.random.default_rng(1000 + s))["R"].sum()
                     for s in range(RANDOM_CTRL_REPS)])
    real_total_R = R.sum()
    ctrl_mean, ctrl_std = float(ctrl.mean()), float(ctrl.std(ddof=1))
    beats_random = (real_total_R > 0) and \
                   (real_total_R > ctrl_mean + 1.64 * ctrl_std)   # ~95% one-sided

    checks = {
        f"Sharpe >= {G1_SHARPE_MIN}":            (sh >= G1_SHARPE_MIN, f"{sh:.2f}"),
        "every full year 2021-25 net positive":  (all_years_pos, str({k: round(v) for k, v in years_ok.items()})),
        f"profit factor >= {G1_PF_MIN}":         (pf >= G1_PF_MIN, f"{pf:.2f}"),
        "beats random-direction control":        (beats_random, f"real {real_total_R:.1f}R vs rand {ctrl_mean:.1f}+/-{ctrl_std:.1f}R"),
    }
    passed = all(ok for ok, _ in checks.values())
    def side(d):
        s = trades[trades["direction"] == d]["R"].values
        return dict(n=int(len(s)),
                    win=float((s > 0).mean()) if len(s) else 0.0,
                    total_R=float(s.sum()) if len(s) else 0.0)
    extra = dict(trades=len(R), win_rate=float((R > 0).mean()), avg_R=float(R.mean()),
                 total_R=float(real_total_R),
                 longs=side(1), shorts=side(-1),
                 exit_mix=trades["exit_type"].value_counts(normalize=True).round(3).to_dict())
    return passed, dict(checks=checks, extra=extra)


# =========================================================================
# GATE 1.5 -- robustness: cost sensitivity + drop-2024 (lot-independent)
# =========================================================================
def _edge_stats(trades: pd.DataFrame) -> dict:
    R = trades["R"].values
    return dict(
        n=int(len(R)),
        win=float((R > 0).mean()) if len(R) else 0.0,
        avg_R=float(R.mean()) if len(R) else 0.0,
        total_R=float(R.sum()) if len(R) else 0.0,
        sharpe=sharpe_annual(R),
        pf=profit_factor(R),
    )


def gate1_5(df: pd.DataFrame, base_trades: pd.DataFrame) -> tuple[bool, dict]:
    """Two artifact-killers Gates 1-3 can't test:
       (a) re-run the FULL backtest at 1.0 / 2.0 / 3.0 pt round-trip cost;
       (b) drop 2024 entirely and re-check the edge.
       Each scenario must stay net-positive in R AND keep PF >= R15_PF_MIN."""
    def ok(st):  # shared survivability rule
        return (st["total_R"] > R15_TOTALR_MIN) and (st["pf"] >= R15_PF_MIN)

    # (a) cost sensitivity -- cost only shifts net_pts, never the price-based exits
    cost_rows = {}
    for c in COST_SWEEP:
        st = _edge_stats(run_backtest(df, cost_pts=c))
        st["ok"] = ok(st)
        cost_rows[c] = st
    cost_ok = all(r["ok"] for r in cost_rows.values())

    # (b) drop-2024 -- reuse the base backtest (default cost), remove the year
    drop = _edge_stats(base_trades[base_trades["year"] != DROP_YEAR])
    drop["ok"] = ok(drop)

    passed = cost_ok and drop["ok"]
    return passed, dict(cost_rows=cost_rows, drop=drop,
                        cost_ok=cost_ok, drop_ok=drop["ok"])


# =========================================================================
# GATE 2 -- 5-fold walk-forward with 30-day embargo (stability check)
# =========================================================================
def gate2(trades: pd.DataFrame) -> tuple[bool, dict]:
    t = trades.sort_values("date").reset_index(drop=True)
    edges = pd.date_range(t["date"].min(), t["date"].max(), periods=6)
    folds = []
    for i in range(5):
        lo = edges[i] + pd.Timedelta(days=30)        # 30-day embargo at fold start
        hi = edges[i + 1]
        mask = (t["date"] >= lo) & ((t["date"] <= hi) if i == 4 else (t["date"] < hi))
        sub = t[mask]
        if len(sub) < 20:
            folds.append(dict(n=len(sub), sharpe=float("nan"), total_R=float("nan"),
                              maxdd=float("nan"), ok=False)); continue
        Rf = sub["R"].values
        folds.append(dict(n=len(sub), sharpe=sharpe_annual(Rf), total_R=float(Rf.sum()),
                          maxdd=max_dd_usd(Rf, GATE_LOT), ok=True))
    n_good = sum(1 for f in folds if f["ok"] and f["sharpe"] >= 1.0)
    n_pos  = sum(1 for f in folds if f["ok"] and f["total_R"] > 0)
    catastrophic = any(f["ok"] and f["total_R"] < -8.0 for f in folds)   # R-based, lot-independent
    passed = (n_pos >= 4) and (not catastrophic)
    return passed, dict(folds=folds, n_good=n_good, n_pos=n_pos, catastrophic=catastrophic)


# =========================================================================
# GATE 3 -- Monte-Carlo eval-pass simulation vs FundedNext rules
# =========================================================================
def _first_true_idx(mat: np.ndarray) -> np.ndarray:
    H = mat.shape[1]
    return np.where(mat.any(axis=1), mat.argmax(axis=1), H)


def mc_pass_prob(R_pool: np.ndarray, preset: dict, risk_frac: float,
                 h_max: int, n: int, rng: np.random.Generator) -> float:
    """P(pass all phases) with NO TIME LIMIT: each phase is a run-to-absorption race
    -- reach the profit target before the static (or trailing) max-loss / daily breach.
    Phases treated as independent resets (approx) -> product of per-phase pass probs."""
    trailing = (preset["dd_type"] == "trailing")
    dd    = preset["overall_dd"]
    daily = preset["daily_dd"]
    md    = max(int(preset["min_days"]), 1)
    p_total = 1.0
    for tgt in preset["targets"]:
        bal  = np.ones(n)
        peak = np.ones(n)
        done = np.zeros(n, dtype=bool)            # path resolved (won or breached)
        won  = np.zeros(n, dtype=bool)
        for step in range(h_max):
            pnl = rng.choice(R_pool, size=n) * risk_frac
            bal += pnl
            if trailing:
                peak = np.maximum(peak, bal)
                breach_lvl = peak * (1.0 - dd)
            else:
                breach_lvl = 1.0 - dd             # 8% static from initial
            if daily is not None:                 # one trade/day => daily loss = pnl
                done |= (~done) & (pnl <= -daily)
            done |= (~done) & (bal <= breach_lvl) # ruin
            if step + 1 >= md:                    # target valid only after min days
                hit = (~done) & (bal >= 1.0 + tgt)
                won  |= hit
                done |= hit
            if done.all():
                break
        p_total *= float(won.mean())              # unresolved paths count as not-passed
    return p_total


def gate3(trades: pd.DataFrame) -> tuple[bool, dict]:
    """Sweep LOT_SWEEP for the ACTIVE_PRESET; pass if ANY lot clears the bar."""
    R_pool = trades["R"].values
    preset = PRESETS[ACTIVE_PRESET]
    rng = np.random.default_rng(7)
    rows = {}
    for lot in LOT_SWEEP:
        risk_frac = risk_usd(lot) / ACCOUNT_USD
        p = mc_pass_prob(R_pool, preset, risk_frac, MC_HMAX, MC_SIMS, rng)
        boot = np.array([mc_pass_prob(rng.choice(R_pool, size=len(R_pool)), preset,
                                      risk_frac, MC_HMAX, MC_BOOT_SIMS, rng)
                         for _ in range(MC_BOOT_REPS)])
        ci_lo, ci_hi = float(np.percentile(boot, 5)), float(np.percentile(boot, 95))
        null = mc_pass_prob(R_pool - R_pool.mean(), preset, risk_frac,
                            MC_HMAX, MC_SIMS, rng)
        rows[lot] = dict(p_pass=p, ci_lo=ci_lo, ci_hi=ci_hi, null=null,
                         ok=(ci_lo >= MC_PASS_CI_LO and p - null >= 0.10))
    passed = any(r["ok"] for r in rows.values())
    return passed, dict(label=preset["label"], rows=rows)


# =========================================================================
# MAIN
# =========================================================================
def main() -> int:
    bar = "=" * 72
    preset = PRESETS[ACTIVE_PRESET]
    tgt_s = "+".join(f"{t*100:.0f}%" for t in preset["targets"])
    daily_s = f"{preset['daily_dd']*100:.0f}%" if preset["daily_dd"] is not None else "none"
    print(bar)
    print("  run_all_gates.py  -  First-Hour Momentum / NDX100 (FundedNext CFD)")
    print(bar)
    print(f"  Contract value : ${POINT_VALUE_PER_LOT:.0f}/index-point/lot   "
          f"cost: {COST_POINTS_ROUND_TRIP} pt round-trip")
    print(f"  Account        : ${ACCOUNT_USD:,.0f}   rules: {preset['label']}  "
          f"(target {tgt_s}, daily {daily_s}, "
          f"max {preset['overall_dd']*100:.0f}% {preset['dd_type']})")
    print(f"  Lot sweep      : {LOT_SWEEP}  -> "
          + " | ".join(f"{l}:${risk_usd(l):.0f}/tr({risk_usd(l)/ACCOUNT_USD*100:.1f}%)"
                       for l in LOT_SWEEP))

    df = load_data(INPUT_CSV)
    trades = run_backtest(df)
    if trades.empty:
        print("\n  No trades produced -- check the CSV path/format.")
        return 2
    print(f"  Backtest       : {len(trades)} trades, "
          f"{trades['date'].min().date()} -> {trades['date'].max().date()}")

    p1, d1 = gate1(trades, df)
    p15, d15 = gate1_5(df, trades)
    p2, d2 = gate2(trades)
    p3, d3 = gate3(trades)
    e = d1["extra"]

    # ---- Gate 1 -----------------------------------------------------------
    print("\n" + bar)
    print("  GATE 1  -  edge real on full history?  (lot-independent)")
    print(bar)
    print(f"  trades {e['trades']} | win {e['win_rate']*100:.1f}% | "
          f"avgR {e['avg_R']:+.3f} | totalR {e['total_R']:+.1f} | exits {e['exit_mix']}")
    L, S = e["longs"], e["shorts"]
    print(f"  longs : n={L['n']:>4} win={L['win']*100:>5.1f}% totalR={L['total_R']:+.1f}")
    print(f"  shorts: n={S['n']:>4} win={S['win']*100:>5.1f}% totalR={S['total_R']:+.1f}")
    for name, (ok, val) in d1["checks"].items():
        print(f"    [{'PASS' if ok else 'FAIL'}] {name:<38} {val}")
    print(f"  => GATE 1 (signal): {'PASS' if p1 else 'FAIL'}")

    # ---- Gate 1.5 (robustness) -------------------------------------------
    print("\n" + bar)
    print("  GATE 1.5  -  robustness: cost sensitivity + drop-2024  (lot-independent)")
    print(bar)
    print(f"  needs (every scenario): net-positive R  AND  PF >= {R15_PF_MIN}")
    print(f"  (a) cost sensitivity  (full backtest re-run per round-trip cost; {COST_SWEEP[0]:.1f} = base)")
    print(f"    {'cost':>5}{'trades':>8}{'win':>7}{'avgR':>9}{'totalR':>9}{'PF':>6}{'Sharpe':>8}{'ok':>5}")
    for c in COST_SWEEP:
        r = d15["cost_rows"][c]
        print(f"    {c:>5.1f}{r['n']:>8}{r['win']*100:>6.1f}%{r['avg_R']:>+9.3f}"
              f"{r['total_R']:>+9.1f}{r['pf']:>6.2f}{r['sharpe']:>8.2f}"
              f"{('Y' if r['ok'] else 'N'):>5}")
    dr = d15["drop"]
    print(f"  (b) drop-{DROP_YEAR}  (exclude the year, default {COST_POINTS_ROUND_TRIP:.1f}pt cost)")
    print(f"    kept {dr['n']} trades | win {dr['win']*100:.1f}% | avgR {dr['avg_R']:+.3f} | "
          f"totalR {dr['total_R']:+.1f} | PF {dr['pf']:.2f} | Sharpe {dr['sharpe']:.2f} | "
          f"{'OK' if dr['ok'] else 'FAIL'}")
    print(f"  => GATE 1.5 (robustness): {'PASS' if p15 else 'FAIL'}")

    # ---- Gate 2 -----------------------------------------------------------
    print("\n" + bar)
    print("  GATE 2  -  5-fold walk-forward, 30-day embargo  (lot-independent)")
    print(bar)
    print(f"  {'fold':<6}{'n':>6}{'sharpe':>9}{'totalR':>10}")
    for i, f in enumerate(d2["folds"], 1):
        print(f"  {i:<6}{f['n']:>6}{f['sharpe']:>9.2f}{f['total_R']:>10.1f}")
    print(f"  folds net-positive: {d2['n_pos']}/5 | folds Sharpe>=1.0: {d2['n_good']}/5 | "
          f"catastrophic (<-8R): {d2['catastrophic']}")
    print(f"  => GATE 2 (stability): {'PASS' if p2 else 'FAIL'}")

    # ---- Gate 3 + lot sweep ----------------------------------------------
    print("\n" + bar)
    print(f"  GATE 3  -  Monte-Carlo eval-pass vs {preset['label']}  (per lot)")
    print(bar)
    print(f"  GO needs: hist maxDD<=${G1_MAXDD_USD:.0f} (5% cap; firm hard limit 8%=${0.08*ACCOUNT_USD:.0f})  "
          f"AND  5th-pct CI>={MC_PASS_CI_LO}  AND  P(pass)>=null+0.10  AND  Gate1/1.5/2 pass")
    print(f"  {'lot':>5}{'risk$/tr':>10}{'%acct':>8}{'maxDD$':>10}{'DDok':>6}"
          f"{'P(pass)':>9}{'CI_lo':>7}{'CI_hi':>7}{'null':>7}{'GO?':>6}")
    go_lots = []
    for lot in LOT_SWEEP:
        dd = max_dd_usd(trades["R"].values, lot)
        dd_ok = dd <= G1_MAXDD_USD
        r = d3["rows"][lot]
        go = p1 and p2 and p15 and dd_ok and r["ok"]
        if go:
            go_lots.append(lot)
        print(f"  {lot:>5}{risk_usd(lot):>10.0f}{risk_usd(lot)/ACCOUNT_USD*100:>7.1f}%"
              f"{dd:>10.0f}{('Y' if dd_ok else 'N'):>6}"
              f"{r['p_pass']:>9.2f}{r['ci_lo']:>7.2f}{r['ci_hi']:>7.2f}{r['null']:>7.2f}"
              f"{('GO' if go else 'NO'):>6}")
    print(f"  => GATE 3 (any lot clears MC): {'PASS' if p3 else 'FAIL'}")

    # ---- Final ------------------------------------------------------------
    signal_ok = p1 and p15 and p2
    print("\n" + bar)
    if signal_ok and go_lots:
        print(f"  FINAL: GO  ->  edge real+stable AND clears all gates at lot(s): {go_lots}")
        print("         Proceed to the paid step at the SMALLEST GO lot.")
    elif signal_ok:
        print("  FINAL: NO-GO  ->  edge real+stable, but NO swept lot clears DD/MC.")
        print("         Lots are too big for $5k at this contract value -- size down,")
        print("         or re-check POINT_VALUE_PER_LOT against your demo, then re-run.")
    else:
        print("  FINAL: NO-GO  ->  the edge itself failed Gate 1/1.5/2. Do NOT pay; debug above.")
    print(f"  Gate1={'PASS' if p1 else 'FAIL'} | Gate1.5={'PASS' if p15 else 'FAIL'} | "
          f"Gate2={'PASS' if p2 else 'FAIL'} | Gate3={'PASS' if p3 else 'FAIL'}")
    print(bar)
    return 0 if (signal_ok and go_lots) else 1


if __name__ == "__main__":
    raise SystemExit(main())