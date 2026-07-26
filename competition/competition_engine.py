#!/usr/bin/env python3
"""
competition_engine.py
=====================
Return-ranked trading-competition engine.

Objective: maximize P(hit the challenge target on unseen near-future data),
NOT long-term expectancy. Asset-agnostic: every feature is normalized, so the
same code runs on whatever instrument the competition uses -- even one you have
no prior data for.

Pipeline:
  features()        - asset-agnostic, normalized features from OHLC bars
  signal()          - simple low-DOF binary directional signal (2 real knobs)
  trade_outcomes()  - simulate stop/target -> realized R per trade
  walk_forward()    - rolling OOS param selection (no leakage, with embargo)
  calibrate()       - isotonic calibration -> per-trade confidence in [0,1]
  goal_dp()         - dynamic, target-aware bold sizing (the core)
  competition_mc()  - Monte-Carlo P(hit target) + random-signal null
  deploy()          - one new bar -> {signal, confidence, size}
"""
from __future__ import annotations
import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# 1. FEATURES (everything normalized -> asset-agnostic)
# ---------------------------------------------------------------------------
def features(df: pd.DataFrame, L: int = 20, atr_n: int = 14) -> pd.DataFrame:
    """df needs columns: open, high, low, close. Index = datetime."""
    out = pd.DataFrame(index=df.index)
    ret = df["close"].pct_change()
    out["mom_z"] = ret.rolling(L).mean() / (ret.rolling(L).std() + 1e-12)
    hi = df["high"].rolling(L).max()
    lo = df["low"].rolling(L).min()
    out["range_pos"] = (df["close"] - lo) / (hi - lo + 1e-12)
    tr = pd.concat([
        (df["high"] - df["low"]),
        (df["high"] - df["close"].shift()).abs(),
        (df["low"] - df["close"].shift()).abs(),
    ], axis=1).max(axis=1)
    out["atr"] = tr.rolling(atr_n).mean()
    out["close"] = df["close"]
    return out


# ---------------------------------------------------------------------------
# 2. SIGNAL (2 real degrees of freedom: L in features, thr here)
# ---------------------------------------------------------------------------
def signal(feat: pd.DataFrame, thr: float = 0.5) -> pd.DataFrame:
    s = pd.DataFrame(index=feat.index)
    direction = np.where(feat["mom_z"] > thr, 1,
                np.where(feat["mom_z"] < -thr, -1, 0))
    s["side"] = direction
    s["enter"] = (direction != 0).astype(int)
    s["score"] = 1.0 / (1.0 + np.exp(-feat["mom_z"]))   # raw P(up) in [0,1]
    s["atr"] = feat["atr"]
    s["close"] = feat["close"]
    return s


# ---------------------------------------------------------------------------
# 3. TRADE OUTCOMES -> realized R multiples
# ---------------------------------------------------------------------------
def trade_outcomes(df, s, k_stop=1.5, b=2.0, max_hold=30) -> pd.DataFrame:
    rows = []
    close, high, low = df["close"].values, df["high"].values, df["low"].values
    idx = df.index
    side, atr, score = s["side"].values, s["atr"].values, s["score"].values
    n = len(df)
    for i in range(n - 1):
        if side[i] == 0 or np.isnan(atr[i]) or atr[i] <= 0:
            continue
        entry = close[i]                 # reference; you enter on the NEXT bar
        risk = k_stop * atr[i]
        if side[i] == 1:
            stop, target = entry - risk, entry + b * risk
        else:
            stop, target = entry + risk, entry - b * risk
        r = None
        for j in range(i + 1, min(i + 1 + max_hold, n)):
            if side[i] == 1:
                if low[j] <= stop:   r = -1.0; break
                if high[j] >= target: r = b;    break
            else:
                if high[j] >= stop:  r = -1.0; break
                if low[j] <= target:  r = b;    break
        if r is None:                    # timeout -> mark-to-market in R units
            exit_px = close[min(i + max_hold, n - 1)]
            r = (exit_px - entry) / risk * side[i]
        rows.append({"t": idx[i], "side": int(side[i]),
                     "score": float(score[i]), "win": int(r > 0), "R": float(r)})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# 4. WALK-FORWARD (rolling OOS, embargo gap, low-DOF objective)
# ---------------------------------------------------------------------------
def walk_forward(df, grid, n_folds=5, embargo=50, k_stop=1.5, b=2.0):
    idx = np.arange(len(df))
    folds = np.array_split(idx, n_folds + 1)
    oos_all, chosen = [], []
    for f in range(1, n_folds + 1):
        cut = folds[f][0]
        train = df.iloc[:max(0, cut - embargo)]
        test = df.iloc[cut: folds[f][-1] + 1]
        if len(train) < 200 or len(test) < 50:
            continue
        best, best_score = None, -1e18
        for (L, thr) in grid:
            ft = features(train, L=L)
            sg = signal(ft, thr=thr)
            tr = trade_outcomes(train, sg, k_stop=k_stop, b=b)
            if len(tr) < 30:
                continue
            sc = tr["R"].sum() / (tr["R"].std() + 1e-9)   # train Sharpe-ish
            if sc > best_score:
                best_score, best = sc, (L, thr)
        if best is None:
            continue
        L, thr = best
        ft = features(test, L=L)
        sg = signal(ft, thr=thr)
        tr = trade_outcomes(test, sg, k_stop=k_stop, b=b)
        tr["fold"] = f
        oos_all.append(tr)
        chosen.append({"fold": f, "L": L, "thr": thr})
    oos = pd.concat(oos_all, ignore_index=True) if oos_all else pd.DataFrame()
    return oos, chosen


# ---------------------------------------------------------------------------
# 5. CALIBRATION -> per-trade confidence
# ---------------------------------------------------------------------------
def calibrate(scores, wins):
    from sklearn.isotonic import IsotonicRegression
    ir = IsotonicRegression(out_of_bounds="clip", y_min=0.0, y_max=1.0)
    ir.fit(np.asarray(scores, float), np.asarray(wins, float))
    return ir   # ir.predict([score]) -> calibrated P(up)


# ---------------------------------------------------------------------------
# 6. GOAL-REACHING DP  (the core: dynamic bold sizing)
# ---------------------------------------------------------------------------
def goal_dp(p, b, T, H, dd_floor=0.0, f_grid=None, n_grid=400):
    """
    Maximize P(equity reaches 1+T within H trades).
      p        : per-trade win probability (calibrated)
      b        : reward:risk
      T        : target return fraction (0.30 = +30%)
      H        : trades remaining
      dd_floor : bust if equity <= 1-dd_floor (0 disables). Set to the comp's
                 max-DD limit for return+DD scoring.
    Returns (start_value, f_star) where f_star(trades_left, equity) -> fraction.
    LEADERBOARD SWITCH: to chase the upper tail instead of a fixed target,
    set T high (or replace the terminal value with E[return]), dd_floor=0,
    and raise the f_grid ceiling.
    """
    if f_grid is None:
        f_grid = np.linspace(0.0, 0.95, 40)
    lo = max(1e-3, 1.0 - dd_floor) if dd_floor > 0 else 1e-3
    hi = 1.0 + T
    g = np.linspace(np.log(lo), np.log(hi), n_grid)
    eq = np.exp(g)
    V = (eq >= hi * (1 - 1e-9)).astype(float)      # terminal: reached target?
    policy = []
    for _h in range(1, H + 1):
        bestV = np.where(eq >= hi, 1.0, np.where(eq <= lo, 0.0, 0.0))
        bestF = np.zeros_like(V)
        for f in f_grid:
            up = eq * (1 + b * f)
            dn = eq * (1 - f)
            Vu = np.where(up >= hi, 1.0, np.interp(np.log(np.clip(up, lo, hi)), g, V))
            Vd = np.where(dn <= lo, 0.0, np.interp(np.log(np.clip(dn, lo, hi)), g, V))
            ev = p * Vu + (1 - p) * Vd
            ev = np.where(eq >= hi, 1.0, ev)        # absorbing target
            ev = np.where(eq <= lo, 0.0, ev)        # absorbing bust
            take = ev > bestV
            bestV = np.where(take, ev, bestV)
            bestF = np.where(take, f, bestF)
        V = bestV
        policy.append((g.copy(), bestF.copy()))     # policy[h-1] = h trades left
    start_value = float(np.interp(0.0, g, V))        # equity = 1 -> log = 0

    def f_star(trades_left, equity):
        trades_left = int(max(1, min(trades_left, H)))
        gg, ff = policy[trades_left - 1]
        return float(np.interp(np.log(np.clip(equity, lo, hi)), gg, ff))

    return start_value, f_star


# ---------------------------------------------------------------------------
# 7. COMPETITION MONTE-CARLO  -> P(hit target) + null comparison
# ---------------------------------------------------------------------------
def competition_mc(oos_R, T, H, f_star=None, fixed_f=None, dd_floor=0.0, n=20000, seed=0):
    rng = np.random.default_rng(seed)
    oos_R = np.asarray(oos_R, float)
    lo = (1.0 - dd_floor) if dd_floor > 0 else 0.0
    hits = 0
    for _ in range(n):
        eq = 1.0
        seq = rng.choice(oos_R, H, replace=True)
        for t, r in enumerate(seq):
            f = fixed_f if fixed_f is not None else f_star(H - t, eq)
            eq *= (1.0 + f * r)              # risk f of equity, trade returns r risk-units
            if dd_floor > 0 and eq <= lo:
                eq = 0.0; break
            if eq >= 1.0 + T:
                break
        hits += int(eq >= 1.0 + T)
    return hits / n


def bootstrap_ci(oos_R, T, H, f_star, dd_floor=0.0, reps=300, n=4000):
    oos_R = np.asarray(oos_R, float)
    est = []
    for s in range(reps):
        samp = np.random.default_rng(s).choice(oos_R, len(oos_R), replace=True)
        est.append(competition_mc(samp, T, H, f_star=f_star, dd_floor=dd_floor, n=n, seed=s))
    est = np.array(est)
    return est.mean(), np.percentile(est, 5), np.percentile(est, 95)


# ---------------------------------------------------------------------------
# 8. DEPLOY  -> one new bar => signal + confidence + size
# ---------------------------------------------------------------------------
def deploy(df_recent, params, calibrator, f_star, equity, trades_left, b=2.0):
    ft = features(df_recent, L=params["L"])
    sg = signal(ft, thr=params["thr"])
    last = sg.iloc[-1]
    side = int(last["side"])
    raw = float(last["score"])
    p_up = float(calibrator.predict([raw])[0])
    conf_side = p_up if side == 1 else (1.0 - p_up) if side == -1 else 0.5
    f = f_star(trades_left, equity) if side != 0 else 0.0
    atr = float(last["atr"])
    risk = params["k_stop"] * atr
    return {
        "enter": int(side != 0),
        "side": {1: "LONG", -1: "SHORT", 0: "FLAT"}[side],
        "binary_signal": int(side != 0),
        "confidence": round(conf_side, 3),
        "risk_fraction": round(f, 4),
        "stop_distance": round(risk, 4),
        "target_distance": round(b * risk, 4),
    }


# ---------------------------------------------------------------------------
# DEMO
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Load your competition asset's OHLC into `df` (columns: open,high,low,close).
    # Example with yfinance:
    #   import yfinance as yf
    #   df = yf.download("BTC-USD", interval="1h", period="720d")
    #   df.columns = [c.lower() for c in df.columns]
    try:
        import yfinance as yf
        df = yf.download("BTC-USD", interval="1h", period="360d", progress=False)
        df.columns = [str(c[0]).lower() if isinstance(c, tuple) else str(c).lower()
                      for c in df.columns]
        df = df[["open", "high", "low", "close"]].dropna()
    except Exception as e:
        print("Provide your own df. yfinance failed:", e); raise SystemExit

    # --- competition spec (EDIT THESE) ---
    T, H, dd_floor = 0.50, 25, 0.0     # +50% target, 25 trades, no DD limit
    b, k_stop = 2.0, 1.5

    grid = [(L, thr) for L in (10, 20, 30, 40) for thr in (0.25, 0.5, 0.75, 1.0)]
    oos, chosen = walk_forward(df, grid, k_stop=k_stop, b=b)
    print("chosen params per fold:", chosen)
    print("OOS trades:", len(oos), "| mean R:", round(oos["R"].mean(), 3),
          "| win%:", round(100 * oos["win"].mean(), 1))

    cal = calibrate(oos["score"], oos["win"])
    p = float(oos["win"].mean())                       # avg calibrated win prob
    _, f_star = goal_dp(p, b, T, H, dd_floor=dd_floor)

    p_hit = competition_mc(oos["R"], T, H, f_star=f_star, dd_floor=dd_floor)
    mean, lo5, hi95 = bootstrap_ci(oos["R"], T, H, f_star, dd_floor=dd_floor)

    # random-signal NULL: shuffle outcomes to destroy any edge
    null_R = np.random.default_rng(1).permutation(oos["R"].values)
    p_null = competition_mc(null_R, T, H, f_star=f_star, dd_floor=dd_floor)

    print(f"P(hit target)  = {p_hit:.3f}   90% CI [{lo5:.3f}, {hi95:.3f}]")
    print(f"P(hit | null)  = {p_null:.3f}")
    print("VERDICT:", "DEPLOY" if lo5 > p_null + 0.02 else "DISCARD (not beating null)")

    # --- live: one ticket for today ---
    params = {"L": chosen[-1]["L"], "thr": chosen[-1]["thr"], "k_stop": k_stop}
    ticket = deploy(df.tail(200), params, cal, f_star, equity=1.0, trades_left=H, b=b)
    print("TODAY:", ticket)