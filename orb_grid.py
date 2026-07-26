"""
orb_grid.py — Step 5: Aggressive combination grid
=================================================
Unified ORB strategy parameterised so cerebro.optstrategy() sweeps V1- and
V4-style configurations + an optional one-shot VWAP direction filter
in a single grid.

Grid (3 x 4 x 3 x 2 x 2 = 144 combinations):
  range_window_min  : [15, 30, 45]
  target_mult       : [1.0, 1.5, 2.0, 2.5]
  atr_gate_mult     : [0.0, 1.5, 2.0]      # 0.0 = gate disabled
  use_vwap_filter   : [0, 1]                # 0 = no filter
  cutoff_hour       : [11, 14]

Look-ahead fix vs V4:
  V4 read self.atr[0] from the daily-resampled feed. Intraday, that daily
  bar is still forming, so [0] silently leaks today's range into the ATR
  used to gate today's trade. This strategy uses self.atr[-1]
  (previous closed daily bar) instead.

Run:
  python orb_grid.py

Outputs:
  data_clean/step5_grid_results.csv   (one row per combo, sorted by Sharpe)
  Top 10 by Sharpe (filtered trades >= 100) printed to stdout.
"""

import os
import sys
import csv
import time
import datetime
import multiprocessing as mp

import backtrader as bt
import pandas as pd

from orb_common import NQData, RTH_VWAP, make_cerebro

DATA_DIR    = os.path.join(os.path.dirname(__file__), "data_clean")
CSV_1MIN    = os.path.join(DATA_DIR, "NQ_1min_rth.csv")
CSV_DAILY   = os.path.join(DATA_DIR, "NQ_daily_rth.csv")
RESULTS_CSV = os.path.join(DATA_DIR, "step5_grid_results.csv")


# ── DAILY FEED PREP ───────────────────────────────────────────────────────────
def ensure_daily_csv(src_1min: str, dst_daily: str) -> None:
    """Build a daily RTH CSV from the 1-min RTH file once; reused across runs.
    Plain GenericCSVData feeds pickle cleanly across optstrategy workers,
    in-cerebro resampledata does not always."""
    if os.path.exists(dst_daily):
        return
    print(f"Building daily feed from {src_1min} ...")
    df = pd.read_csv(src_1min, parse_dates=["datetime"])
    daily = (
        df.set_index("datetime")
          .resample("1D", label="left", closed="left")
          .agg(open=("open",  "first"),
               high=("high",  "max"),
               low=("low",   "min"),
               close=("close","last"),
               volume=("volume","sum"))
          .dropna(subset=["open"])
          .reset_index()
    )
    daily["datetime"] = daily["datetime"].dt.strftime("%Y-%m-%d %H:%M:%S")
    daily[["datetime","open","high","low","close","volume"]].to_csv(dst_daily, index=False)
    print(f"  -> {dst_daily}  ({len(daily):,} rows)")


# ── UNIFIED ORB STRATEGY ──────────────────────────────────────────────────────
class ORB_Unified(bt.Strategy):
    """
    Single-trade-per-day ORB.

      Range          09:30 -> 09:30 + range_window_min   (exclusive endpoint)
      Entry          stop-buy 1 tick above range_high, stop-sell 1 tick below low
      Stop           opposite range edge ± 1 tick
      Target         entry ± target_mult * range_width
      ATR gate       if atr_gate_mult > 0 and range_width >
                       atr_gate_mult * ATR(14)[-1], skip the day
      VWAP filter    if use_vwap_filter:
                       place LONG  stop only if range_high > VWAP(range_end)
                       place SHORT stop only if range_low  < VWAP(range_end)
      Cutoff         after cutoff_hour:00 pending entries are cancelled
      Force-close    flat at 15:45 ET

    Sizing handled by FixedFractionalSizer reading self.risk_pts.
    """

    params = (
        # swept by optstrategy
        ("range_window_min", 30),
        ("target_mult",      1.0),
        ("atr_gate_mult",    0.0),
        ("use_vwap_filter",   0),
        ("cutoff_hour",      14),
        # fixed
        ("entry_offset_ticks", 1),
        ("atr_period",        14),
        ("cutoff_min",         0),
        ("close_hour",        15),
        ("close_min",         45),
        ("rth_start_hour",     9),
        ("rth_start_min",     30),
        ("tick_size",         0.25),
        ("verbose",            False),
    )

    def __init__(self):
        self.data_1min  = self.datas[0]
        self.data_daily = self.datas[1]

        self.atr  = bt.indicators.ATR(self.data_daily, period=self.p.atr_period)
        self.vwap = RTH_VWAP(
            self.data_1min,
            rth_start_hour=self.p.rth_start_hour,
            rth_start_minute=self.p.rth_start_min,
        )

        self._reset_daily_state()
        self.risk_pts     = 0.0
        self._long_order  = None
        self._short_order = None
        self._stop_order  = None
        self._tgt_order   = None

    # ── daily state ────────────────────────────────────────────────────────
    def _reset_daily_state(self):
        self._range_high  = None
        self._range_low   = None
        self._range_width = None
        self._range_built = False
        self._trade_taken = False
        self._in_position = False
        self._direction   = None

    # ── time helpers ───────────────────────────────────────────────────────
    def _bar_dt(self):     return self.data_1min.datetime.datetime(0)
    def _bar_time(self):   return self._bar_dt().time()
    def _rth_start(self):  return datetime.time(self.p.rth_start_hour, self.p.rth_start_min)
    def _range_end(self):
        base = datetime.datetime.combine(datetime.date.today(), self._rth_start())
        return (base + datetime.timedelta(minutes=self.p.range_window_min)).time()
    def _cutoff_time(self):return datetime.time(self.p.cutoff_hour, self.p.cutoff_min)
    def _close_time(self): return datetime.time(self.p.close_hour,  self.p.close_min)

    # ── order helpers ──────────────────────────────────────────────────────
    def _cancel_entries(self):
        for o in (self._long_order, self._short_order):
            if o and o.status in (o.Created, o.Accepted, o.Partial):
                self.cancel(o)
        self._long_order  = None
        self._short_order = None

    def _is_entry_order(self, order):
        return order in (self._long_order, self._short_order)

    def _atr_prev(self):
        """Previous *closed* daily ATR — avoids intraday look-ahead."""
        if len(self.atr) < self.p.atr_period + 1:
            return None
        return self.atr[-1]

    # ── main bar loop ──────────────────────────────────────────────────────
    def next(self):
        t      = self._bar_time()
        tick   = self.p.tick_size
        offset = self.p.entry_offset_ticks * tick

        # A. day rollover
        if t == self._rth_start():
            if self._in_position:
                self.close()
            self._cancel_entries()
            self._reset_daily_state()

        # B. force-close
        if t >= self._close_time() and self._in_position:
            self._cancel_entries()
            self.close()
            return

        # C. cutoff: cancel un-filled entries
        if (t >= self._cutoff_time()
                and not self._in_position
                and not self._trade_taken):
            self._cancel_entries()
            self._trade_taken = True

        if self._trade_taken:
            return

        # D. build range
        if t >= self._rth_start() and t < self._range_end():
            h = self.data_1min.high[0]
            l = self.data_1min.low[0]
            if self._range_high is None:
                self._range_high, self._range_low = h, l
            else:
                self._range_high = max(self._range_high, h)
                self._range_low  = min(self._range_low,  l)
            return

        # E. range end: maybe place entry stops
        if (t == self._range_end()
                and not self._range_built
                and self._range_high is not None
                and t < self._cutoff_time()):

            self._range_built = True
            self._range_width = self._range_high - self._range_low
            if self._range_width <= 0:
                self._trade_taken = True
                return

            # ATR gate (uses previous closed daily ATR — no look-ahead)
            if self.p.atr_gate_mult > 0:
                atr_prev = self._atr_prev()
                if atr_prev is None or atr_prev <= 0:
                    self._trade_taken = True  # warmup -> safe skip
                    return
                if self._range_width > self.p.atr_gate_mult * atr_prev:
                    self._trade_taken = True
                    return

            # VWAP filter: decide which legs to place
            place_long  = True
            place_short = True
            if self.p.use_vwap_filter:
                vw = self.vwap.vwap[0]
                place_long  = self._range_high > vw
                place_short = self._range_low  < vw
                if not (place_long or place_short):
                    self._trade_taken = True
                    return

            # Risk for the sizer = range_width + offset (matches V1/V4)
            self.risk_pts = self._range_width + offset

            long_entry  = self._range_high + offset
            short_entry = self._range_low  - offset

            if place_long:
                self._long_order = self.buy(
                    exectype=bt.Order.Stop, price=long_entry, transmit=True)
                self._long_order.addinfo(
                    rw=self._range_width,
                    rng_high=self._range_high,
                    rng_low=self._range_low,
                )
            if place_short:
                self._short_order = self.sell(
                    exectype=bt.Order.Stop, price=short_entry, transmit=True)
                self._short_order.addinfo(
                    rw=self._range_width,
                    rng_high=self._range_high,
                    rng_low=self._range_low,
                )

    # ── notifications ──────────────────────────────────────────────────────
    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            return

        if order.status != order.Completed:
            return

        if not self._is_entry_order(order):
            return  # exit fills handled by notify_trade

        rw       = order.info.get("rw",       self._range_width or 0)
        rng_high = order.info.get("rng_high", self._range_high  or 0)
        rng_low  = order.info.get("rng_low",  self._range_low   or 0)
        if not rw:
            return

        self._trade_taken = True
        self._in_position = True
        entry = order.executed.price
        off   = self.p.entry_offset_ticks * self.p.tick_size
        size  = abs(order.executed.size)

        if order.isbuy():
            self._direction = "long"
            stop_px   = rng_low  - off
            target_px = entry + rw * self.p.target_mult
            if self._short_order:
                self.cancel(self._short_order)
                self._short_order = None
            self._stop_order = self.sell(
                size=size, exectype=bt.Order.Stop,  price=stop_px,   transmit=False)
            self._tgt_order  = self.sell(
                size=size, exectype=bt.Order.Limit, price=target_px, transmit=True)
        else:
            self._direction = "short"
            stop_px   = rng_high + off
            target_px = entry - rw * self.p.target_mult
            if self._long_order:
                self.cancel(self._long_order)
                self._long_order = None
            self._stop_order = self.buy(
                size=size, exectype=bt.Order.Stop,  price=stop_px,   transmit=False)
            self._tgt_order  = self.buy(
                size=size, exectype=bt.Order.Limit, price=target_px, transmit=True)

    def notify_trade(self, trade):
        if trade.isclosed:
            self._in_position = False
            self._stop_order  = None
            self._tgt_order   = None


# ── GRID RUNNER ───────────────────────────────────────────────────────────────
def _row_from_strategy(strat) -> dict:
    p  = strat.params
    sh = strat.analyzers.sharpe.get_analysis()
    dd = strat.analyzers.drawdown.get_analysis()
    tr = strat.analyzers.trades.get_analysis()

    n_total = tr.get("total", {}).get("total", 0)
    won  = tr.get("won",  {}).get("total", 0)
    lost = tr.get("lost", {}).get("total", 0)
    net  = tr.get("pnl",  {}).get("net", {}).get("total", 0.0)
    wr   = (won / n_total * 100) if n_total else 0.0
    sharpe = sh.get("sharperatio") or 0.0
    dd_p   = dd.get("max", {}).get("drawdown",  0.0)
    dd_m   = dd.get("max", {}).get("moneydown", 0.0)
    avg_w  = tr.get("won",  {}).get("pnl", {}).get("average", 0.0)
    avg_l  = tr.get("lost", {}).get("pnl", {}).get("average", 0.0)
    return {
        "range_window_min": p.range_window_min,
        "target_mult":      p.target_mult,
        "atr_gate_mult":    p.atr_gate_mult,
        "use_vwap_filter":  p.use_vwap_filter,
        "cutoff_hour":      p.cutoff_hour,
        "trades":   n_total,
        "won":      won,
        "lost":     lost,
        "win_rate": round(wr, 2),
        "net_pnl":  round(net, 2),
        "sharpe":   round(sharpe, 3),
        "max_dd_pct": round(dd_p, 2),
        "max_dd_usd": round(dd_m, 2),
        "avg_win":  round(avg_w, 2),
        "avg_loss": round(avg_l, 2),
    }


def run_grid(verbose: bool = True) -> None:
    if not os.path.exists(CSV_1MIN):
        sys.exit(f"ERROR: {CSV_1MIN} not found. Run step0_data_prep.py first.")
    ensure_daily_csv(CSV_1MIN, CSV_DAILY)

    range_windows = [15, 30, 45]
    target_mults  = [1.0, 1.5, 2.0, 2.5]
    atr_gates     = [0.0, 1.5, 2.0]
    vwap_filters  = [0, 1]
    cutoff_hours  = [11, 14]
    total = (len(range_windows) * len(target_mults) * len(atr_gates)
             * len(vwap_filters) * len(cutoff_hours))
    if verbose:
        print(f"Grid size: {total} combinations")

    cerebro = make_cerebro(CSV_1MIN, cash=100_000, risk_pct=0.01)

    # Separate daily feed — picklable across optstrategy workers
    daily_feed = bt.feeds.GenericCSVData(
        dataname=CSV_DAILY,
        dtformat="%Y-%m-%d %H:%M:%S",
        datetime=0, open=1, high=2, low=3, close=4, volume=5,
        openinterest=-1,
        timeframe=bt.TimeFrame.Days,
        compression=1,
    )
    cerebro.adddata(daily_feed, name="NQ_daily")

    cerebro.optstrategy(
        ORB_Unified,
        range_window_min=range_windows,
        target_mult=target_mults,
        atr_gate_mult=atr_gates,
        use_vwap_filter=vwap_filters,
        cutoff_hour=cutoff_hours,
    )

    cpus = max(1, (mp.cpu_count() or 2) - 1)
    if verbose:
        print(f"Running on {cpus} CPUs ...")

    t0 = time.time()
    opt_runs = cerebro.run(maxcpus=cpus, optreturn=False)
    elapsed = time.time() - t0
    if verbose:
        print(f"Done in {elapsed/60:.1f} min  ({len(opt_runs)} runs)")

    rows = [_row_from_strategy(run[0]) for run in opt_runs]
    rows.sort(key=lambda r: (r["sharpe"], r["net_pnl"]), reverse=True)

    os.makedirs(DATA_DIR, exist_ok=True)
    with open(RESULTS_CSV, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    if verbose:
        print(f"Saved {len(rows)} rows -> {RESULTS_CSV}")

        keep = [r for r in rows if r["trades"] >= 100]
        print(f"\nTop 10 by Sharpe (filtered trades >= 100; "
              f"{len(keep)} of {len(rows)} survived):")
        for r in keep[:10]:
            print(f"  rw={r['range_window_min']:>2}  tgt={r['target_mult']:.1f}  "
                  f"atr={r['atr_gate_mult']:.1f}  vwap={r['use_vwap_filter']}  "
                  f"cut={r['cutoff_hour']:>2} | "
                  f"trades={r['trades']:>4}  wr={r['win_rate']:>5.1f}%  "
                  f"net=${r['net_pnl']:>10,.0f}  "
                  f"sharpe={r['sharpe']:>+.3f}  dd={r['max_dd_pct']:>5.1f}%")


if __name__ == "__main__":
    run_grid()