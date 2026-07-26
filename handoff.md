Closing out — here's your handoff. Everything below is already saved in **Phase 3.5 — Fast Funded Playbook** so you can pick up cold next session.

## ✅ Decided (locked)

- **ORB is dead** for this goal — proven on out-of-sample data with costs. Stop polishing it.
- **The edge: First-Hour Momentum.** At 10:30 ET, trade the direction of the first hour (long if up, short if down), **40pt stop, 2R target (80pt), flat 15:55, never overnight, one trade/day.**
- **Validated:** OOS Sharpe 1.42, positive every year 2023–25, beats always-long, shorts work in a down year (not bull-beta), survives no-look-ahead. It can both **pass** the eval and **sustain** funded money.
- **Setup:** Apex 50K EOD-trailing, MNQ/MES micros, broker-side OCO brackets (crash-proof, no VPS), semi-auto (tap-to-send on mobile), under-$50 entry via coupons.

## 📋 To do next session

1. **Pick the risk dial** (still open — your call below).
2. **Build the bot:** 10:30 signal → bracket ticket (entry next bar, 40pt stop, 2R) + fixed-$ micro sizer + one-trade/day + daily-loss lockout.
3. **Wire the phone alert** (Telegram/Discord/TradingView) that prints the day's ticket.
4. **Buy the eval** (coupon), connect Tradovate, then trade it live at 1 micro.

## 🎛️ On the bot + the options you saw

- **Safe (3 micros, ~$250 risk):** ~0% blow-up, ~11% pass/attempt. Near-bulletproof, slower.
- **Balanced (4 micros, ~$350 risk):** ~30% pass, ~20% blow-up, ~3 cheap evals (~$66) to fund.
- **More robustness / phone alerts** were optional add-ons — not blockers. The bot itself is the critical path.

## ⚠️ Crucial points going forward

- **The edge needs a profit target** — the "hold-to-close" version overfit and failed OOS. Keep the 2R target.
- **Micro-sizing is mandatory:** full-size drawdown runs ~$4–5k; only tiny size keeps you under the $2,500 limit.
- **40% win rate** — you *will* hit losing streaks. The bot must enforce the one-trade/day + daily lockout so discipline isn't a willpower problem.
- **Eval vs funded are different games:** passing is about surviving 30 days; on the funded account watch Apex's **30% consistency rule** (one big trend day can dominate payouts).
- **Known refinement for the bot:** enter on the *next* bar (already validated), and re-check slippage on fast stop-outs when you go live.
- **Don't re-open the strategy search.** It's validated. Next effort goes into *execution*, not another backtest.
- **Anti-FOMO:** until you're funded, ignore new strategies/indicators/papers. The playbook's ignore-list is your filter.

When you're back, just tell me **Safe or Balanced** and I'll build the bot. Good work today — you killed a false hope and found a real one.