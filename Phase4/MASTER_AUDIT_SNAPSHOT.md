# Phase 3–4 — Master audit and evidence archive

Offline snapshot of the Notion master audit, made 2026-11-03. Source links require access to Notion. For any later edits, consult the [live master audit](https://app.notion.com/p/cf9d5ac010d24c1abe6b15590fcac305).

## Start here — rechecked evidence

**Rechecked on November 3, 2026:** the earlier version missed two original audit ZIPs subsequently attached to PHASE4 and did not recover the full 2023 source file. All three have now been recovered and added to the consolidated package in section 11. The detailed additions and corrections are in section 10A; the outstanding gaps are in section 12. Historical results remain model outputs, not realized account returns.[\[1\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)

## Executive record

- **Current research status:** First-Hour Momentum (FHM) is a historically promising but fragile candidate, **parked for paid deployment**, not proven permanently dead. The paid-account recommendation and payout forecasts in the older Phase 4 plan were subsequently withdrawn. No paid evaluation, funded payout, or completed execution-calibration series is established in the recovered evidence.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)
- **The positive baseline and the negative recent sample both matter.** Reproducing the original model gives 1,412 trades and +136.19R at an assumed 1-point cost. The later execution audit found 124 trades in the available part of 2026, −14.75R at an assumed 2-point cost. These are backtest results, not actual returns.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)
- **The Phase 3 robustness gate failed:** at 3 assumed points per round trip, profit factor was 1.07, below the 1.10 threshold, although historical net R remained positive. Real all-in costs remain unmeasured.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)
- **Use this as an archive, not a trading instruction.** Older pages contain confident, superseded recommendations, contradictory rules, and sizing errors. Product rules, prices, eligibility, account specifications and testing permissions must be checked for the exact account and date before any action.

## 1. The story: what was attempted and why

### Objective and constraints

David’s aim was to build consistent wealth through trading and eventually compound and scale capital, not merely make a long-term investment. The initial budget was approximately \$50, with no regular monthly additions; one or two failures would matter. The plan needed to work from Nepal, use a legitimate affordable firm, and accommodate practical execution. He preferred automation and free hosting, but was open to manual entry, other firms and instruments. He later removed the suggested three-month pass deadline; retries were permissible only if the limited budget allowed them.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

### Phase 3: ORB to FHM

The original strategy-factory plan proposed cleaning NQ data, specifying ORB variants, coding and testing them, then using robustness and walk-forward checks before paper trading. A historical Phase 3.5 snapshot reported testing an ORB candidate on 764 RTH days from December 2022 to December 2025. Its fixed-stop redesign reportedly fell from 37% in-sample pass to 15% out-of-sample pass, with 67% OOS breach; the original range-width version had modeled drawdowns of roughly \$4.3k–\$6k against a \$2.5k limit. These are **old reported results**, not a newly reconstructed trade ledger. The tested ORB variants were parked; this does not prove every ORB strategy fails.[\[2\]](https://app.notion.com/chat?t=3f4a5d08f8f580ac9ce100a977eff2e0)

FHM then became the main candidate. David later clarified that he had only superficially tested a few ORB variants, took FHM directly from the internet, and did not optimize FHM parameters. The older playbook instead describes exploring returns in-sample and selecting a signal; the exact discovery/selection history and which periods were genuinely untouched are therefore **not independently reconciled**. Do not assume extensive FHM optimization, but do not claim a fully documented unbiased selection process either.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)[\[2\]](https://app.notion.com/chat?t=3f4a5d08f8f580ac9ce100a977eff2e0)

The original plan focused on Apex, MNQ and a semi-automatic bracket ticket. The project later pivoted to FundedNext’s US100/NDX100 CFD and MT5 because the originally proposed futures route did not fit the stated Nepal/budget constraints. Competition trading was a separate experimental branch that David had already discarded; it is preserved for history, not recommended as an active project.[\[3\]](https://app.notion.com/p/3f4a5d08f8f581b69b9aea11e7210908)[\[4\]](https://app.notion.com/p/3f4a5d08f8f581cbb3d8dfb982762707)

### Frozen FHM rules

- New York time: compare the 09:30 M1 opening price with the 10:30 M1 opening price; trade in the direction of the first-hour move; skip a tie.
- Original validator: enter at the next row’s open, intended to be 10:31; 40 index-point stop; 80-point target; at most one entry per day; force-flat near 15:55. Historical code monitored the 15:55 bar and used its close; the EA intended to close at the first quote at or after 15:55.
- **1R is the nominal 40-point stop distance**, not a guarantee of the actual loss. A server-side SL/TP does not itself guarantee the scheduled time exit or an exact stop fill.[\[5\]](https://app.notion.com/p/3f4a5d08f8f581aba92de8d9b918b5a6)[\[6\]](https://app.notion.com/p/3f4a5d08f8f5814b8dd9d5e39fead7d2)

## 2. Data and provenance

The attached `usa100_clean.csv` has **552,092** one-minute OHLC rows, 2021-01-04 09:30 through 2026-06-25 16:00, with no duplicate rows and no missing OHLC values on the current profile. The original download command specified Dukascopy `usatechidxusd`, BID, New York-formatted timestamps; the later audit treated timestamps as minute-start labels, an assumption not independently confirmed against ticks. This is not the FundedNext feed.[\[7\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

A prior reconstruction of the original 2023 source—UTC to New York, weekday/RTH filter, and whole-session-flat removal—matched all **100,096** master rows for that year exactly. The other five source-year files were not independently verified. The prior audit separately flagged **37 calendar-proxy dates** and **10 early-close dates**; excluding the 37 non-session proxy dates did not eliminate historical profitability. The calendar was not a fully verified Nasdaq archive, and the early-close dates were not excluded or silently assigned new exit rules. The master ends in June; attempted recent-data downloads failed and no post-June historical result was established.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

## 3. Original baseline: reproduced from the attached files

This section is a fresh reproduction of the **original** script, with an assumed 1-point additive round-trip cost, exact stop/target fills and the 15:55-close rule. The script’s per-trade Sharpe annualizes by √252. Results are historical model outputs; cost is not broker-calibrated. The separately generated ledger is in the evidence ZIP.

| Metric | Original baseline |
| --- | --- |
| Dates / trades | 2021-01-04 to 2026-06-25; 1,412 trades |
| Win rate | 39.09% |
| Total / mean | +136.1907R / +0.09645R per trade |
| PF / annualized Sharpe | 1.1596 / 1.0959 |
| Exit counts | 819 stop; 473 target; 120 end-of-day |
| Longs / shorts | 737 long, +79.4R; 675 short, +56.8R, as reported |
| Full years 2021–2025 | Each positive; 2026 is partial and negative |

**Return translation, not account performance:** at \$10/index point/lot and 0.02 lot, 1R = \$8 nominal. +136.1907R translates to about **\$1,089.53**, or **21.79% of an assumed \$5,000 initial balance over the whole sample**, using fixed size, no compounding and the model’s assumptions. It is not a realized account return, annual return or CAGR.

Original baseline yearly total net R; the final bar is a partial year, not comparable as a full-year return.

[Open the original annual chart](originals/year_notion_agent_chart.html)

| Year | Trades | Total net R | Mean R/trade |
| --- | --- | --- | --- |
| 2021 | 258 | +18.22 | +0.071 |
| 2022 | 258 | +16.22 | +0.063 |
| 2023 | 256 | +21.09 | +0.082 |
| 2024 | 259 | +41.36 | +0.160 |
| 2025 | 257 | +51.02 | +0.199 |
| 2026 through June 25 | 124 | −11.71 | −0.094 |

The sum of `net_pts / 40` was independently checked against the script’s total R. The annual chart and table use the same reproduced trade ledger. The original historical result includes dates that may not have been valid full cash sessions; no holiday exclusion was applied to this baseline.

## 4. Earlier results and contradictions

- The old Phase 3.5 playbook reported 2025 OOS profit of \$9,306 and Sharpe 1.42, an always-long control of −\$3,698, shorts +\$5,653, and a random signal of −\$4,051. It also reported annual figures of approximately +\$4.1k, +\$12.9k and +\$8.5k for 2023–25. These old figures use a different setup and cannot be directly merged with the later CFD baseline.[\[2\]](https://app.notion.com/chat?t=3f4a5d08f8f580ac9ce100a977eff2e0)
- Phase 3.6 reported a January 1–June 16, 2026 OOS test: 109 trades, 41.3% wins, +18.34R, +0.17R/trade, PF 1.22, Sharpe 1.43 and 7.3% max drawdown. It reported \$4,549 at four MNQ contracts, but 18.34R × \$320/R = \$5,868.80; the note does not explain the difference. This **positive 2026 report conflicts with the later negative 2026 audit**; the underlying trade ledgers and model differences are not reconciled. Neither number should be silently overwritten.[\[3\]](https://app.notion.com/p/3f4a5d08f8f581b69b9aea11e7210908)
- Phase 3.6 described both 3 micros as “safe” and later recommended 2 for a real Apex evaluation. Early “near-bulletproof,” “edge is real,” and “walk away” assurances were too strong. The alert bot does not itself route orders or enforce a scheduled close. Its Python, Pine and validator timing/price conventions are not demonstrably identical.[\[3\]](https://app.notion.com/p/3f4a5d08f8f581b69b9aea11e7210908)[\[2\]](https://app.notion.com/chat?t=3f4a5d08f8f580ac9ce100a977eff2e0)

## 5. The gates: what passed, failed, and changed

The user supplied the following historical output. Gate 1 passed the **revised** Sharpe floor of 1.00, full years 2021–25 positive, PF ≥1.15, and a random-direction control of approximately −0.7R ±46.3R compared with +136.2R. The prior 1.20 Sharpe requirement was lowered after the observed 1.10. Gate 2’s original requirement—Sharpe ≥1 in at least four of five folds—was changed to ≥4 positive folds, with an R-based catastrophic check. That change matters: only **1/5** folds had Sharpe ≥1, although **5/5** had positive total R.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)[\[5\]](https://app.notion.com/p/3f4a5d08f8f581aba92de8d9b918b5a6)

| Fold | Trades | Sharpe | Net R |
| --- | --- | --- | --- |
| 1 | 262 | 0.79 | +17.5 |
| 2 | 261 | 0.55 | +12.6 |
| 3 | 259 | 0.33 | +7.4 |
| 4 | 260 | 2.79 | +66.7 |
| 5 | 261 | 0.87 | +20.0 |

| Original cost scenario | Trades | Mean R | Total R | PF | Sharpe | Gate 1.5 |
| --- | --- | --- | --- | --- | --- | --- |
| 1 point | 1,412 | +0.096 | +136.2 | 1.16 | 1.10 | Pass |
| 2 points | 1,412 | +0.071 | +100.9 | 1.12 | 0.81 | Pass |
| 3 points | 1,412 | +0.046 | +65.6 | 1.07 | 0.53 | **Fail PF ≥1.10** |

Dropping 2024 at the 1-point assumption retained 1,153 trades, +94.8R, PF 1.14 and Sharpe 0.94. This is evidence against dependence solely on that year, not proof of a durable edge. The older printed Gate 3 gave 0.02/0.03 lot GO and pass estimates 0.94/0.93, but its final output did not include the subsequently failing Gate 1.5. The attached version does include it, so the integrated decision is **NO-GO under those criteria**. The old Monte Carlo used closed P&L rather than full intratrade equity, IID resampling, a 1,200-trade cap per phase, and five minimum days. Do not use its pass estimates as verified live odds.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

## 6. Phase 4 execution audit and cost limits

A separate prior audit preserved the baseline and tested the 15:55-open exit proxy: at 1 assumed point and ideal stop fills, total R changed from **+136.1907R to +139.9447R**, with 85 outcomes changed. This comparison did not show the timing change destroying the historical edge; it did not measure live fills. Five original stop exits had bars opening beyond the stop, while the original model filled exactly at the stop.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

The later audit included the 15:55 bid-open proxy and observed stop-gap adjustments. With **2 assumed points**: full history **+101.37R**, PF **1.116**, about **+0.072R/trade**; available 2026 **124 trades, −14.75R**. At 1 assumed point the same later-audit 2026 result was **−11.65R**. These are distinct from the original model’s +100.9R at 2 points and −11.71R for partial 2026 at 1 point: exit/gap assumptions differ. One historical sequence produced a 163-point gross-loss proxy instead of a nominal 40-point stop; the feed discontinuity is not proof of an actual FundedNext fill.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

A subsequent calculation on those 1,412 audited trades estimated gross expectancy **4.87 points/trade** before additive costs. At 10 points, mean net was **−5.13 points**, total **−181.03R**, PF about **0.83**. Historical break-even cost was approximately 4.87 points; approximately **2.37 points** retained PF ≥1.10. Both are accounting thresholds for unchanged historical trade outcomes, not safe live allowances: real bid/ask spreads can change triggering, fills and exits.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

## 7. Challenge simulations and scaling: record, not prediction

The completed later audit reported **453 scenarios and 3,080,300 simulated paths**, derived from the same 1,412 historical trades—not new independent market observations. It modeled fixed lots, \$5,000 initial account, 8% then 4% targets, two minimum days, 4% daily loss and static 8%/10% loss scenarios, including modeled intratrade adverse exposure. Costs were hypothetical; news-profit adjustments and full rule compliance remained unverified. At 10% maximum loss and 2-point cost:[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

| Lot | Nominal stop risk of \$5k | IID success / 20-trade-block success | Median opportunities among successes, IID / block |
| --- | --- | --- | --- |
| 0.03 | 0.24% | 92.6% / 96.9% | 531 / 583 |
| 0.05 | 0.40% | 79.3% / 87.5% | 249 / 293 |
| 0.06 | 0.48% | 73.6% / 81.9% | 185 / 223 |
| 0.08 | 0.64% | 65.2% / 73.7% | 112 / 138 |
| 0.09 | 0.72% | 62.4% / 71.1% | 91 / 116 |

The horizon was 2,520 opportunities over both phases; medians exclude failed and unfinished attempts. For 0.08 lot, a block-bootstrap historical sensitivity exercise produced about 44–88% across its 5th–95th percentiles; it is **not** a calibrated confidence interval for a real future pass probability. For the same lot at 10% loss, IID/block success was 74.0%/81.8% at 1 point, 65.2%/73.7% at 2 points, and 56.8%/63.1% at 3 points. An independent 20,000-path NumPy check for the 2-point IID case gave 65.875%, consistent with simulation noise. None establishes a current 70–80% live pass probability.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

The older [Phase 4.0 — Plan, prop-rule audit & scaling math](https://app.notion.com/p/6f2cab0962ad41bf9d91ada229903208) contains add-on, position-sizing, 24-month payout and reinvestment scenarios. Those were synthetic assumptions and the later audit explicitly withdrew them as validated income or purchase guidance. Do not use the old \$49.95 bundle, 0.55% sizing, expected payout or “buy now” call as a current decision. Same-signal accounts are correlated; additional firm accounts do not automatically diversify market risk.

## 8. Broker specification, rules and the EA

### Sizing correction

The Phase 3.8 assumption of **\$1/point/lot** was corrected by the trial’s MT5 specification: 2 digits, contract size 10, tick size 0.01, tick value \$0.10, hence **\$10 per index point per 1.0 lot**. At 40 points, 0.02 lot implies \$8 nominal risk, 0.03 \$12, 0.04 \$16 and 0.05 \$20, before spread, slippage or overruns. The old 0.3-lot idea implied \$120, not \$12. These are historical trial specs, not proof of current paid-account specs.[\[5\]](https://app.notion.com/p/3f4a5d08f8f581aba92de8d9b918b5a6)[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

David supplied a \$6,000 free-trial panel: \$300 target, 3 minimum trading days, 5% daily loss and 10% maximum loss; 1:20 index leverage and \$0/lot commission were also reported. This trial was **not** proof of a purchased \$5,000 challenge. Historical paid Lite rules were reviewed as 8% then 4% targets, 4% daily, 8% static max loss including equity, and two minimum days for purchases/resets on or after October 12, 2026. Earlier documents said five days. Paid EA add-on, funded news-profit treatment and Quick Strike restrictions require product/date-specific verification; no minute-bar backtest proves sub-30-second compliance. Treat all prices and terms as historical, not current.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

### Code and test status

- Original `first_hour_momentum.mq5` is in the archive. Static review identified that a true modify/close request return is not sufficient evidence of server execution; a potential duplicate-entry retry race; fixed lots rather than promised floor/target caps; state isolation limitations; and insufficient logging for all-in costs. A duplicate live trade was **not** demonstrated.
- A separate safety/logging v2 draft defaulted trading off, added account-specific state and a one-attempt lock, and improved response checks. David reported compilation **0 errors, 0 warnings, 611 ms**, initialization `armed=false`, normalized 0.02 lot and the \$10/point/lot spec on October 16. Compilation and initialization do not establish broker-runtime safety; v2 was not shown to be broker-tested or approved for paid use.
- The free-trial rules were later found to prohibit EAs; the instruction was to remove v2 and leave Algo Trading off. The previous installation guidance was corrected. A different EA-permitted demo can test mechanics, but does not validate FundedNext fills or permissions. A paid add-on does not automatically permit an EA on a free trial.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)[\[8\]](https://help.fundednext.com/en/articles/8902893-fundednext-free-trial-rules)

## 9. Recovered logs and observed quotes

The five supplied v2 CSV rows are all **INIT**, not completed orders or fills. Their `actual_price` and `adverse_points` zeros are placeholders, not evidence of zero execution cost. Account identifiers are omitted here. All rows are dated October 16, 2026; the following timestamps are the logged UTC fields, and the five spread snapshots were all 1.60 index points.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

| Logged UTC | Bid | Ask | Spread |
| --- | --- | --- | --- |
| 09:17:15 | 29964.20 | 29965.80 | 1.60 |
| 09:17:29 | 29963.20 | 29964.80 | 1.60 |
| 09:21:39 | 29951.58 | 29953.18 | 1.60 |
| 09:21:53 | 29948.08 | 29949.68 | 1.60 |
| 11:07:29 | 29893.83 | 29895.43 | 1.60 |

The first row’s `quote_time_msc=1792153034081`, interpreted as Unix UTC, corresponds to about 12:17:14 UTC, while the logged UTC field is 09:17:15; this three-hour convention mismatch needs reconciliation before quote/fill matching. Earlier trial logs supported server = UTC+3 at that time; that offset must not automatically be applied to another export.[\[9\]](https://app.notion.com/chat?t=404a5d08f8f58032a4a700a93fa24671)

The separately recovered `NDX100_202610202200_202610221447.csv` contains **2,226,113 rows with both bid and ask**, with a previously reproduced quote-update-weighted mean spread of approximately **1.7884 points**. The earlier audit reported 20 duplicate rows and 165 incomplete quote rows. Its timestamps span October 20–22, but timezone, originating account and server are not established. Quote updates are not equally spaced in time; their mean is not a time-weighted or strategy-entry-window cost. The file has no order IDs or fills and cannot establish slippage, realized all-in cost or profitability.[\[9\]](https://app.notion.com/chat?t=404a5d08f8f58032a4a700a93fa24671)

## 10. What the evidence supports—and does not

**Strengths:** fixed simple rules, a sizable reproducible historical sample, positive full years 2021–25, positive long and short totals, positive results after dropping 2024, and historical net profitability at the modeled 3-point cost despite the PF-gate failure. These are historical strengths, not proof of a durable live edge.

**Material concerns:** a negative partial 2026; thin cost-sensitive expectancy; revised gates after seeing results; uncertain selection history; a failed robustness threshold; bid-only historical approximations and gap exposure; no synchronized broker fill series; untested EA runtime behavior; incomplete funded-rule monetization modeling; and a small non-replenishing budget. A few seconds of delay has **not** been shown to destroy the strategy, and the negative half-year does **not** prove permanent decay. A few demo trades could test mechanics but would not establish profitability or reliable cost tails.[\[1\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

**Current practical conclusion:** preserve the candidate and the \$50, do not treat the old purchase or scaling plan as approved, and do not assume a replacement is automatically better. A later search for another strategy should be bounded and pre-specified; current status of that separate research is outside this archive’s verified scope.

## 10A. Recheck additions — original outputs and missing details

### Source-file and integrity checks

The original raw **ndx\_2023.csv** was recovered: 525,600 data rows; SHA-256 `155c4ef755c2f4a14daaf3774d1f20e245f57ef0e5bcd0fb99a88d6b5f352e70`. Its hash matches the original audit’s recorded input exactly. The original audit reports no duplicate timestamps and 60-second UTC intervals throughout; its winter/summer New York conversions match the 100,096 corresponding cleaned rows exactly. This is a **2023-only** verification, not independent verification of the other years.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

The recovered archives’ original validator and EA hashes match the earlier preserved copies. The complete FHM audit contains 114 files: the audited trade paths, all simulation cases and results, scenario summaries, bootstrap pools, code, logs, tests, charts and an evidence JSON. The earlier execution archive contains nine files, including both original-close and 15:55-open proxy trade ledgers. Extract the two unchanged ZIPs inside the consolidated package to inspect all rows and scenarios. Their README files explain assumptions and reproduction requirements.[\[1\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)

The original input profile found no bad OHLC values, nonpositive prices, weekend or outside-09:30–16:00 rows, and no actual missing 10:31 or 15:55 bars in this sample. A synthetic test nevertheless found that the original validator can silently enter a later bar if 10:31 is missing. This was a test of a failure mode, not a claim that the sample contained such a day. Another test checked hourly DST translation against Python zoneinfo across 52,584 hours; this is not a substitute for MT5 runtime testing.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

### Original Gate 3 output, preserved completely

These are the **older, superseded** numbers under a 1-point assumed cost, 8% static maximum loss and the then-coded five-day minimum. The final GO omitted the subsequently failing Gate 1.5. “CI” and null are labels from the original output, not validated live-probability bounds.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

| Lot | Nominal risk/trade | Historical max DD | DD within \$250 cap? | Modeled pass | CI low / high | Null | Old decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.02 | \$8 | \$163 | Yes | 0.94 | 0.64 / 1.00 | 0.17 | GO |
| 0.03 | \$12 | \$244 | Yes | 0.93 | 0.66 / 1.00 | 0.29 | GO |
| 0.04 | \$16 | \$326 | No | 0.88 | 0.68 / 0.97 | 0.32 | NO |
| 0.05 | \$20 | \$407 | No | 0.81 | 0.51 / 0.94 | 0.32 | NO |

### Later audited annual results and gap details

These use the later **15:55 bid-open and stop-gap proxies**, with 2 assumed cost points; they differ from the original annual table in section 3.[\[1\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)

| Year | Trades | Total R | Mean R/trade | PF |
| --- | --- | --- | --- | --- |
| 2021 | 258 | +13.77 | +0.0534 | 1.091 |
| 2022 | 258 | +9.98 | +0.0387 | 1.059 |
| 2023 | 256 | +14.55 | +0.0568 | 1.091 |
| 2024 | 259 | +35.61 | +0.1375 | 1.228 |
| 2025 | 257 | +42.22 | +0.1643 | 1.276 |
| 2026 through June 25 | 124 | −14.75 | −0.1189 | 0.832 |

Five original stop exits had gap-proxy gross outcomes of −40.009, −40.109, −163.061, −40.022 and −47.819 points, on 2021-06-03, 2023-12-04, 2025-10-10, 2026-02-06 and 2026-03-24 respectively, versus the original ideal −40 each. These are bar-feed proxies, not broker fills. One profitable exit occurred in the entry bar on 2025-04-07; its actual duration is unknown, so M1 data cannot establish a sub-30-second violation or compliance.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

At 2 assumed points, excluding the 37 calendar-proxy dates left 1,375 trades, +98.72R and PF 1.114. The exchange calendar used was a proxy and early closes were not silently fixed. A hypothetical 60% deduction from a subset of positive net P&L would reach historical break-even if applied to about 17.27% of that positive P&L; this is **not** a news-calendar-matched estimate or a prediction of firm deductions.[\[1\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)

### Additional simulation comparison — 8% static loss scenario

Same 2-point assumptions, 2,520-opportunity horizon and historical pool as section 7. “Success” means both modeled phases within the horizon; these are model frequencies, not live odds. Median opportunities are conditional on successful paths.[\[1\]](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090)

| Lot | IID / 20-trade-block success | Median opportunities among successes, IID / block |
| --- | --- | --- |
| 0.03 | 86.4% / 93.4% | 508 / 571 |
| 0.05 | 69.8% / 78.8% | 226 / 272 |
| 0.06 | 64.0% / 73.3% | 168 / 204 |
| 0.08 | 56.2% / 64.5% | 100 / 126 |
| 0.09 | 53.9% / 61.0% | 81 / 104 |

All 453 cases, including other sizes, block lengths, cost and horizon sensitivities, unfinished paths, seeds and bootstrap results, are preserved in `fhm_audit_complete.zip` inside the consolidated package.

### Quote distribution and manual-trial history

The separate quote analysis found median and mode **1.60** points, mean **1.7884**, 95th and 99th percentiles **2.08**, and maximum **114.04**. Spread was 1.60 on 61.24% of paired quote updates, 2.08 on 33.03% and 1.84 on 4.96%; 99.33% were at or below 2.08. The maximum was at 2026-10-21 01:01:00.182 in the file’s **unverified timezone**. These are quote-update-weighted observations, not a time-weighted entry/exit sample, and spread alone omits slippage and other charges.[\[3\]](https://app.notion.com/chat?t=404a5d08f8f58032a4a700a93fa24671)

After trial EA use was found prohibited, the historical plan shifted to manual trial execution and a separate EA-permitted demo. For the then-observed October mapping only, server time was reported as UTC+3: New York 09:30 / 10:30 / 10:31 / 15:55 corresponded to server 16:30 / 17:30 / 17:31 / 22:55 and Nepal 19:15 / 20:15 / 20:16 / 01:40 next day. These offsets must be rechecked for DST and broker-server changes. The proposed initial pilot was 3–5 normal strategy trades with the first reviewed immediately; it was a plan, **not evidence those trades happened**.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

The user-supplied historical MT5 specification also listed bid chart mode, market execution, 0.01 minimum and step, 40 maximum lot, USD profit/margin currency, FOK/IOC filling, and swaps of −329.382 long / +62.821 short in points, with Friday triple swap. These are trial-era values, not current paid-account guarantees. The original user-supplied funded rules listed 80% reward share, first and subsequent withdrawals after 10 days, refund at the third reward, and 3% maximum risk; they need independent product/date-specific verification before use.[\[2\]](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263)

## 11. Files: one downloadable package

**This document is a snapshot of the Notion master audit.** The files described below are in this package. It includes the original OHLC CSV, the full recovered 2023 raw CSV, validator and original EA, NDX100 quote CSV, original Phase 4 chart, reproduced original-model ledger and calculations, historical snapshots of four deleted Phase 3 pages, and both unchanged original audit ZIPs. Extract the two original ZIPs to access their 123 constituent files, including full simulation tables, audited trade paths, logs and scripts. `READ_FIRST_RECHECK.txt` explains the layout; `SHA256SUMS_RECHECK.txt` covers all packaged files. The older README and checksum list describe the earlier package only. Snapshots preserve historical claims, not endorsements.

[The referenced file is included in this package; see READ_FIRST_RECHECK.txt.]

The original reproduced ledger is also available separately:

[The referenced file is included in this package; see READ_FIRST_RECHECK.txt.]

### Sources and navigation

- [PHASE4](https://app.notion.com/p/3f4a5d08f8f580399305f211a0f6d090): 3.6 bot/Pine, 3.8 pivot, 3.9 gates, 3.10 demo gate, Phase 4.0 plan, guardrails, data, validator and original EA.
- [Main Phase 4 Plan conversation](https://app.notion.com/chat?t=3f5a5d08f8f5803ea32c00a9ed1e3263): the original pasted gate output, calculations, October 16 logs, later audit and original downloadable `fhm_audit_complete.zip`, `phase3_execution_audit.zip` and `first_hour_momentum_demo_v2.mq5`.
- [Notion source](https://app.notion.com/p/3fda5d08f8f58068ab09f60b361cf52d) and [later spread and fill-log conversation](https://app.notion.com/chat?t=404a5d08f8f58032a4a700a93fa24671).
- [Earlier Phase 3 review conversation](https://app.notion.com/chat?t=3f4a5d08f8f580ac9ce100a977eff2e0): source for historical snapshots of the deleted Phase 3 plan, playbook, handoff and competition page.

## 12. Gaps and completeness boundary

**Corrected after recheck:** both original audit ZIPs and the full 2023 raw source are now included. The revised v2 EA source was delivered in the original chat but its old attachment could not be reopened; it is **not** in the package. The full original ORB return series, complete earlier 14-day trial history, synchronized broker orders and fills, current account/server specifications, raw source files for the other years and market data after June 25, 2026 were not recovered. “Not recovered” does not prove they no longer exist. Adding the v2 source, MT5 History/Journal/Experts exports or missing source-year data would close some gaps without placing new trades.

Scope: visible PHASE4 child pages and attachments, the named main chat, the earlier Phase 3 review, the later spread/fill-log chat, the recovered audit packages and related session search results. Two additional sessions surfaced in historical search—“CSV bid-ask spread calculation” and “Prop Firm Guardrails Page”—but direct access returned “Agent thread not found.” The spread session’s substantive result was recovered as quoted in the later chat and is summarized above; the other session could not be fully reviewed. Search may not index every conversation. This is a detailed, bounded record of the evidence found, not a guarantee that every prior chat or file has been recovered.
