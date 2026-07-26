#!/usr/bin/env python3
"""
daily_calmar_sprint.py
======================
SPECIALIZED: DAILY window | leaderboard top-K | Calmar (return/maxDD) scoring
| FREE entry | asset varies (maybe no history).

KEY FACT that flips the generic advice:
  Calmar = return / maxDD is (to first order) INVARIANT to position size --
  scaling every bet by k scales numerator AND denominator. So BOLD SIZING DOES
  NOT IMPROVE RANK. The levers are TRADE STRUCTURE:
    tight initial stop -> small DD denominator
    trailing exit      -> let a winner run -> big numerator on trend days
    conviction gate    -> only trade days likely to produce a clean run
    few trades/day     -> fewer drawdown opportunities
    a real edge        -> raises P(a clean winning day)
  Rank top-K => you need a RIGHT-TAIL 'monster Calmar' day, so tune the 90th
  percentile of daily Calmar, NOT the mean. Free daily entry => enter many.

Reuses features()/signal() from competition_engine.py (same folder).
"""
from __future__ import annotations
import numpy as np
import pandas as pd
from competition_engine import features, signal


def simulate_day(day, sg, params):
    """One day's intraday bars + aligned signals -> daily Calmar (in R units).
    Tight initial stop + ATR trailing exit; up to max_trades conviction entries."""
    high, low, close = day["high"].values, day["low"].values, day["close"].values
    side, atr, score = sg["side"].values, sg["atr"].values, sg["score"].values
    n = len(day)
    eq = peak = maxdd = 0.0
    trades = 0; i = 0
    while i < n - 1 and trades < params["max_trades"]:
        conf = score[i] if side[i] == 1 else (1 - score[i]) if side[i] == -1 else 0.5
        if side[i] == 0 or conf < params["conf_gate"] or atr[i] <= 0 or np.isnan(atr[i]):
            i += 1; continue
        s = int(side[i]); entry = close[i]; risk = params["k_stop"] * atr[i]
        best = entry; stop = entry - s * risk; exit_px = None; j = i + 1
        while j < n:
            if s == 1:
                best = max(best, high[j]); stop = max(stop, best - params["trail"] * atr[i])
                dip = eq + (low[j] - entry) / risk * s
                peak = max(peak, dip); maxdd = max(maxdd, peak - dip)
                if low[j] <= stop: exit_px = stop; break
            else:
                best = min(best, low[j]); stop = min(stop, best + params["trail"] * atr[i])
                dip = eq + (high[j] - entry) / risk * s
                peak = max(peak, dip); maxdd = max(maxdd, peak - dip)
                if high[j] >= stop: exit_px = stop; break
            j += 1
        if exit_px is None: exit_px = close[min(j, n - 1)]
        eq += (exit_px - entry) / risk * s
        peak = max(peak, eq); maxdd = max(maxdd, peak - eq)
        trades += 1; i = j + 1
    calmar = eq / maxdd if maxdd > 1e-9 else (eq if eq > 0 else 0.0)
    return {"ret_R": eq, "maxdd_R": maxdd, "calmar": calmar, "n": trades}


def daily_calmars(df, params):
    """Compute features/signal once, then one Calmar per calendar day."""
    feat = features(df, L=params["L"]); sg = signal(feat, thr=params["thr"])
    rows = []
    for day, idx in df.groupby(df.index.normalize()).groups.items():
        d = df.loc[idx]; s = sg.loc[idx]
        if len(d) < 5: continue
        r = simulate_day(d, s, params); r["day"] = day; rows.append(r)
    return pd.DataFrame(rows)


def walk_forward_tail(df, grid, n_folds=5, embargo_days=3):
    """Select params by OOS 90th-pct daily Calmar (the right tail that ranks)."""
    days = np.array(sorted(pd.unique(df.index.normalize())))
    folds = np.array_split(np.arange(len(days)), n_folds + 1)
    oos, chosen = [], []
    for f in range(1, n_folds + 1):
        cut = folds[f][0]
        tr_days = days[:max(0, cut - embargo_days)]
        te_days = days[cut: folds[f][-1] + 1]
        if len(tr_days) < 30 or len(te_days) < 10: continue
        tr_df = df[df.index.normalize().isin(tr_days)]
        te_df = df[df.index.normalize().isin(te_days)]
        best, best_tail = None, -1e18
        for g in grid:
            dc = daily_calmars(tr_df, g)
            if len(dc) < 20: continue
            tail = np.percentile(dc["calmar"], 90)      # tune the RIGHT TAIL
            if tail > best_tail: best_tail, best = tail, g
        if best is None: continue
        dc = daily_calmars(te_df, best); dc["fold"] = f
        oos.append(dc); chosen.append(best)
    oos = pd.concat(oos, ignore_index=True) if oos else pd.DataFrame()
    return oos, chosen


def rank_probability(oos_calmar, win_threshold):
    """P(a day's Calmar beats the level that historically ranks top-K)."""
    c = np.asarray(oos_calmar, float)
    return float((c >= win_threshold).mean())


def deploy_today(df_recent, params):
    """Cold-start safe: defaults still produce a ticket with no fitting."""
    feat = features(df_recent, L=params["L"]); sg = signal(feat, thr=params["thr"])
    last = sg.iloc[-1]; side = int(last["side"]); score = float(last["score"])
    conf = score if side == 1 else (1 - score) if side == -1 else 0.5
    atr = float(last["atr"]); risk = params["k_stop"] * atr
    return {
        "fire": bool(side != 0 and conf >= params["conf_gate"]),
        "side": {1: "LONG", -1: "SHORT", 0: "FLAT"}[side],
        "confidence": round(conf, 3),
        "initial_stop_distance": round(risk, 4),
        "exit": f"ATR trailing stop, trail={params['trail']}xATR (let it run, no fixed target)",
        "size_note": "Use platform max within margin. Size is IRRELEVANT to Calmar rank "
                     "-- it cancels in return/DD. Do NOT oversize to climb.",
    }


DEFAULTS = {"L": 20, "thr": 0.5, "k_stop": 1.0, "trail": 2.0,
            "conf_gate": 0.58, "max_trades": 2}


if __name__ == "__main__":
    import yfinance as yf
    df = yf.download("BTC-USD", interval="1h", period="360d", progress=False)
    df.columns = [str(c[0]).lower() if isinstance(c, tuple) else str(c).lower()
                  for c in df.columns]
    df = df[["open", "high", "low", "close"]].dropna()

    grid = [dict(L=L, thr=t, k_stop=k, trail=tr, conf_gate=0.58, max_trades=2)
            for L in (10, 20, 30) for t in (0.5, 0.75)
            for k in (0.75, 1.0) for tr in (1.5, 2.5)]
    oos, chosen = walk_forward_tail(df, grid)
    print("chosen per fold:", chosen)
    if len(oos):
        print("OOS days:", len(oos),
              "| median Calmar:", round(oos['calmar'].median(), 2),
              "| 90th pct:", round(np.percentile(oos['calmar'], 90), 2),
              "| best day:", round(oos['calmar'].max(), 2))
        # null: shuffle the daily Calmars' sign-bearing structure via random signal
        print("P(monster day, Calmar>=5):", rank_probability(oos['calmar'], 5.0))
    print("today:", deploy_today(df.tail(300), chosen[-1] if chosen else DEFAULTS))