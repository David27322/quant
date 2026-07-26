"""
orb_v4_atr.py — V4: ATR-gated 30-min ORB  (Kaufman TSM Ch.15 variant)
=======================================================================
Spec:
  - RTH session; range window 09:30–10:00 (same as V1)
  - ATR(14) on DAILY RTH bars; if today's opening range > atr_mult x ATR -> skip
  - Entry: identical to V1 (stop-buy/sell 1 tick beyond range)
  - Stop  : opposite side of range + 1 tick (no hard cap — ATR gate handles it)
  - Target: 2x range width (R:R 2:1)
  - Cutoff: no new entries after 14:00 ET
  - Force-close: 15:45 ET
  - One trade per day; no re-entry

Implementation note:
  Two data feeds required:
    datas[0] = 1-min RTH feed  (NQ_1min_rth.csv)
    datas[1] = daily RTH feed  (resampled from 1-min inside cerebro)
  We compute ATR on the daily feed using bt.indicators.ATR.

Run standalone:
    python orb_v4_atr.py
"""

import datetime
import backtrader as bt
from orb_common import NQData, FixedFractionalSizer, make_cerebro, print_results

import os, sys
DATA_DIR = os.path.join(os.path.dirname(__file__), "data_clean")


class ORB_V4_ATR(bt.Strategy):

    params = (
        ("range_window_min",    30),
        ("entry_offset_ticks",   1),
        ("atr_period",          14),
        ("atr_mult",           1.5),    # skip day if range > mult * ATR
        ("target_mult",        2.0),
        ("cutoff_hour",         14),
        ("cutoff_min",           0),
        ("close_hour",          15),
        ("close_min",           45),
        ("rth_start_hour",       9),
        ("rth_start_min",       30),
        ("tick_size",          0.25),
        ("verbose",            True),
    )

    def __init__(self):
        self.data_1min  = self.datas[0]
        self.data_daily = self.datas[1]   # resampled daily feed

        # ATR on daily bars — Wilder smoothing (bt default)
        self.atr = bt.indicators.ATR(
            self.data_daily,
            period=self.p.atr_period,
            plotname="ATR_daily",
        )

        self._reset_daily_state()
        self.risk_pts    = 0.0
        self._long_order  = None
        self._short_order = None
        self._stop_order  = None
        self._tgt_order   = None

    def _reset_daily_state(self):
        self._range_high  = None
        self._range_low   = None
        self._range_built = False
        self._trade_taken = False
        self._in_position = False
        self._direction   = None
        self._range_width = None

    def _bar_dt(self):
        return self.data_1min.datetime.datetime(0)

    def _bar_time(self):
        return self._bar_dt().time()

    def _rth_start(self):
        return datetime.time(self.p.rth_start_hour, self.p.rth_start_min)

    def _range_end(self):
        base = datetime.datetime.combine(datetime.date.today(), self._rth_start())
        return (base + datetime.timedelta(minutes=self.p.range_window_min)).time()

    def _cutoff_time(self):
        return datetime.time(self.p.cutoff_hour, self.p.cutoff_min)

    def _close_time(self):
        return datetime.time(self.p.close_hour, self.p.close_min)

    def _cancel_pending(self):
        for o in [self._long_order, self._short_order]:
            if o and o.status in [o.Created, o.Accepted, o.Partial]:
                self.cancel(o)
        self._long_order  = None
        self._short_order = None

    def next(self):
        t      = self._bar_time()
        tick   = self.p.tick_size
        offset = self.p.entry_offset_ticks * tick

        # --- day rollover ---
        if t == self._rth_start():
            if self._in_position:
                self.close()
            self._cancel_pending()
            self._reset_daily_state()

        # --- force-close ---
        if t >= self._close_time() and self._in_position:
            self._cancel_pending()
            self.close()
            if self.p.verbose:
                print(f"  [V4] {self._bar_dt()}  Force-closed")
            return

        if self._trade_taken:
            return

        # --- build range ---
        if t >= self._rth_start() and t < self._range_end():
            h = self.data_1min.high[0]
            l = self.data_1min.low[0]
            if self._range_high is None:
                self._range_high, self._range_low = h, l
            else:
                self._range_high = max(self._range_high, h)
                self._range_low  = min(self._range_low,  l)
            return

        # --- place orders at range end ---
        if (t == self._range_end()
                and not self._range_built
                and self._range_high is not None
                and t < self._cutoff_time()):

            self._range_built = True
            self._range_width = self._range_high - self._range_low

            if self._range_width <= 0:
                return

            # ATR gate: use prior day's ATR (atr[0] is current completed value)
            current_atr = self.atr[0]
            if current_atr and current_atr > 0:
                atr_threshold = current_atr * self.p.atr_mult
                if self._range_width > atr_threshold:
                    self._trade_taken = True   # skip wide day
                    if self.p.verbose:
                        print(f"  [V4] {self._bar_dt()}  ATR GATE triggered — "
                              f"range={self._range_width:.0f} > "
                              f"{self.p.atr_mult}x ATR({self.p.atr_period})"
                              f"={atr_threshold:.0f} — skip")
                    return

            self.risk_pts = self._range_width + offset

            long_entry  = self._range_high + offset
            short_entry = self._range_low  - offset

            self._long_order = self.buy(
                exectype=bt.Order.Stop, price=long_entry, transmit=True)
            self._long_order.addinfo(
                rw=self._range_width,
                rng_high=self._range_high,
                rng_low=self._range_low,
            )
            self._short_order = self.sell(
                exectype=bt.Order.Stop, price=short_entry, transmit=True)
            self._short_order.addinfo(
                rw=self._range_width,
                rng_high=self._range_high,
                rng_low=self._range_low,
            )

            if self.p.verbose:
                print(f"  [V4] {self._bar_dt()}  "
                      f"Range {self._range_low:.2f}-{self._range_high:.2f} "
                      f"width={self._range_width:.2f}  "
                      f"ATR={current_atr:.2f}  "
                      f"L@{long_entry:.2f} S@{short_entry:.2f}")

    def _is_entry_order(self, order):
        return order in (self._long_order, self._short_order)

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed:
            # Only handle entry fills — exit orders (stop/target) manage themselves
            if self._is_entry_order(order):
                rw       = order.info.get("rw",       self._range_width or 0)
                rng_high = order.info.get("rng_high", self._range_high  or 0)
                rng_low  = order.info.get("rng_low",  self._range_low   or 0)

                if not rw:
                    if self.p.verbose:
                        print(f"  [V4] {self._bar_dt()}  WARNING: rw=0 on fill, skipping exits")
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
                        size=size, exectype=bt.Order.Stop,
                        price=stop_px, transmit=False)
                    self._tgt_order  = self.sell(
                        size=size, exectype=bt.Order.Limit,
                        price=target_px, transmit=True)
                else:
                    self._direction = "short"
                    stop_px   = rng_high + off
                    target_px = entry - rw * self.p.target_mult
                    if self._long_order:
                        self.cancel(self._long_order)
                        self._long_order = None
                    self._stop_order = self.buy(
                        size=size, exectype=bt.Order.Stop,
                        price=stop_px, transmit=False)
                    self._tgt_order  = self.buy(
                        size=size, exectype=bt.Order.Limit,
                        price=target_px, transmit=True)

                if self.p.verbose:
                    print(f"  [V4] {self._bar_dt()}  "
                          f"FILLED {self._direction.upper()} "
                          f"entry={entry:.2f} stop={stop_px:.2f} "
                          f"target={target_px:.2f} size={size}")

    def notify_trade(self, trade):
        if trade.isclosed:
            self._in_position = False
            self._stop_order  = None
            self._tgt_order   = None
            if self.p.verbose:
                print(f"  [V4] {self._bar_dt()}  "
                      f"Closed pnl={trade.pnl:.2f} net={trade.pnlcomm:.2f}")


# ── STANDALONE RUN ────────────────────────────────────────────────────────────

def run_v4(csv_1min, cash=100_000, risk_pct=0.01, verbose=True):
    """
    V4 needs two feeds: 1-min + daily resampled.
    We add the 1-min feed then resample it inside cerebro.
    """
    cerebro = make_cerebro(csv_1min, cash=cash, risk_pct=risk_pct)

    # Add a daily resampled version of the same data for ATR
    data_daily = NQData(dataname=csv_1min)
    cerebro.resampledata(
        data_daily,
        timeframe=bt.TimeFrame.Days,
        compression=1,
        name="NQ_daily",
    )

    cerebro.addstrategy(ORB_V4_ATR, verbose=verbose)
    return cerebro


if __name__ == "__main__":
    csv = os.path.join(DATA_DIR, "NQ_1min_rth.csv")
    if not os.path.exists(csv):
        sys.exit(f"ERROR: {csv} not found.")

    cerebro = run_v4(csv, cash=100_000, risk_pct=0.01, verbose=True)

    print("Running V4 ATR-gated 30-min ORB ...")
    start_val = cerebro.broker.getvalue()
    results   = cerebro.run()
    end_val   = cerebro.broker.getvalue()

    print_results(results[0], label="V4 ATR")
    print(f"  Start: ${start_val:,.0f}  End: ${end_val:,.0f}  "
          f"Return: {(end_val/start_val-1)*100:.2f}%")