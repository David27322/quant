import sys, csv, math
from datetime import time
from statistics import mean, pstdev
import backtrader as bt


# ==========================================================
# DATA FEED
# ==========================================================

class DukasCSV(bt.feeds.GenericCSVData):
    params = (
        ('dtformat',     '%Y-%m-%d %H:%M'),
        ('datetime',      0),
        ('open',          1),
        ('high',          2),
        ('low',           3),
        ('close',         4),
        ('volume',       -1),
        ('openinterest', -1),
        ('timeframe',    bt.TimeFrame.Minutes),
        ('compression',  1),
    )


# ==========================================================
# STRATEGY
# ==========================================================

class FirstHourMomentum(bt.Strategy):

    params = dict(
        stop_pts      = 40.0,
        target_r      = 2.0,
        contracts     = 4,        # Balanced dial
        point_value   = 2.0,      # MNQ $/pt
        comm_per_side = 1.5,      # $/contract/side
        slip_pts      = 0.5,      # pts per side
    )

    def __init__(self):
        self.cur_date          = None
        self.rth_open          = None
        self.daily_done        = False
        self.entry_pending_dir = 0

        self.in_pos            = False
        self.dir               = 0

        self.entry_price       = None
        self.entry_dt          = None
        self.stop_price        = None
        self.target_price      = None

        self.trades            = []

    # ------------------------------------------------------
    # HELPERS
    # ------------------------------------------------------

    def _reset_day(self, d):
        self.cur_date          = d
        self.rth_open          = None
        self.daily_done        = False
        self.entry_pending_dir = 0

    def _open(self, direction, raw_price, dt):
        self.in_pos      = True
        self.dir         = direction
        self.entry_price = raw_price + direction * self.p.slip_pts   # adverse slip

        if direction > 0:
            self.stop_price   = self.entry_price - self.p.stop_pts
            self.target_price = self.entry_price + self.p.stop_pts * self.p.target_r
        else:
            self.stop_price   = self.entry_price + self.p.stop_pts
            self.target_price = self.entry_price - self.p.stop_pts * self.p.target_r

        self.entry_dt = dt

    def _close_pos(self, reason, raw_price, dt):

        if not self.in_pos:
            return

        exit_price = (
            raw_price
            if reason == 'target'
            else raw_price - self.dir * self.p.slip_pts     # adverse slip
        )

        pts   = self.dir * (exit_price - self.entry_price)
        gross = pts * self.p.point_value * self.p.contracts
        comm  = 2 * self.p.comm_per_side * self.p.contracts   # round-trip

        self.trades.append({
            'date'     : self.cur_date.isoformat(),
            'dir'      : 'L' if self.dir > 0 else 'S',
            'entry_dt' : self.entry_dt.strftime('%H:%M'),
            'exit_dt'  : dt.strftime('%H:%M'),
            'entry'    : round(self.entry_price, 2),
            'exit'     : round(exit_price, 2),
            'pts'      : round(pts, 2),
            'R'        : round(pts / self.p.stop_pts, 3),
            'gross_$'  : round(gross, 2),
            'comm_$'   : round(comm, 2),
            'net_$'    : round(gross - comm, 2),
            'reason'   : reason,
        })

        self.in_pos = False
        self.dir = 0
        self.entry_price = self.stop_price = self.target_price = None

    # ------------------------------------------------------
    # MAIN LOOP
    # ------------------------------------------------------

    def next(self):

        dt   = self.data.datetime.datetime(0)
        d, t = dt.date(), dt.time()

        # New day
        if d != self.cur_date:

            if self.in_pos:  # data gap safety
                self._close_pos('day_rollover', self.data.open[0], dt)

            self._reset_day(d)

        # 09:30 -> record RTH open
        if t == time(9, 30) and self.rth_open is None:
            self.rth_open = self.data.open[0]

        # Deferred entry fill (bar after 10:30)
        if self.entry_pending_dir != 0 and not self.in_pos:
            self._open(self.entry_pending_dir, self.data.open[0], dt)
            self.entry_pending_dir = 0

        # Manage open position
        # (intrabar stop/target — pessimistic: stop first)
        if self.in_pos:

            hi, lo = self.data.high[0], self.data.low[0]

            if self.dir > 0:
                if lo <= self.stop_price:
                    self._close_pos('stop', self.stop_price, dt)
                elif hi >= self.target_price:
                    self._close_pos('target', self.target_price, dt)
            else:
                if hi >= self.stop_price:
                    self._close_pos('stop', self.stop_price, dt)
                elif lo <= self.target_price:
                    self._close_pos('target', self.target_price, dt)

        # 15:55 -> force flat at this bar's close
        if self.in_pos and t >= time(15, 55):
            self._close_pos('eod', self.data.close[0], dt)

        # 10:30 -> compute signal, defer entry to next bar
        if (
            t == time(10, 30)
            and self.rth_open is not None
            and not self.daily_done
            and not self.in_pos
        ):

            c = self.data.close[0]

            if c > self.rth_open:
                self.entry_pending_dir = 1
                self.daily_done = True

            elif c < self.rth_open:
                self.entry_pending_dir = -1
                self.daily_done = True


# ==========================================================
# REPORTING
# ==========================================================

def report(strat, starting_cash=50_000.0):

    tr = strat.trades
    n  = len(tr)

    if n == 0:
        print("No trades.")
        return

    wins  = [x for x in tr if x['net_$'] > 0]
    loses = [x for x in tr if x['net_$'] <= 0]

    total_pts = sum(x['pts']   for x in tr)
    total_R   = sum(x['R']     for x in tr)
    total_d   = sum(x['net_$'] for x in tr)

    win_rate = 100 * len(wins) / n

    avg_R   = total_R / n
    avg_w_R = (sum(x['R'] for x in wins)  / len(wins))  if wins  else 0
    avg_l_R = (sum(x['R'] for x in loses) / len(loses)) if loses else 0

    pf = (
        sum(x['net_$'] for x in wins)
        / abs(sum(x['net_$'] for x in loses))
    ) if loses else float('inf')

    # Equity curve & max DD
    eq = [starting_cash]

    for x in tr:
        eq.append(eq[-1] + x['net_$'])

    peak, mdd = eq[0], 0.0

    for v in eq:
        peak = max(peak, v)
        mdd  = max(mdd, peak - v)

    # Daily Sharpe (annualised, rf=0)
    by_day = {}

    for x in tr:
        by_day[x['date']] = by_day.get(x['date'], 0.0) + x['net_$']

    daily = [v / starting_cash for v in by_day.values()]

    sharpe = (
        mean(daily) / pstdev(daily) * math.sqrt(252)
        if len(daily) > 1 and pstdev(daily) > 0
        else float('nan')
    )

    print("\n=========== First-Hour Momentum — OOS Backtest ===========")
    print(f"Trades              : {n}")
    print(f"Win rate            : {win_rate:5.1f}%")
    print(f"Total points        : {total_pts:+8.1f}")
    print(f"Total R             : {total_R:+8.2f}")
    print(f"Avg R / trade       : {avg_R:+8.2f}")
    print(f"Avg winner  (R)     : {avg_w_R:+8.2f}")
    print(f"Avg loser   (R)     : {avg_l_R:+8.2f}")
    print(f"Profit factor       : {pf:8.2f}")

    print(f"---  $ at 4x MNQ ($2/pt), {starting_cash:,.0f} start  ---")
    print(f"Net P&L             : ${total_d:+,.0f}")
    print(f"Final equity        : ${eq[-1]:,.0f}")
    print(f"Max drawdown ($)    : ${mdd:,.0f}")
    print(f"Max DD (% of start) : {100 * mdd / starting_cash:5.1f}%")
    print(f"Daily Sharpe (ann.) : {sharpe:8.2f}")

    print("Exit reason breakdown:")

    for r in ('target', 'stop', 'eod', 'day_rollover'):
        c = sum(1 for x in tr if x['reason'] == r)

        if c:
            print(f"    {r:14s}: {c:4d}  ({100*c/n:4.1f}%)")

    print("==========================================================\n")

    with open('trades.csv', 'w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=list(tr[0].keys()))
        w.writeheader()
        w.writerows(tr)

    print("Per-trade log written to trades.csv")


# ==========================================================
# MAIN
# ==========================================================

def main():

    src = sys.argv[1] if len(sys.argv) > 1 else "usa100_rth_only.csv"

    print(f"Loading {src} ...")

    cerebro = bt.Cerebro(stdstats=False)

    cerebro.adddata(DukasCSV(dataname=src))
    cerebro.addstrategy(FirstHourMomentum)

    cerebro.broker.setcash(1_000_000)  # headroom; real accounting lives in strategy

    strats = cerebro.run()

    report(strats[0])


if __name__ == "__main__":
    main()