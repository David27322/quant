"""
orb_v1_classic.py — V1: Classic 30-min ORB  (Crabel / Kaufman TSM)
====================================================================
Spec:
  - RTH session; range window 09:30–10:00 (default 30 min, parametrised)
  - Entry: stop-buy 1 tick above range high, stop-sell 1 tick below range low
  - Orders placed at 10:00 ET; first fill wins, other cancelled
  - Stop  : opposite side of range + 1 tick
  - Target: 1x range width (R:R 1:1)
  - Cutoff: no new entries after 14:00 ET
  - Force-close: 15:45 ET
  - One trade per day; no re-entry

Run standalone:
    python orb_v1_classic.py
"""

import datetime
import backtrader as bt
from orb_common import NQData, FixedFractionalSizer, make_cerebro, print_results

import os, sys
DATA_DIR = os.path.join(os.path.dirname(__file__), "data_clean")


class ORB_V1_Classic(bt.Strategy):

    params = (
        ("range_window_min",    30),
        ("entry_offset_ticks",   1),
        ("target_mult",        1.0),
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
        self.data_1min = self.datas[0]
        self._reset_daily_state()
        self._long_order   = None
        self._short_order  = None
        self._stop_order   = None
        self._target_order = None
        self.risk_pts      = 0.0

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

    def _is_entry_order(self, order):
        """True if this order is one of the two resting entry stops."""
        return order in (self._long_order, self._short_order)

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
                print(f"  [V1] {self._bar_dt()}  Force-closed")
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

            self.risk_pts = self._range_width + offset

            long_entry  = self._range_high + offset
            short_entry = self._range_low  - offset

            self._long_order = self.buy(
                exectype=bt.Order.Stop, price=long_entry, transmit=True)
            # Attach the range snapshot to the order so notify_order
            # never depends on mutable strategy state.
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
                print(f"  [V1] {self._bar_dt()}  "
                      f"Range {self._range_low:.2f}-{self._range_high:.2f} "
                      f"width={self._range_width:.2f}  "
                      f"L@{long_entry:.2f} S@{short_entry:.2f}")

    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            return

        if order.status == order.Completed and self._is_entry_order(order):
            # Read range values from the order itself — immune to daily resets
            rw       = order.info.get("rw",       self._range_width or 0)
            rng_high = order.info.get("rng_high", self._range_high  or 0)
            rng_low  = order.info.get("rng_low",  self._range_low   or 0)

            if not rw:
                if self.p.verbose:
                    print(f"  [V1] {self._bar_dt()}  WARNING: rw=0 on fill, skipping exits")
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
                self._stop_order   = self.sell(size=size, exectype=bt.Order.Stop,
                                               price=stop_px, transmit=False)
                self._target_order = self.sell(size=size, exectype=bt.Order.Limit,
                                               price=target_px, transmit=True)
            else:
                self._direction = "short"
                stop_px   = rng_high + off
                target_px = entry - rw * self.p.target_mult
                if self._long_order:
                    self.cancel(self._long_order)
                    self._long_order = None
                self._stop_order   = self.buy(size=size, exectype=bt.Order.Stop,
                                              price=stop_px, transmit=False)
                self._target_order = self.buy(size=size, exectype=bt.Order.Limit,
                                              price=target_px, transmit=True)

            if self.p.verbose:
                print(f"  [V1] {self._bar_dt()}  FILLED {self._direction.upper()} "
                      f"entry={entry:.2f} stop={stop_px:.2f} "
                      f"target={target_px:.2f} size={size}")

    def notify_trade(self, trade):
        if trade.isclosed:
            self._in_position  = False
            self._stop_order   = None
            self._target_order = None
            if self.p.verbose:
                print(f"  [V1] {self._bar_dt()}  "
                      f"Closed pnl={trade.pnl:.2f} net={trade.pnlcomm:.2f}")


# ── STANDALONE RUN ────────────────────────────────────────────────────────────

if __name__ == "__main__":
    csv = os.path.join(DATA_DIR, "NQ_1min_rth.csv")
    if not os.path.exists(csv):
        sys.exit(f"ERROR: {csv} not found.")

    cerebro = make_cerebro(csv, cash=100_000, risk_pct=0.01)
    cerebro.addstrategy(ORB_V1_Classic, verbose=True)

    print("Running V1 Classic 30-min ORB ...")
    start_val = cerebro.broker.getvalue()
    results   = cerebro.run()
    end_val   = cerebro.broker.getvalue()

    print_results(results[0], label="V1 Classic")
    print(f"  Start: ${start_val:,.0f}  End: ${end_val:,.0f}  "
          f"Return: {(end_val/start_val-1)*100:.2f}%")