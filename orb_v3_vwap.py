"""
orb_v3_vwap.py — V3: VWAP-filtered 15-min ORB  (rewrite v3 — fixed)
====================================================================

WHY THIS REWRITE
----------------
The previous v3 "made only 1 trade in 3 years." After tracing through the
code bar-by-bar against the docstring spec, the root cause is the SIZER,
not the signal logic. The signal itself fires often (a 15-min ORB break
above the range while close > VWAP is a very common NQ event).

Root cause
~~~~~~~~~~
The old code delegated sizing to the external `FixedFractional` sizer by
calling `self.buy()` with no size and shoving a `self.risk_pts` magic
attribute on the strategy. That sizer turns risk_pts into a contract
count but does NOT cross-check against available margin. On NQ at
~$17,600 margin per contract with a $100k account:

  * On TIGHT range days (5–10 pts) the previous attempt to "cap risk_pts
    at hard_stop_pts" did nothing — actual_distance was already smaller
    than the cap — so risk_per_contract was tiny and the sizer asked for
    10+ contracts. Margin required >> cash → REJECTED.
  * On WIDE range days (>30 pts) the *original* file was using
    hard_stop_pts as a range-width FILTER, skipping the day entirely
    (BUG 1 in the old header). The "fix" left a different bug behind:
    the sizer still saw the capped points figure but the broker still
    placed the stop at the raw range edge, so dollar risk was 2× what
    the sizer thought — fine on a win, blew through margin on losing
    streaks.

Every margin reject set `_trade_taken = True` (correct — same-bar retry
would just reject again) and the day was dead. Result: across ~750
trading days almost every day rejected → 1–2 trades total.

Fix
~~~
Compute size INSIDE the strategy with BOTH a risk cap AND a margin cap,
then call `self.buy(size=N)` / `self.sell(size=N)` explicitly. Passing
an explicit size bypasses the (still-attached, harmless) FixedFractional
sizer entirely.

    risk_per_contract = capped_risk_pts × point_value
    size_risk         = floor(equity × risk_pct / risk_per_contract)
    size_margin       = floor(equity × max_margin_pct / margin_per_ct)
    size              = max(0, min(size_risk, size_margin))

With $100k equity, 1% risk, 25-pt cap, $20/pt, $17,600 margin, 50% max:
    size_risk   = floor(1000 / 500)    = 2
    size_margin = floor(50000 / 17600) = 2
    size                               = 2 contracts ✓ — never rejected.

Other fixes carried in
~~~~~~~~~~~~~~~~~~~~~~
  B. Stale-position guard at 09:30 uses `self.position.size` (the broker
     truth) instead of an internal `_in_position` flag that could drift.
     `_in_position` is removed entirely.
  C. When T1 fills, the full-size stop is ALWAYS cancelled — even on
     1-lot trades where remainder == 0 (the old code returned early and
     left a phantom stop live → could open a short after exit).
  D. Margin/Reject on the ENTRY no longer kills the day permanently; the
     size guard now prevents margin rejects in the first place, but if
     one ever slips through, the day frees up so the next bar can retry
     with a (by then) different risk profile.
  E. Diagnostic counters (signals seen, sized-out skips, trades taken,
     rejects) print at strategy stop so you can verify health quickly.

Drop-in: replace your old orb_v3_vwap.py with this file. orb_common.py
is still used for NQData, RTH_VWAP, make_cerebro, print_results.

Spec (unchanged):
  - Opening range: 09:30–09:44 ET inclusive
  - Long  if close > range_high AND close > VWAP
  - Short if close < range_low  AND close < VWAP
  - Stop at opposite range edge ± 1 tick (risk-points capped at hard_stop_pts)
  - T1 = fill + 1.5 × range_width (half position exits)
  - Remainder: BE stop at range edge + VWAP-cross trail
  - No new entries after 11:30 ET, force-flat at 15:45 ET
  - 1 trade/day max
"""

import os
import sys
import datetime
import backtrader as bt

from orb_common import NQData, RTH_VWAP, make_cerebro, print_results

DATA_DIR = os.path.join(os.path.dirname(__file__), "data_clean")


class ORB_V3_VWAP(bt.Strategy):

    params = (
        # ── spec params ─────────────────────────────────────────────
        ("range_window_min",    15),     # 09:30 → 09:44 inclusive
        ("hard_stop_pts",       25),     # CAP on stop distance (points)
        ("target1_mult",        1.5),    # T1 = fill ± range_width × mult
        ("cutoff_hour",         11),
        ("cutoff_min",          30),
        ("close_hour",          15),
        ("close_min",           45),
        ("rth_start_hour",       9),
        ("rth_start_min",       30),
        ("tick_size",           0.25),
        # ── sizing params (in-strategy; bypasses FixedFractional) ───
        ("point_value",         20.0),   # NQ=$20/pt, MNQ=$2/pt
        ("risk_pct",            0.01),   # 1% of equity per trade
        ("margin_per_contract", 17600),  # NQ ~ $17.6k; tune to your broker
        ("max_margin_pct",      0.50),   # ≤50% of equity in margin
        ("min_risk_pts",        2.0),    # never divide by ~0 for tiny ranges
        ("verbose",             True),
    )

    # ── init ────────────────────────────────────────────────────────

    def __init__(self):
        self.d = self.datas[0]
        self.vwap = RTH_VWAP(
            self.d,
            rth_start_hour=self.p.rth_start_hour,
            rth_start_minute=self.p.rth_start_min,
        )
        # diagnostics
        self._n_signals_seen    = 0
        self._n_sized_out       = 0
        self._n_entries_sent    = 0
        self._n_entries_filled  = 0
        self._n_margin_rejects  = 0
        self._n_days_seen       = 0
        self._last_seen_date    = None
        self._reset_daily_state()

    # ── per-day state ──────────────────────────────────────────────

    def _reset_daily_state(self):
        # range
        self._range_high       = None
        self._range_low        = None
        self._range_width      = None
        self._range_built      = False
        # one-trade-per-day lock
        self._trade_taken      = False
        self._direction        = None
        # planned exit prices (set at signal, applied on fill)
        self._planned_stop_px  = None
        self._planned_target_offset = 0.0
        self._planned_be_px    = None
        # order references
        self._entry_order      = None
        self._stop_order       = None
        self._target_order     = None
        # fill bookkeeping for partials
        self._initial_size     = 0
        self._half_size        = 0
        self._t1_hit           = False

    # ── time helpers ───────────────────────────────────────────────

    def _now(self):       return self.d.datetime.datetime(0)
    def _t(self):         return self._now().time()
    def _rth_start(self): return datetime.time(self.p.rth_start_hour, self.p.rth_start_min)
    def _cutoff(self):    return datetime.time(self.p.cutoff_hour, self.p.cutoff_min)
    def _force_close(self): return datetime.time(self.p.close_hour, self.p.close_min)

    def _range_end(self):
        """Last bar INCLUDED in the opening range (09:30 + window-1 minutes)."""
        base = datetime.datetime.combine(datetime.date.today(), self._rth_start())
        return (base + datetime.timedelta(minutes=self.p.range_window_min - 1)).time()

    # ── order helpers ──────────────────────────────────────────────

    def _safe_cancel(self, order):
        if order is None:
            return
        if order.status in (order.Submitted, order.Accepted, order.Partial):
            self.cancel(order)

    def _cancel_all_exits(self):
        self._safe_cancel(self._stop_order)
        self._safe_cancel(self._target_order)
        self._stop_order  = None
        self._target_order = None

    # ── position sizing (the fix) ──────────────────────────────────

    def _compute_size(self, risk_pts):
        """
        Risk-and-margin-aware contract count.

        Bypasses the external FixedFractional sizer; we pass the result
        as `size=` to self.buy()/self.sell(), which short-circuits the
        sizer in Backtrader.
        """
        equity = self.broker.getvalue()
        risk_pts_eff = max(risk_pts, self.p.min_risk_pts)

        risk_per_contract_dollars = risk_pts_eff * self.p.point_value
        risk_budget_dollars       = equity * self.p.risk_pct
        size_risk = int(risk_budget_dollars // risk_per_contract_dollars)

        if self.p.margin_per_contract > 0:
            max_margin_dollars = equity * self.p.max_margin_pct
            size_margin = int(max_margin_dollars // self.p.margin_per_contract)
        else:
            size_margin = 10**6

        return max(0, min(size_risk, size_margin))

    # ── main bar loop ─────────────────────────────────────────────

    def next(self):
        t     = self._t()
        close = self.d.close[0]
        high  = self.d.high[0]
        low   = self.d.low[0]
        vwap  = self.vwap.vwap[0]
        tick  = self.p.tick_size

        # day counter
        cur_date = self._now().date()
        if cur_date != self._last_seen_date:
            self._n_days_seen += 1
            self._last_seen_date = cur_date

        # ── A. Daily rollover at 09:30 ─────────────────────────────
        # Trust the broker, not an internal flag. Close anything that
        # somehow survived overnight, then reset state.
        if t == self._rth_start():
            if self.position.size != 0:
                self._cancel_all_exits()
                self.close()
            else:
                self._safe_cancel(self._entry_order)
            self._reset_daily_state()

        # ── B. Force-close at 15:45 ────────────────────────────────
        if t >= self._force_close() and self.position.size != 0:
            self._cancel_all_exits()
            self.close()
            if self.p.verbose:
                print(f"  [V3] {self._now()}  Force-close {t}")
            return

        # ── C. VWAP-cross trailing exit (only after T1 hit) ────────
        if self.position.size != 0 and self._t1_hit:
            cross = ((self._direction == "long"  and close < vwap) or
                     (self._direction == "short" and close > vwap))
            if cross:
                self._cancel_all_exits()
                self.close()
                if self.p.verbose:
                    print(f"  [V3] {self._now()}  VWAP-trail EXIT "
                          f"{self._direction.upper()}  close={close:.2f}  vwap={vwap:.2f}")
                return

        # ── D. one trade per day ───────────────────────────────────
        if self._trade_taken:
            return

        # ── E. Build opening range 09:30..range_end ────────────────
        if self._rth_start() <= t <= self._range_end():
            if self._range_high is None:
                self._range_high, self._range_low = high, low
            else:
                self._range_high = max(self._range_high, high)
                self._range_low  = min(self._range_low,  low)

            if t == self._range_end():
                self._range_width = self._range_high - self._range_low
                self._range_built = True
                if self.p.verbose:
                    print(f"  [V3] {self._now()}  Range "
                          f"{self._range_low:.2f}–{self._range_high:.2f}  "
                          f"w={self._range_width:.2f}")
            return

        # ── F. Post-range, pre-cutoff: scan for breakout ───────────
        if not self._range_built:
            return
        if t >= self._cutoff():
            return

        self._check_breakout(close, vwap, tick)

    # ── breakout signal ───────────────────────────────────────────

    def _check_breakout(self, close, vwap, tick):
        rng_h = self._range_high
        rng_l = self._range_low
        cap   = self.p.hard_stop_pts

        if close > rng_h and close > vwap:
            raw_stop    = rng_l - tick
            raw_dist    = close - raw_stop
            capped_dist = min(raw_dist, cap)
            # If raw_dist > cap, pull the stop up so actual risk matches
            # what the sizer was told (no more 2× hidden risk).
            actual_stop = close - capped_dist if raw_dist > cap else raw_stop
            self._submit_entry("long", close, actual_stop, capped_dist)

        elif close < rng_l and close < vwap:
            raw_stop    = rng_h + tick
            raw_dist    = raw_stop - close
            capped_dist = min(raw_dist, cap)
            actual_stop = close + capped_dist if raw_dist > cap else raw_stop
            self._submit_entry("short", close, actual_stop, capped_dist)

    def _submit_entry(self, direction, close, stop_px, risk_pts):
        self._n_signals_seen += 1
        size = self._compute_size(risk_pts)

        if size < 1:
            # Don't lock the day — next bar may have a slightly different
            # capped_dist (only matters for raw_dist near the cap boundary).
            self._n_sized_out += 1
            if self.p.verbose:
                print(f"  [V3] {self._now()}  {direction.upper()} skip — "
                      f"sized=0  risk_pts={risk_pts:.2f}  "
                      f"equity=${self.broker.getvalue():,.0f}")
            return

        rw = self._range_width
        self._direction        = direction
        self._planned_stop_px  = stop_px
        self._planned_target_offset = (+rw if direction == "long" else -rw) * self.p.target1_mult
        self._planned_be_px    = self._range_high if direction == "long" else self._range_low
        self._initial_size     = size

        if direction == "long":
            self._entry_order = self.buy(size=size)
        else:
            self._entry_order = self.sell(size=size)

        self._trade_taken     = True
        self._n_entries_sent += 1

        if self.p.verbose:
            print(f"  [V3] {self._now()}  {direction.upper()} signal  "
                  f"close={close:.2f}  stop={stop_px:.2f}  "
                  f"risk_pts={risk_pts:.2f}  size={size}  "
                  f"range={self._range_low:.2f}–{self._range_high:.2f}")

    # ── notify_order ──────────────────────────────────────────────

    def notify_order(self, order):
        if order.status in (order.Submitted, order.Accepted):
            return

        dt = self._now()

        if order.status in (order.Margin, order.Rejected):
            self._n_margin_rejects += 1
            if self.p.verbose:
                print(f"  [V3] {dt}  MARGIN/REJECTED  "
                      f"val=${self.broker.getvalue():,.0f}")
            # Free up the day if it was the entry that rejected — our
            # size guard should make this unreachable, but be defensive.
            if order is self._entry_order:
                self._entry_order = None
                self._trade_taken = False
            elif order is self._stop_order:
                self._stop_order = None
            elif order is self._target_order:
                self._target_order = None
            return

        if order.status == order.Canceled:
            return

        if order.status != order.Completed:
            return

        # ── Entry filled ──────────────────────────────────────────
        if order is self._entry_order:
            fill = order.executed.price
            size = abs(order.executed.size)
            self._n_entries_filled += 1
            self._initial_size     = size
            self._half_size        = max(1, size // 2)

            target_px = fill + self._planned_target_offset
            stop_px   = self._planned_stop_px

            if self._direction == "long":
                self._stop_order = self.sell(
                    size=size, exectype=bt.Order.Stop,  price=stop_px)
                self._target_order = self.sell(
                    size=self._half_size, exectype=bt.Order.Limit, price=target_px)
            else:
                self._stop_order = self.buy(
                    size=size, exectype=bt.Order.Stop,  price=stop_px)
                self._target_order = self.buy(
                    size=self._half_size, exectype=bt.Order.Limit, price=target_px)

            if self.p.verbose:
                print(f"  [V3] {dt}  FILLED {self._direction.upper()}  "
                      f"fill={fill:.2f}  stop={stop_px:.2f}  t1={target_px:.2f}  "
                      f"size={size}  half={self._half_size}")
            return

        # ── T1 filled ─────────────────────────────────────────────
        if order is self._target_order:
            self._t1_hit = True
            remainder = self._initial_size - self._half_size

            # ALWAYS cancel the (full-size) stop. The old code skipped this
            # when remainder == 0 (1-lot trade) and left a phantom stop live.
            self._safe_cancel(self._stop_order)
            self._stop_order = None

            if remainder > 0:
                be = self._planned_be_px
                if self._direction == "long":
                    self._stop_order = self.sell(
                        size=remainder, exectype=bt.Order.Stop, price=be)
                else:
                    self._stop_order = self.buy(
                        size=remainder, exectype=bt.Order.Stop, price=be)
                if self.p.verbose:
                    print(f"  [V3] {dt}  T1 HIT  fill={order.executed.price:.2f}  "
                          f"BE_stop={be:.2f}  remainder={remainder}")
            else:
                if self.p.verbose:
                    print(f"  [V3] {dt}  T1 HIT  fill={order.executed.price:.2f}  "
                          f"position fully closed (1-lot)")
            return

        # ── Stop filled ───────────────────────────────────────────
        if order is self._stop_order:
            if self.p.verbose:
                print(f"  [V3] {dt}  STOP filled  fill={order.executed.price:.2f}")
            self._stop_order = None
            return

    # ── notify_trade ──────────────────────────────────────────────

    def notify_trade(self, trade):
        if not trade.isclosed:
            return
        if self.p.verbose:
            print(f"  [V3] {self._now()}  Trade closed  "
                  f"pnl={trade.pnl:.2f}  net={trade.pnlcomm:.2f}")

        # Only finalise per-trade state when the BROKER says we're flat.
        if self.position.size == 0:
            self._t1_hit = False
            self._half_size = 0
            # tidy up any stray references; do not cancel — that's handled
            # at the exit path / next day's rollover.
            self._stop_order   = None
            self._target_order = None

    # ── stop diagnostics ──────────────────────────────────────────

    def stop(self):
        print("\n[V3] === diagnostics ===")
        print(f"  trading days seen   : {self._n_days_seen}")
        print(f"  breakout signals    : {self._n_signals_seen}")
        print(f"  sized-out skips     : {self._n_sized_out}")
        print(f"  entries submitted   : {self._n_entries_sent}")
        print(f"  entries filled      : {self._n_entries_filled}")
        print(f"  margin/rejected     : {self._n_margin_rejects}")
        print(f"  final equity        : ${self.broker.getvalue():,.2f}")


# ── STANDALONE RUN ────────────────────────────────────────────────

if __name__ == "__main__":
    csv = os.path.join(DATA_DIR, "NQ_1min_rth.csv")
    if not os.path.exists(csv):
        sys.exit(f"ERROR: {csv} not found.")

    cerebro = make_cerebro(csv, cash=100_000, risk_pct=0.01)
    cerebro.addstrategy(ORB_V3_VWAP, verbose=True)

    print("Running V3 VWAP-filtered 15-min ORB (fixed sizing) ...")
    start_val = cerebro.broker.getvalue()
    results   = cerebro.run()
    end_val   = cerebro.broker.getvalue()

    print_results(results[0], label="V3 VWAP")
    print(f"  Start: ${start_val:,.0f}  End: ${end_val:,.0f}  "
          f"Return: {(end_val/start_val-1)*100:.2f}%")
