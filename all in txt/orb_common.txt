"""
orb_common.py — shared utilities for all ORB strategies
=========================================================
  - NQData          : GenericCSVData loader for our cleaned CSVs
  - RTH_VWAP        : indicator — resets daily at 09:30, runs on 1-min bars
  - FixedFractional : sizer — risk X% of portfolio per trade
  - make_cerebro()  : convenience factory
"""

import backtrader as bt
import pandas as pd
import datetime


# ── DATA FEED ──────────────────────────────────────────────────────────────────

class NQData(bt.feeds.GenericCSVData):
    """
    Loads the cleaned CSVs produced by step0_data_prep.py.
    Format: datetime,open,high,low,close,volume
    Datetime string: YYYY-MM-DD HH:MM:SS  (no tz suffix — BT wants naive)
    """
    params = (
        ("dtformat",  "%Y-%m-%d %H:%M:%S"),
        ("datetime",  0),
        ("open",      1),
        ("high",      2),
        ("low",       3),
        ("close",     4),
        ("volume",    5),
        ("openinterest", -1),    # not present — tell BT to ignore
        ("timeframe", bt.TimeFrame.Minutes),
        ("compression", 1),
    )


# ── RTH VWAP INDICATOR ────────────────────────────────────────────────────────

class RTH_VWAP(bt.Indicator):
    """
    RTH VWAP — resets every day at 09:30 ET.

    Computes: cumsum(typical_price × volume) / cumsum(volume)
    where typical_price = (high + low + close) / 3

    Runs on 1-min bars.  Attach to the 1-min data feed.
    """
    lines  = ("vwap",)
    params = (
        ("rth_start_hour",   9),
        ("rth_start_minute", 30),
    )

    def __init__(self):
        self._cum_tpv = 0.0   # cumulative typical_price × volume
        self._cum_vol = 0.0   # cumulative volume
        self._last_date = None

    def next(self):
        bar_dt   = self.data.datetime.datetime(0)
        bar_date = bar_dt.date()
        bar_time = bar_dt.time()
        rth_start = datetime.time(
            self.p.rth_start_hour,
            self.p.rth_start_minute
        )

        # Reset accumulators at the first bar of each RTH session
        if bar_date != self._last_date and bar_time == rth_start:
            self._cum_tpv  = 0.0
            self._cum_vol  = 0.0
            self._last_date = bar_date

        tp  = (self.data.high[0] + self.data.low[0] + self.data.close[0]) / 3.0
        vol = self.data.volume[0]

        self._cum_tpv += tp * vol
        self._cum_vol += vol

        if self._cum_vol > 0:
            self.lines.vwap[0] = self._cum_tpv / self._cum_vol
        else:
            self.lines.vwap[0] = self.data.close[0]   # fallback: use close


# ── FIXED-FRACTIONAL SIZER ────────────────────────────────────────────────────

class FixedFractionalSizer(bt.Sizer):
    """
    Sizes each trade so the stop-loss risk = risk_pct % of current portfolio.

    Requires the strategy to set  self.risk_pts  (float, points at risk)
    BEFORE calling  self.buy() / self.sell().

    NQ contract value: $20 per point  (1 pt = 4 ticks × $5/tick)
    MNQ contract value: $2 per point  (use instrument_multiplier=2 for MNQ)
    """
    params = (
        ("risk_pct",              0.01),    # 1% default; override per run
        ("instrument_multiplier", 20),      # $20/pt for NQ
        ("min_contracts",         1),
    )

    def _getsizing(self, comminfo, cash, data, isbuy):
        portfolio_value = self.broker.getvalue()
        risk_dollars    = portfolio_value * self.p.risk_pct

        # strategy must set self.strategy.risk_pts before order
        risk_pts = getattr(self.strategy, "risk_pts", None)
        if not risk_pts or risk_pts <= 0:
            return self.p.min_contracts

        risk_per_contract = risk_pts * self.p.instrument_multiplier
        contracts = int(risk_dollars / risk_per_contract)
        return max(contracts, self.p.min_contracts)


# ── CEREBRO FACTORY ───────────────────────────────────────────────────────────

def make_cerebro(
    csv_path: str,
    cash:            float = 100_000.0,
    risk_pct:        float = 0.01,
    commission_per_contract: float = 2.05,   # NQ round-trip ~ $4.10; one-way ~$2.05
    slippage_pts:    float = 0.25,           # 1 tick slippage each way
):
    """
    Returns a configured Cerebro instance with:
      - NQData loaded from csv_path
      - FixedFractionalSizer at risk_pct
      - Realistic commission + slippage
    """
    cerebro = bt.Cerebro(stdstats=False)

    data = NQData(dataname=csv_path)
    cerebro.adddata(data, name="NQ_1min")

    cerebro.broker.setcash(cash)

    cerebro.broker.setcommission(
        commission=commission_per_contract,
        commtype=bt.CommInfoBase.COMM_FIXED,
        mult=20.0,            # NQ point multiplier
        margin=17_600.0,      # approx CME NQ intraday margin (adjust if needed)
    )

    # Slippage: 1 tick (0.25 pt) each way
    cerebro.broker.set_slippage_fixed(
        slippage_pts,
        slip_open=True,
        slip_limit=True,
        slip_match=True,
    )

    cerebro.addsizer(FixedFractionalSizer, risk_pct=risk_pct)

    # Standard analyzers — used by all strategies
    cerebro.addanalyzer(bt.analyzers.SharpeRatio,
                        _name="sharpe",
                        timeframe=bt.TimeFrame.Days,
                        annualize=True,
                        riskfreerate=0.05)
    cerebro.addanalyzer(bt.analyzers.DrawDown,      _name="drawdown")
    cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name="trades")
    cerebro.addanalyzer(bt.analyzers.Returns,       _name="returns",
                        timeframe=bt.TimeFrame.Days)

    return cerebro


def print_results(strategy, label: str = ""):
    """Pretty-print analyzer output after cerebro.run()."""
    s  = strategy
    sh = s.analyzers.sharpe.get_analysis()
    dd = s.analyzers.drawdown.get_analysis()
    tr = s.analyzers.trades.get_analysis()

    total  = tr.get("total",   {}).get("total",  0)
    won    = tr.get("won",     {}).get("total",  0)
    lost   = tr.get("lost",    {}).get("total",  0)
    pnl_net = tr.get("pnl",   {}).get("net",    {}).get("total", 0.0)

    win_rate = (won / total * 100) if total > 0 else 0.0
    sharpe   = sh.get("sharperatio", None)
    max_dd   = dd.get("max", {}).get("drawdown", 0.0)
    max_dd_m = dd.get("max", {}).get("moneydown", 0.0)

    tag = f"[{label}] " if label else ""
    print(f"\n{'='*55}")
    print(f"{tag}RESULTS")
    print(f"  Trades      : {total}  (won {won} / lost {lost})")
    print(f"  Win rate    : {win_rate:.1f}%")
    print(f"  Net P&L     : ${pnl_net:,.0f}")
    print(f"  Sharpe      : {sharpe:.3f}" if sharpe else "  Sharpe      : n/a")
    print(f"  Max DD      : {max_dd:.2f}%  (${max_dd_m:,.0f})")
    print(f"{'='*55}")
