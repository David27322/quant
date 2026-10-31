# Journey
# My Retail Quant Research Journey

### Phase 1 – Getting Started with Quantitative Trading

I started with the basics (Before, I had explored discretionary trading and learned about technical analysis). In Phase 1, I fetched five years of EUR/USD daily price data using `yfinance` and built my first custom trading strategy: a 10/50 Simple Moving Average (SMA) crossover.

I implemented the backtesting logic myself, calculated the performance metrics, and generated visualizations to understand how the strategy behaved. The initial results were encouraging. The strategy returned **+6.87%**, compared to **−8.50% for buy-and-hold** over the same period.

However, rather than simply accepting those results, I wanted to see how sensitive the strategy was to its parameters. So, I deliberately changed the moving averages from 10/50 to 5/20. This produced 39 trades and a return of **−0.74%**. It was a useful way to see how easily results could change with different parameter choices.

Finally, I divided the dataset into two separate periods: an In-Sample (IS) training period covering 2020–2024 and a sealed Out-of-Sample (OOS) testing period covering 2025–2026. The idea was to keep the OOS data untouched during strategy development and avoid using future information to influence the research.

### Phase 2 – RSI Mean Reversion and Statistical Testing

In Phase 2, I moved on to an RSI-based mean reversion strategy. I experimented with different parameters and eventually found that a **7-period RSI with 25/75 thresholds** produced the best results among the configurations I tested.

But I didn't want to rely on backtest profitability alone. I started looking into whether the observed results had any statistical significance. To investigate this, I implemented a Monte Carlo permutation test, checked the strategy's out-of-sample performance, introduced a fixed fractional position-sizing model, and conducted an expanding-window walk-forward analysis.

This phase exposed me to several important aspects of quantitative research, particularly the need to distinguish between a strategy that looks profitable in a backtest and one that has evidence of a genuine edge.

Eventually, I decided that the overall approach was still too basic and relied on too many assumptions to justify risking real money on it.

These first two phases were primarily learning exercises. Alongside the practical work, I was also studying quantitative finance and gradually learning the terminology, concepts, and mathematical foundations involved in finance and data science. A book that got me started is, "Quantitative Trading: How to build your own algorithmic trading business" (2nd ed., 2009) by Ernest P. Chan.

### Phase 3 – Moving to Futures and More Serious Strategy Research

Phase 3 was considerably larger. It eventually extended from Phase 3.0 through Phase 3.10.

I installed Backtrader as my backtesting framework and obtained a Kaggle NQ (Nasdaq-100 E-mini futures) dataset containing three years of cleaned one-minute data. The dataset consisted of approximately **1.05 million bars and 765 Regular Trading Hours (RTH) sessions**.

I started with three documented Opening Range Breakout (ORB) strategy variants and implemented them in Backtrader. I then conducted extensive parameter sweeps, testing anywhere from 50 to more than 200 parameter combinations. The results were subsequently filtered through bootstrap significance tests and a 70/30 walk-forward evaluation.

The results were quite interesting, but they also demonstrated why raw profitability isn't enough.

- **V1:** 763 trades and +92% return.
- **V4:** 748 trades and +222% return.
- Both strategies, however, suffered from approximately 60–67% drawdowns, making their results far too risky and unreliable to trust at that stage.
- **V3:** Essentially broken, producing only five trades and a 385% drawdown.

After the failure of ORB experiments, I moved on to another strategy: First-Hour Momentum (FHM). 

This involved another extensive round of backtesting, random-signal comparisons, year-by-year performance checks, and position-sizing experiments. I used Duckascopy to get cleaned 5.5 years of NDX100 1-min data. 

One encouraging observation was that every full year from 2021 through 2025 was profitable, and all five chronological folds I tested were positive as well. Importantly, I did not perform parameter optimization for this strategy.

However, the results weren't entirely convincing. The integrated robustness gate failed when using an assumed transaction cost of three points. At a lower assumed cost of two points, the strategy showed an expectancy of **+0.072R per trade** and a **Profit Factor of 1.12**.

The biggest concern was 2026. Its performance was negative, with a loss of **−14.75R**, even at the assumed two-point round-trip transaction cost.

Eventually, I paused the research for a few months.

### Phase 4 – Execution Engineering, Data Auditing and Reality Checks

By Phase 4, the project had grown considerably. I was now working with more than five years of minute-level data, approximately **552,092 price bars and 1,412 historical trades**.

At this point, the focus wasn't just on whether a strategy could make money in a backtest. I also needed to understand whether the underlying data, assumptions, and execution process were reliable.

I started auditing different aspects of the research, including trading-session timings, holidays, shortened trading days, price gaps, and alternative transaction-cost assumptions. One of the audits alone covered **453 simulation cases and approximately 3.08 million simulated paths**.

During this process, I discovered and corrected a serious 10× contract-value mistake. I also began developing the actual trading and logging code, worked through compilation issues, and audited order handling and restart safety.

I even tried a 14-day trial of the trading platform. Later, I successfully compiled the revised bot with **zero errors and zero warnings**. However, there was another problem: the free trial did not permit Expert Advisors (EAs).

This forced me to reconsider the execution approach, and the plan shifted towards manual execution.

I also realized that timing accuracy needed its own investigation. I checked the clocks and eventually examined more than **2.2 million paired BID/ASK quotes** to understand the available execution data.

However, these quotes were not synchronized execution or fill records. They could help examine market pricing and potential execution conditions, but they couldn't establish what actual fills would have looked like.

By the end of this phase, I had to confront the uncomfortable reality: the FHM strategy had a very thin edge, there was worrying evidence in the results, and its 2026 performance was terrible.

I decided to drop FHM for the time being.

### Phase 5 – Starting Over and Expanding the Research Process

In Phase 5, I started again with a more important question: **Could I actually find something worth risking real money on?**

What followed became a much larger research and engineering project.

I worked through at least **20 strategy trials**, exploring different market behaviours and trading ideas. These included opening breakouts, late-session momentum, opening-gap reversals, and month-end effects.

The data itself also needed more work. I audited approximately **5.5 years of minute-level data**, covering 534,450 price bars across 1,375 trading sessions. During the audit, I corrected holiday and early-close handling and removed **17,642 bars** that fell outside the intended trading hours.

I then expanded the testing process considerably.

Instead of relying on ordinary backtest results, I introduced more realistic transaction-cost modelling, doubled and tripled cost stress tests, thousands of reshuffled trading paths, delayed-entry scenarios, missed-trade simulations, noisy-price tests, and checks across different years and market conditions.

The objective was to understand how fragile each strategy was and whether its apparent edge could survive conditions that were less favourable than the original backtest.

But something else started bothering me. Almost everything I tested was getting rejected. At some point, I had to question whether the strategies were genuinely poor or whether my testing and selection process had become excessively demanding.

So, I started auditing the research process itself.

I ran more than **one million synthetic test cases**, specifically to investigate the selection mathematics and the effects of testing multiple strategies. The purpose wasn't to generate imaginary profits or manufacture a successful strategy. It was to understand whether the statistical filters were behaving as intended.

One particular setup detected genuinely planted edges in only **4.51% of simulated rounds**. That raised a serious concern: perhaps the testing process was rejecting too much, even when an edge was actually present.

Later, I also discovered a genuine arithmetic bug in the research code and corrected it. After the correction, **443 regression checks passed**, and I replayed **38,472 saved order and scenario records** to verify the results.

The correction changed 12 exit timings, but it didn't materially change the profitability results.

By this point, the amount of work completed was substantial. I had tested numerous strategies, investigated execution assumptions, audited the data, stress-tested the results, and even examined the correctness of the statistical selection process itself.

But the honest conclusion remained the same: despite all that work, **I still had no strategy that qualified for deployment.**

### Phase 6 – Questioning the Statistical Limits of the Entire Research Process

Phase 6 came from one observation that I couldn't ignore: a testing process that detected planted edges in only **4.51% of simulated rounds**.

I started wondering whether I was pursuing a level of statistical certainty that simply wasn't realistic in live financial markets, particularly with the amount of historical data available to me.

Instead of running yet another strategy trial, I decided to investigate the problem at a deeper level.

I engineered a synthetic meta-test covering more than **1,354 trading sessions**. The objective was to understand the statistical detection power of the strategy-selection process itself.

The results were quite revealing.

Even a simplified selector achieved only **5.5% detection power for sparse +0.10R net edges**. Furthermore, its detection power reached only **35.3% even when using 10 years of data**.

This changed how I viewed the entire project.

The bottleneck might not have been a lack of good strategy ideas or poor implementation. Instead, the available sample length and the statistical limitations of detecting small trading edges were becoming the dominant constraints.

In other words, I couldn't simply keep testing strategies until something passed every filter. With limited historical observations and a very small underlying edge, the research process could become so demanding that even genuine opportunities would rarely be detected.

This was the point where I had to stop the project.

Continuing to run more strategy trials under those conditions would no longer represent meaningful quantitative research. It would increasingly resemble gambling.

There was one final question I wanted to investigate before closing this direction.

I considered whether switching instruments could make a difference. In particular, I looked at EUR/USD again to see whether it offered any verified, material feasibility advantage over the NDX100/US100 CFD market.

However, screening EUR/USD did not demonstrate any such advantage.

So, changing the symbol wasn't a solution. The exhausted research budget and underlying statistical limitations didn't disappear simply because I switched markets.

<img width="1920" height="1200" alt="Image" src="https://github.com/user-attachments/assets/35cea96e-c6b0-4ba1-a760-7b8cc39a8cde" />
