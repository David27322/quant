# PHASE 5 — Project Audit & Continuation Handoff

**Checkpoint: 8 November 2026.** A consolidated, code-free record of the project’s decisions, evidence, failures, corrections and next steps. This is a research handoff, not a trading recommendation.

## Executive status

- **No qualified, account-ready edge has been established.** The original 16 available US-index configurations did not qualify. The later, separately authorized pre-2021 ORB replication failed its screen, and the USDJPY Tokyo-fix screen was inconclusive. These are not proof that profitable strategies do not exist.
- **The current weekly cross-sectional FX momentum idea is a draft, not a tested or approved strategy.** A practical source of sufficiently complete historical bid/ask data remains the immediate blocker. Its economic and statistical usefulness remain unproven.
- **Preserve the research history and the 2026 reserve.** At least 20 prior US-index configurations were recorded, including at least four with missing return histories; the later USDJPY screen added one exploratory candidate. A separate GitHub history reports many more searches whose overlap has not been reconciled. Do not reset the count or add the figures blindly.
- **No account purchase, live trade, new strategy trial, or holdout test is authorized by this handoff.** Research can continue, but each performance test needs a clearly scoped, predeclared budget and a defensible interpretation.

## 1. Purpose, preferences and constraints

The goal is to find a genuine after-cost edge, then use prop funding to compound, scale and eventually diversify risk. The original setup was a FundedNext Stellar Lite 5K CFD challenge, MT5/MetaEditor, and Dukascopy Nasdaq/US100 historical data. Earlier ORB variants were screened superficially; a first-hour momentum strategy was studied for more than three months. It was not conclusively disproven but appeared thin, with poor 2026 performance. The project sought a rigorous process rather than immediately buying a challenge.

The original context recorded a $50 budget and a $30 estimated base account, with illustrative EA and daily-loss-limit add-on totals. Later, the user described $50 as the current total loss budget, possible future $10 monthly contributions, and an illustrative goal of passing in roughly three months and receiving a first payout one to two months later. Future money was not treated as already available. On 6 November the user was open to considering FundedNext Futures, including Flex and Rapid Pro, with approximately $74 potentially available if good results were found. This was openness to consider alternatives, **not authorization to switch or buy**. Prices, taxes, eligibility and account terms can change.

The user wants clear, practical work without unnecessary complexity or long data-collection burdens. They explicitly asked that assumptions be identified, calculations checked, plans criticized before delivery, unsuccessful results preserved, and the project not be abandoned simply because one research round stopped. Trading rules and product terms must be verified for the actual account before relying on them.

## 2. How to read the numbers

- **R/trade** is return divided by a specified research risk denominator. The original runs used a constant reference risk budget and continuous, cost-aware exposure; they were **not** compounded account returns, actual dollars, executable lot sizes or prop-account payout forecasts. A stop can gap beyond −1R.
- **Daily Sharpe** is an annualized statistic based on daily research returns; no-trade eligible days are zeros. It is not a guaranteed future Sharpe.
- **Development results** are measured on history used for research and selection. Cross-validation, walk-forward splits and robustness checks on that same history are useful diagnostics, but are not equivalent to a genuinely untouched final confirmation.
- **Provisional costs** are scenarios, not verified broker averages or worst-case bounds. A positive point estimate does not itself establish an edge, and a negative estimate or failed gate does not prove the population effect is negative.
- A **preliminary pass**, if one occurs in the future, is not account qualification. A candidate still needs meaningful economics, execution and risk feasibility, credible independent evidence and a forward demo.

## 3. Chronology and research accounting

| Stage | What happened | Disposition |
| --- | --- | --- |
| Before the frozen selection | At least 3 older ORB variants and 1 FHM configuration were tried. Their complete return streams are missing. | Count at least 4; exact search-adjusted DSR cannot be reconstructed from trial count alone. |
| Selection and preparation, October | Frozen set of 4 ORB and 4 late-session momentum configurations; data, cost, execution and synthetic logic checks. | No market results at selection stage. |
| Original development round | 8 configurations evaluated on the 2021–June 2026 Nasdaq proxy. | None qualified. |
| Opening-gap reversal | User authorized 4 fixed configurations despite an earlier recommendation not to spend that round. | All 4 negative at base costs; none qualified. |
| Turn-of-month calendar flow | 4 fixed configurations tested in a separately authorized round. | None qualified; family and joint statistical gates failed. |
| Decision and engineering audit | Reclassified rejection reasons, checked costs and identified/repaired a narrow floating-point touch defect in a separate sandbox copy. | No historical rejection was overturned. |
| Selection-method synthetic comparison | Compared a strict gate stack with a simpler Holm-adjusted mean test on simulated data. | Neither met the fixed usefulness standard across required conditions; neither was adopted. |
| Pre-2021 ORB forensic replication | One unchanged ORB-30-2R rule tested on previously unused 2013–2020 proxy history after explicit authorization. | Failed prespecified preliminary screen. The older period is now exposed. |
| USDJPY Tokyo-fix | One separately authorized new exploratory test, 2021–2025. | Inconclusive; preliminary gate did not pass; no stress test was run. |
| Later literature and feasibility work | SPX trend, FX trend/carry, macro announcements, futures and weekly FX momentum reviewed. | Feasibility/design only unless explicitly identified above; no claim of strategy profitability. |

**Count carefully:** at least 4 older trials + 8 original development + 4 gap + 4 calendar = at least 20 US-index configurations, of which 16 return streams were available. The unchanged ORB replication used a new data period, not a new parameter variant; it is a separately logged performance exposure. The USDJPY test is one additional exploratory strategy trial. A linked GitHub README reports 50 to over 200 NQ ORB combinations and later momentum research; the overlap with the 20+ record is unknown. It is therefore unsafe to state an exact total or sum the two numbers.

A key process error was giving inconsistent advice after research budgets had been exhausted: at times further rounds were suggested without adequately carrying the stopping rule or earlier selection. Another error was implying that a failed round meant abandoning the whole trading project. The corrected position is: **close the specific round, preserve its evidence, and only start a distinct, finite, explicitly authorized research program when its design and data are defensible.**

### The story in brief

ORB-30-2R looked promising in development: it was the least-bad available candidate, with positive base and 2× estimates. But it had been selected from a broader search, failed its adjusted statistical test and later failed the unchanged pre-2021 forensic replication. It was therefore parked—not declared impossible. The team pursued a distinct USDJPY Tokyo-fix idea because published spot-market evidence and a closer spot-to-CFD mapping offered a different mechanism; its one authorized screen was inconclusive. Futures were subsequently considered for their research and market-data infrastructure, but suitable contract-level MNQ history was difficult to obtain, and related Nasdaq history had already been searched. No futures strategy backtest was run. The current weekly FX basket is a draft, not a proven winner.

## 4. Original US100 data and execution model

### Data

The original development proxy was Dukascopy **USATECHIDXUSD BID one-minute candles**, interpreted in America/New_York and restricted to XNYS scheduled cash sessions including early closes. The supplied file had 552,092 unique timestamps. A calendar audit excluded 17,642 out-of-session or holiday bars, retaining **534,450 cash bars across 1,375 sessions**, 4 January 2021–25 June 2026. Twenty-one prior-close warm-up sessions left **1,354 common scored sessions**, beginning 3 February 2021. Seventeen large minute changes were retained and flagged rather than deleted. The data are a CFD proxy, not verified FundedNext fills.

The audit reconciled the expected cash-minute grids and scheduled closes. It corrected earlier calendar assumptions; use a real exchange calendar and scheduled early closes, not a constant UTC offset. The turn-of-month round used an independent full calendar so the truncated June 25 endpoint was not incorrectly treated as month-end.

### Frozen cost-v1 scenarios

| Scenario | Spread | Adverse slippage per fill | Reference round-trip friction |
| --- | --- | --- | --- |
| Base | 1.80 points | 1.00 point at entry and exit | 3.80 points |
| 2× | 3.60 | 2.00 each | 7.60 |
| 3× | 5.40 | 3.00 each | 11.40 |
| Cautious-spread overlay | 2.10 | 1.00 each | 4.10 |

Commission was provisionally $0 for the index. The user’s spread summary was 1.60 typical, about 1.80 average, and about 2.10 cautious; four absolute execution deviations averaged 0.8725 points. The 1-point adverse allowance per fill was rounded policy, **not** an estimate of signed expected slippage or a tail bound. Later the user reported seven trades used for spread sampling and four for execution calibration; the raw synchronized observations and complete dates are still unavailable. Minute bars do not reveal subsecond execution or actual intrabar ASK extrema.

Model BID/ASK and costs once: short exits trigger on modeled ASK, and costs already included in fill-to-fill P&L must not be deducted again. One journal short from 29312.53 to 29321.63 was −9.10 points in actual fill-to-fill terms, before any separately charged fees. Latency was recorded as a diagnostic, not converted into an invented cash charge. Cost validation reported 22 checks and 30,000 synthetic fill calculations; those establish accounting checks, not profitability.

## 5. Original eight-candidate development results

Four ORBs used 15- or 30-minute ranges and 1R or 2R targets. Four late-session momentum configurations varied entry 60 or 30 minutes before close and signal threshold 0 or 0.25 prior-volatility units. Both families used at most one daily opportunity and scheduled exits five minutes before cash close. Rules were frozen before the market backtest.

| Configuration | Trades | Base Sharpe | Base R/trade | 2× R/trade | 3× R/trade | Joint adjusted p, 20-session blocks |
| --- | --- | --- | --- | --- | --- | --- |
| ORB-15-1R | 1,335 | 0.128 | +0.0074 | −0.0349 | −0.0788 | 0.8733 |
| ORB-15-2R | 1,335 | 0.677 | +0.0503 | +0.0062 | −0.0383 | 0.2274 |
| ORB-30-1R | 1,212 | 0.453 | +0.0255 | −0.0099 | −0.0436 | 0.5001 |
| ORB-30-2R | 1,212 | 0.785 | +0.0528 | +0.0165 | −0.0166 | 0.1384 |
| LATE-60-0 | 1,354 | −0.838 | −0.0256 | −0.0624 | −0.0967 | 1.0000 |
| LATE-60-0.25 | 908 | −0.323 | −0.0121 | −0.0476 | −0.0815 | 0.9976 |
| LATE-30-0 | 1,354 | −2.013 | −0.0478 | −0.0840 | −0.1176 | 1.0000 |
| LATE-30-0.25 | 908 | −1.376 | −0.0400 | −0.0749 | −0.1076 | 1.0000 |

**Decision:** none passed the synchronized eight-candidate max-Sharpe null at p ≤ 0.05. ORB-30-2R was the highest archived base-cost daily Sharpe among the 16 available return streams, not necessarily the best of the entire unknown history. Its adjusted p-values were 0.1336 and 0.1384 using 5- and 20-session blocks. Its positive 2× estimate had a 20-block nominal 95% interval of approximately [−0.0325, +0.0669] R/trade.

Important correction: the original **overall** PBO was 6.35%, which passed its gate. ORB-only PBO of 42.06% was a diagnostic warning, not an additional original rejection gate. Selected CPCV paths and family corroboration passed for the descriptive leader; dependent CPCV paths are not independent future confirmations. Exact history-adjusted DSR remained unresolved. All eight were negative at 3×, but 3× was originally diagnostic, not a retroactively added rejection rule.

The original engine and robustness work reported independent scalar comparisons, cost and timing fixtures, block bootstraps, random controls, delay and noise tests, regime breakdowns, and walk-forward analysis. Favorable delays and subgroups were **nonselectable diagnostics**; they are not permission to change entry rules after seeing results.

## 6. ORB-30-2R autopsy — the least-bad available candidate

### Exact frozen rule

- Form the opening range from BID highs/lows between 09:30 and 09:59 New York time. The first completed one-minute close strictly above the high signals long; strictly below the low signals short. Enter at the next minute’s open before 11:00, at most one opportunity per session.
- Stop at the opposite opening-range boundary. The target is twice the raw BID distance from entry open to stop; this nominal 2R is **not** the cost-aware planned-risk denominator. Short exits use synthetic ASK, with the short stop at the original numerical high, not high plus spread a second time.
- Invalid or zero-width entries are skipped; no retry, overnight hold, trailing stop, scaling or news/regime filter. Entry-minute extremes count. Stop first on ambiguous bars; adverse opening gaps execute worse; targets are capped. Time exit is the opening price five minutes before scheduled close, including 12:55 on a 13:00 close.
- Base planned risk in points was entry BID minus stop plus 3.80 for a long; stop minus entry BID plus 2.00 for a short. This asymmetry follows the archived quote convention. The original research did not enforce actual lot steps, margin or broker tick rounding. Later lot examples were conditional illustrations, not approved live sizing.

### Development economics

Across 1,212 trades, the saved same-path accounting decomposition was +0.08949 gross-reference R/trade, −0.01740 spread drag and −0.01933 slippage drag, for **+0.05275 net R/trade**. Costs absorbed about **41.1%** of the gross reference. This is an accounting decomposition using the cost-model paths and sizing, not a separate zero-cost backtest.

[orb_year_notion_agent_chart.html](orb_year_notion_agent_chart.html)

Archived base-cost annual net R/trade. 2021 begins after warm-up; 2026 ends on June 25. These are selected development results, not independent annual confirmations.

| Year | Trades | Net R/trade | Daily Sharpe |
| --- | --- | --- | --- |
| 2021, partial | 204 | +0.0551 | 0.861 |
| 2022 | 227 | +0.0488 | 0.708 |
| 2023 | 218 | +0.0208 | 0.295 |
| 2024 | 232 | +0.1085 | 1.531 |
| 2025 | 224 | +0.0493 | 0.757 |
| 2026, through June 25 | 107 | +0.0083 | 0.138 |

2024 supplied 39.4% of cumulative net R; excluding it still left +0.0396 R/trade, so the full result was not solely one year. Partial 2026 weakened mainly **before** costs: gross reference declined from +0.09526 in 2021–2025 to +0.02990 R/trade, while cost drag fell from 0.03820 to 0.02163 R/trade. Partial 2026 unweighted point means were −2.105 gross and −5.905 net points/trade despite slightly positive constant-risk R. These different exposure conventions are not interchangeable.

The original low-volatility bucket fell from +0.1311 R/trade in 2021–2025 to −0.0892 in partial 2026, based on only 45 trades; mid and high buckets were +0.0341 on 37 and +0.1455 on 25 respectively in partial 2026. This is a descriptive warning, not evidence justifying a new filter or proof of permanent decay. Original closed-day maximum drawdown was 14.52R, not an actual funded-account breach calculation. A small FOMC-only subgroup had 39 leader trades at −0.1143 R/trade versus +0.0583 on other sessions; it is confounded and does not cover all news.

## 7. Opening-gap reversal and calendar rounds

### Positive overnight-gap reversal

Short-only: two gap thresholds, 0.25 and 0.50 prior-volatility units, crossed with exits at 10:00 or 10:30 New York. Entry was 09:31, with the prior close as target and an initial-gap-sized stop. The four rules were preregistered and evaluated on the same 1,354 scored development sessions.

| Configuration | Trades | Base R/trade | 2× R/trade | 3× R/trade |
| --- | --- | --- | --- | --- |
| GAP-025-1000 | 463 | −0.0528 | −0.0935 | −0.1324 |
| GAP-025-1030 | 463 | −0.0396 | −0.0763 | −0.1131 |
| GAP-050-1000 | 258 | −0.0213 | −0.0444 | −0.0672 |
| GAP-050-1030 | 258 | −0.0070 | −0.0282 | −0.0488 |

All four had negative base estimates, despite positive same-path gross-reference point means. The 3.80-point friction plus tick rounding exceeded the average gross estimate under these rules. A +3-minute entry-delay diagnostic for GAP-050-1030 reached about +0.0021 R/trade; it was not a registered candidate and must not be promoted after the fact. A family PBO pass did not make a losing family profitable. Intervals were wide enough that the results did not prove every gap strategy or broker unprofitable.

During QA, 36 initial base-scenario short stops were 0.01 point too high because of intermediate floating-point rounding. Decimal correction and a full rerun preserved the frozen rules and did not change the no-qualification decision.

### Turn-of-month cash-session flow

Long 09:31 to five minutes before close on the last one or two and first two or three scheduled cash days of a month. Stops used prior-only daily volatility. This tested a narrower cash-session idea, not the published overnight premium. Costs were the same provisional scenarios.

| Window | Trades | Base R/trade | 2× R/trade | 3× R/trade | Base total R |
| --- | --- | --- | --- | --- | --- |
| TOM-L1-F2 | 192 | +0.02298 | +0.00426 | −0.01372 | +4.412 |
| TOM-L1-F3 | 257 | +0.03577 | +0.01649 | −0.00200 | +9.192 |
| TOM-L2-F2 | 256 | −0.02057 | −0.03892 | −0.05650 | −5.267 |
| TOM-L2-F3 | 321 | −0.00152 | −0.02038 | −0.03846 | −0.487 |

Configurations overlap, so their totals are not a portfolio sum. Only 2/4 had positive base expectancy versus the 3/4 rule. Family PBO was **35.71%**, above 30%; the descriptive leader’s joint available-16 adjusted p-values were **0.8914/0.9059** for 5/20 blocks. Its 20-block base interval was [−0.05883, +0.13644] R/trade. Five positive CPCV paths were dependent. Exact full-history DSR remained unresolved. One- and three-minute delay diagnostics turned all four estimates positive, but were nonselectable and did not rescue the frozen entries. No final candidate or holdout was selected.

## 8. Audits, corrections and what they do—and do not—prove

### Rejection classification

Across the 16 available configurations, the audit classified **10** with negative base estimated R/trade, **2** positive at base but negative at 2×, and **4** positive at both base and 2× but without sufficient qualification evidence. Only two of the ten base-negative configurations had pointwise 95% intervals entirely below zero; those intervals were not simultaneous, selection-adjusted conclusions. Four or more older return histories remained unavailable.

### ASK touch and arithmetic repair

A legacy binary floating-point calculation could miss an exact short-stop ASK touch. Replay of **38,472 saved order/scenario records** produced **12 changed exit-time records**, all stop-to-stop, with no absolute P&L change above 1e−9 R. An independently checked decimal repair in a separate sandbox copy passed **443 regression checks**. The archive, frozen costs, thresholds and ledgers remained unchanged. This was not a complete repaired-engine strategy rerun or evidence that live execution is correct; it did not reverse any rejection.

No duplicate spread/slippage deduction was found. Other limitations remain: constant synthetic ASK is not actual historical ASK; minute OHLC does not reveal intrabar ordering; the stop-first convention is an assumption; broker pricing, lot steps, margin, gaps, latency and execution tails are not established. The restored decision-audit package is explicitly **not** the original complete audit working folder.

### Statistical gates and synthetic power

The initial synthetic study used 260,000 synthetic evaluations and 120,000 independent null-reference rounds. In one 500-day, 12-candidate independent-normal setup, an unadjusted selected-winner test falsely approved 46.74% of null rounds; the full stack approved 0.06%, but detected a planted four-candidate annual-Sharpe-1 effect in only 1.59%. Another 1,000-day setup detected 4.51%. These are scenario-specific simulations, not estimates of actual market performance or a universal guarantee.

A later preregistered **36,000-dataset** synthetic comparison tested strict procedure A against a simpler Holm-adjusted block-mean procedure B. At 1,354 sessions with 20% clustered activity, detection for an isolated assumed +0.10 R/active-trade effect was **1.2% for A and 5.5% for B**; with three such effects it was 1.5% and 13.3%. At 2,708 sparse sessions B reached 18.4%/35.3%. In an easier daily IID, three-effect case B reached 92.3%. Both met the stated false-approval bounds in those tested scenarios, but neither met the 80% detection standard across all required conditions, so **neither was adopted**. A was a prospective stricter comparator, not a literal replay of the historical gate; B did not certify that the mean exceeded +0.10R and omitted family and stress gates.

The lesson is two-sided: adjusting for search and dependence matters, but stacking gates can leave little power. Historical nonqualification is not proof that every true edge is absent. Conversely, low power is not a license to lower thresholds based on old results or keep searching until something passes. For a future protocol, use the simplest defensible preliminary gates, then independently test both false-positive control and power under relevant dependence **if a candidate survives plausible base gates**.

## 9. New 2013–2020 data and the authorized ORB replication

### Data cleaning and eligibility

The user reported exporting Dukascopy BID one-minute data for 2013–2020 and splitting it for upload; they reported not previously using the pre-2021 data. The CSV itself does not encode instrument, quote side or timezone, so provenance relies partly on the user’s description. A seam check found no overlap or date-crossing between the two halves. XNYS open-inclusive/close-exclusive cleaning preserved original prices, did not fill gaps, and used New York wall time.

| File | Retained cash bars | Scheduled / represented sessions | Missing expected minutes |
| --- | --- | --- | --- |
| 2013–2016 | 382,389 | 1,008 / 992 | 9,111 |
| 2017–2020 | 390,456 | 1,007 / 1,006 | 474 |
| 2026-06-26–2026-10-30 | 34,710 | 89 / 89 | 0 |

Across 2013–2020, **1,980 of 2,015 scheduled sessions were complete**; 35 were incomplete, with 24 of those in 2013. Missingness was clustered, so excluding incomplete sessions can bias results. A primary-source timestamp check found all 2,329 missing timestamps on nine successfully fetched dates present in the provider archive; 26 dates remained unverified because of network errors. This supports some export losses, not proof of the cause for all gaps. After the old common 21-session warm-up convention, 1,959 complete sessions remained. That warm-up was a comparability choice, not intrinsically required by ORB.

### Frozen replication result

The user explicitly authorized the one unchanged ORB-30-2R forensic test: base and 2× costs, incomplete sessions missing rather than zero, and 10,000 scheduled-slot block bootstrap draws each for 5- and 20-slot lengths. Pre-outcome synthetic fixtures and archived-engine comparisons passed. The run used **1,994 scheduled slots**, **1,959 complete eligible sessions**, **1,681 trades**, 269 eligible no-signal sessions and nine zero-range sessions.

| Measure | Base | 2× |
| --- | --- | --- |
| Net expectancy, R/trade | −0.15610 | −0.26487 |
| Mean daily R per eligible session | −0.13394 | −0.22728 |
| Sum of R at fixed reference risk | −262.40 | −445.24 |

**Decision: failed the prespecified preliminary screen.** Base mean daily R had nominal 95% moving-block intervals [−0.17098, −0.09746] and [−0.16900, −0.09552] for 5- and 20-slot blocks. Annual descriptive expectancy was negative in every observed year. The conditional independent false-positive/power calibration was not performed because the base gates failed; the intervals are nominal and model-dependent, not a definitive statistical guarantee. A same-path decomposition was −0.01179 gross-reference and −0.14431 modeled cost R/trade, not a separate zero-cost rerun.

Constant point costs might be disproportionately large relative to older prices and risk distances; true historical ASK and fills are absent, and missing sessions are clustered. The result is a failure under the frozen proxy, not a license to adjust costs or tune the rule on the same exposed history. The user instructed: **no tweak-and-retest if failed or inconclusive**. A demo was conditional on a pass and was not triggered. The 2013–2020 period is now exposed, and the earlier selection-adjusted failure and missing DSR remain unchanged.

## 10. USDJPY Tokyo-fix exploratory test

### Rationale and setup

Published spot-fixing work reported a historical 3.15 bp mean JPY appreciation in a post-Tokyo-fix window, but selecting this pair and window after seeing the paper introduced literature-level selection. This was not an exact replication of the full published portfolio, and historical midquote returns do not establish executable broker profits.

The user authorized **one new exploratory trial**, distinct from the exhausted original budget. The frozen rule shorted USDJPY at 09:55 Asia/Tokyo and covered at 02:00 America/New_York on the same Tokyo date, on Japanese banking days in 2021–2025. It used the first valid synchronized Dukascopy BID/ASK tick at or after each target within five seconds. This timed, no-stop research exposure was never an account-ready trading plan.

Preliminary costs were deliberately optimistic: 0.96 pip round-trip spread, 0.05 pip total slippage and $3 per standard lot round trip, converted into USD-notional basis points. The user’s MT5 showed $3/lot while the public site listed $7 and said per side; actual target-account fee and charge timing remain unresolved. Proxy mid plus all-in spread was used once; no extra provider spread was added.

### Result and data quality

Of **1,223** scheduled Japanese banking days, **1,216** had admissible endpoints, or **99.43%**; seven were missing, several near Christmas. All 2,446 requested hours were retrieved after retry. The dataset contained approximately 16.37 million quote rows; endpoint quality and independent calculation checks passed. This validates the defined proxy procedure, not FundedNext fills.

Mean net return was **−0.574 bp per eligible event** on USD notional. HAC(60) standard error was **0.700 bp**; nominal one-sided 97.5% lower and upper bounds were **−1.945 and +0.797 bp**. The interval spans zero: **inconclusive, not a pass and not proof of a negative population mean**. Per the protocol, the proposed $14 commission and higher-spread stress was not evaluated, and no detailed cost calibration was undertaken. No stops, account drawdown or position-sizing feasibility were tested. Do not tweak and retest the same sample or revive this candidate as if it had passed.

## 11. Other research directions and why they were parked

| Lead | Work completed | Main limitation / current disposition |
| --- | --- | --- |
| EURUSD vs US100 | Documentary feasibility screen: instrument and historical BID/ASK route available. | No demonstrated cost or risk-sizing advantage; exact account lot step and commission unresolved. No EURUSD strategy backtest. |
| Single-SPX slow trend | Literature, sizing and historical-feed quality review. | Weak single-market counterevidence; dividend adjustments, feed construction, account mapping and meaningful power unresolved. No strategy test. |
| USDJPY forward trend | Algebraic spot/forward mapping and feasibility. | Swap-free spot does not reproduce forward premium or published excess return; post-study independence and information limited. Parked. |
| US-equity announcement premium | Literature and account/data feasibility. | Competing evidence, sparse genuinely independent events, news rules and price/dividend mapping. Parked; no backtest. |
| G10 FX carry | Literature, broker-policy and financing review. | Carry requires forward/interest cash flows; swap-free spot alone is not the published strategy. Overnight holding was generally confirmed by support, but basket-specific permission and historical swaps remain open. No test. |
| MNQ intraday futures momentum | Literature, data and contract/account feasibility; no performance test. | NQ/US100 history overlaps previous Nasdaq research. Actual MNQ contract-level data unavailable to user; continuous NQ source/roll/timestamp details not verified. A new feed is not fresh independent evidence. Lead discontinued. |
| Delayed FOMC FX | Event count, point-in-time signal and account-feasibility review. | Live historical availability of the exact surprise measure unverified; few events and possible 30/60-day inactivity-rule conflict. Parked. |
| Weekly cross-sectional FX momentum | Literature, synthetic inference, mapping and quote-access checks. | Current design lead only; coverage, costs, inference and practical account feasibility remain unresolved. No strategy outcomes computed. |

The SPX quality check found 9 daily opens disagreed with first available minute opens among 28 sampled dates, despite highs/lows/closes agreeing. The sample was not representative and no stream was established authoritative. Index dividend adjustments may matter separately from swap.

For futures, CME MNQ was described as $2 per point, 0.25-point tick worth $0.50, launched in May 2019. Full-size NQ is $20 per point; a hypothetical 50-point adverse move is $1,000 before costs, material against a quoted $1,000 Rapid Pro maximum loss. Prices and rule examples recorded on 6 November were approximately $64.99 first 25K Rapid Pro, $44.99 with a daily-loss-limit add-on, and $74.99 first two eligible 50K Flex purchases, subject to verification. These are historical research notes, not current checkout guarantees or purchase advice. Futures have a daily flatten requirement; a CFD overnight idea cannot automatically transfer.

## 12. Latest continuation checkpoint — weekly FX basket

### What is proposed, not authorized

The latest design is an adaptation of cross-sectional spot momentum, **not** an exact reproduction of a published forward-based currency portfolio. The proposed universe is EURUSD, GBPUSD, AUDUSD, NZDUSD, USDCAD, USDCHF, USDJPY, USDNOK and USDSEK. Convert all quotes to USD per foreign currency; rank the return since the previous decision, buy the strongest foreign currency and sell the weakest, with deterministic tie handling. Decisions were proposed at 08:00 UTC weekly; a calendar-only Thursday shift for Wednesday Christmas or New Year was drafted after quote-window checks, before seeing strategy returns. Four such shifted dates were identified. Holiday handling still needs broader validation.

The draft used a hypothetical $2,000 target per leg, 0.01-lot rounding, executable-side proxy quotes, $7 per standard lot per transaction side, zero additional slippage and a hypothetical swap-free account. These are modeling inputs, **not verified account fees, measured returns or recommended sizes**. Changed legs incur spread and commission once; unchanged legs retain units. The draft sample has 623 decision-to-liquidation intervals ending 24 December 2025, plus the initial observation. It is exploratory and not independent merely because the paper ended earlier.

An earlier analyst-selected **$5/week hurdle was rejected by the user as too slow and withdrawn before any test**. It was not the observed return of the basket. The replacement draft normalizes net weekly P&L by starting gross exposure, in basis points, and applies a 12-block preliminary positive-mean screen. It remains a design, not a validated universal rule. Separately proposed $4,000 and $12,000 gross-exposure illustrations and a 26-week horizon were hypothetical, not selected live sizes or the user’s accepted deadline. Weekly snapshots cannot verify intraday daily-loss breaches. Any later account assessment would require synchronized mark-to-market, conversion, gaps, margin, lot rounding, actual rules, target speed and breach risk.

### Evidence and counterevidence

A broad weekly currency-momentum study provides a rationale, but used spot and forward mid-rates across developed and emerging currencies. Later research reported negative results for a different developed-currency momentum construction; it weakens confidence but does not directly test this precise weekly spot-CFD rule. The swap-free spot adaptation excludes forward financing and is a different return construction.

In separately seeded synthetic checks, the revised 12-block test had a 3.90% false-positive rate under an assumed strongly dependent AR(1) rho 0.9, above its one-sided nominal 2.5% tail. With an invented +20 bp/week mean, estimated synthetic detection was 91.67% at rho 0.3 but only 23.37% at rho 0.9. These are simulation examples with assumed volatility/dependence, not actual strategy power or returns. They do not account for the entire search or nonstationarity.

### Data access: latest known position

- A tick-window collector would require about **11,250 hourly requests** for the full nine-pair schedule. The user reported 11 errors after 200 requests and found it too slow; the prior agent acknowledged it was overengineered and advised stopping. The user subsequently deleted the local collector cache. Do not ask them to restart that long job by default.
- A sandbox hourly-candle pilot for March 2014 and March 2025 retrieved **19 of 36** pair/side/month files after retry; 17 failed with 503, TLS or timeout errors. That demonstrates access difficulty, **not** proof that the missing market data do not exist. Five paired hourly/tick checks matched selected boundary prices, insufficient to establish general equivalence or precise five-second execution.
- An ECB daily reference-rate download is compact but indicative, not executable; its publication time does not represent the proposed 08:00 UTC rule. Five of the proposed 625 dates lacked an ECB observation. Do not use it as an equivalent tradable pass or silently alter the calendar to fit it.
- Hourly BID/ASK data could support a revised **preliminary proxy**, if obtained, but it cannot establish synchronized 5-second fills, live execution, or intraday account compliance. Any change from the tick rule must be explicitly specified before looking at performance.

**Current next action:** determine whether a practical, sufficiently complete historical BID/ASK source exists for the nine pairs and 2014–2025, preferably in a small, bounded feasibility check. If hourly data are accessible, define and document the changed proxy rule and its limitations before requesting a separately authorized one-trial budget. If data access or informative inference remains inadequate, say so and reconsider the direction rather than running a weak substitute or burdening the user with another large collector. Do not demand full execution calibration before a plausible preliminary survivor.

## 13. Holdout, account rules and unresolved issues

1. **Recent reserve:** previously reviewed history through 26 June 2026 is development; post-June-26 price performance was kept sealed in the recorded tests. A cleaned 26 June–30 October file exists, but its existence does not imply its returns were inspected or that the whole period is pristine. At least 22 October and all spread/execution-calibration dates must be excluded. Only October 22 is confirmed; other dates remain unknown. No new holdout is automatically created by switching instruments, chats or feeds.
2. **Search history:** at least four older ORB/FHM return streams are missing, preventing exact historical DSR and full joint-null reconstruction. Reconcile the separate GitHub research history before claiming a total. Never fabricate missing streams or reset counts.
3. **Broker costs and environment:** original index slippage and spread, USDJPY $3/$7 commission, exact round-trip charging, server offsets, symbol mapping, variable spread, gaps and live fills remain unverified. Small samples are not tail estimates. Seek accurate calibration after a plausible candidate survives initial gates, not as a prerequisite for every idea.
4. **Rules:** the recorded Stellar Lite document lists 8%/4% phase targets and 4% daily/8% maximum loss, but official pages previously conflicted on minimum trading days and on 30 versus 60 days of inactivity; one review also found conflicting forex leverage descriptions. Verify the actual purchased/reset account’s current governing terms, news rules, EAs/add-ons, stop requirements, equity-based and cumulative risk, lot size and margin. Archived values are not a current contract.
5. **Exposure and inference:** published papers, user research and correlated instruments expose overlapping data. Distinguish exploratory analysis from truly independent confirmation. Account for dependence and selection, allow inconclusive outcomes, and test the power of the proposed gate under plausible scenarios. More years or a new provider do not automatically solve these problems.
6. **Practical objectives:** the user rejected $5/week as too slow; the exact acceptable time horizon, breach risk and revised budget remain to be decided if a plausible candidate emerges. More leverage magnifies losses as well as gains and does not improve signal quality.

## 14. Source map and audit coverage

**Start here:** [PHASE 5](https://app.notion.com/p/PHASE-5-3fe41011d3df80af933fdfe8371656b3?pvs=21). This holds the original context, guardrails, selection/backtest guides, rule/spec note, original cleaned data, selection and cost archives, the complete handoff ZIP, START_HERE, ORB autopsy and cleaned later data. The complete handoff contains the three original round archives plus a transparently restored, incomplete audit package; its nine-file SHA256 manifest was checked for this summary. The original archives include code and large data, but this handoff deliberately does not reproduce them.

**Detailed chronological evidence:** [Edge Audit — Research Log](https://app.notion.com/p/Edge-Audit-Research-Log-e7e41e80203548a0b1984a5e757b3369?pvs=21). It contains the 2013–2020 cleaning and ORB replication, USDJPY registration/results, external-evidence and futures reviews, latest FX design, and links to detailed evidence packages. Read its later dated entries: its introductory “setup” checkpoint and earlier recommendations are historical, not the latest status.

**The four user-supplied chat histories:** [Strategy selection](https://app.notion.com/chat?t=3fe41011d3df80c9923400a94e9e2572) · [Backtesting and decision audit](https://app.notion.com/chat?t=40141011d3df808b9bdb00a905e48739) · [Engine measurement and synthetic selector](https://app.notion.com/chat?t=40341011d3df80759e1100a94c67ed68) · [Data cleaning and subsequent research](https://app.notion.com/chat?t=40c41011d3df80c5812300a9af6c719f). The linked [GitHub research history](https://github.com/David27322/quant/blob/main/README.md) may contain additional un-reconciled trials.

**Coverage and honesty:** this summary reviewed the governing text files, START_HERE, the handoff manifest and the three archived round-result summaries; it examined selected full messages and event indexes from all four linked chats and the existing research log, including its later checkpoints. It did **not** individually read every tool event, every entry in every ZIP, every original CSV, or every possible project chat, and it did not independently rerun historical strategy engines or confirm external broker rules. Some earlier return streams, the original complete decision-audit working folder and exact calibration dates are missing. Therefore this is a detailed, source-linked continuation record—not a claim that every historical detail has been independently recovered. Use original logs for exact protocols, dates, seeds, supporting intervals and deeper evidence.

## 15. Safe restart brief for a future session

Read this handoff, then the latest sections of the research log and the original governing files. State which sources and data are available and whether access is incomplete. Carry all known trials and the unreconciled GitHub history; preserve the 2026 reserve and unknown calibration dates. Do not revive stopped candidates, tune old diagnostics, reset the budget or equate a failed gate with proof of no edge.

The current open question is whether an efficient, reliable historical bid/ask route can support the proposed weekly FX basket, or an explicitly revised preliminary proxy, without an excessive collection burden. First check data coverage and feasibility without calculating strategy returns. Be candid about contrary literature, cost mapping and low-power or miscalibrated inference. Present one simple, predeclared protocol and a finite new research budget for approval before any historical performance evaluation. Detailed broker calibration, account simulation, forward demo, account purchase and live trading are separate later decisions—not automatic next steps.