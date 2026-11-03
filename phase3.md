# Phase 3 — AI Strategy Factory (NQ Futures)

## Context

- **Goal:** Independent, profitable algo trading. Near-term — find a real edge, pass a futures prop firm challenge (Topstep/Apex, NQ or MNQ), get funded and sustain. Long-term (Phase 4+) — adaptive multi-strategy, agentic signal/risk/execution layers, diversification.
- **Phase 1–2 (done):** Learned finance/stats/math fundamentals. Built a basic MA+RSI strategy in python — backtest-only, too many assumptions, not viable live. 
- **Setup ready:** Backtrader installed. Kaggle NQ futures dataset on disk.
- **Phase 3 shift:** Stop designing strategies from scratch. Harvest already-documented ORB rule-sets → AI-extract precise specs → AI-code in Backtrader → backtest → aggressively grid-combine → keep only what survives a robustness check + walk-forward → take that into a prop firm challenge.

## Guardrails (apply at every step)

- Simplicity wins — fewer rules/filters beats more, all else equal.
- Risk 0.5–1% of account per trade, fixed fractional. No exceptions.
- Discard any variant with under ~100 trades — not enough sample to judge.
- Nothing reaches Step 8 unless it survives Step 6 **and** Step 7.


## Step-by-Step Plan

### Step 0 — Data prep
- **Do:** Load Kaggle NQ data, check gaps/duplicates, convert timestamps to US/Eastern, build 5/15/30-min resampled feeds from the base data. Note: NQ trades ~23h — ORB conventionally uses RTH open (9:30 AM ET), but keep a Globex-open version of the data available too, since some published variants use that instead.
- **Model:** GPT-5.5
- **Output:** Clean, multi-timeframe Backtrader-ready feeds.

### Step 1 — Harvest ORB variants
- **Do:** Collect 3–5 ORB descriptions (YouTube, forums, Kaufman's *Trading Systems and Methods*) that give actual numbers — range window, stop/target rule, session definition, filters.
- **Model:** Gemini 3.1 Pro
- **Output:** One comparison table of 3–5 ORB variants.

### Step 2 — Extract precise specs
- **Do:** For each variant, extract: instrument, timeframe, entry trigger, stop calc, target calc, position sizing, session (RTH vs Globex open), extra filters. Mark any gap explicitly as "Assumption:" rather than guessing silently.
- **Model:** Opus 4.7
- **Output:** 3–5 unambiguous strategy specs.

### Step 3 — Code as Backtrader strategies
- **Do:** Implement each spec as a `bt.Strategy` class with parameters exposed (range window, stop multiple, target multiple, etc.) so `cerebro.optstrategy()` can sweep them in Step 5.
- **Model:** Sonnet 4.6 (high)
- **Output:** Runnable Backtrader strategy files.

### Step 4 — Baseline backtest
- **Do:** Run each variant on the full cleaned NQ history. Get Sharpe, Calmar, MaxDD, win rate, trade count.
- **Model:** Sonnet 4.6 (high) to run; escalate to Sonnet 4.6 (max thinking) if a result looks too good to be true (likely look-ahead bias or data leakage).
- **Output:** Baseline metrics table. Drop anything under ~100 trades.

### Step 5 — Aggressive combination grid
- **Do:** Take the 1–2 best baseline variants. Build a grid: range window × stop multiple × target multiple × optional filters (VWAP side, ATR threshold, day-of-week). Run all combinations (50–200+) via `cerebro.optstrategy()`.
- **Model:** Opus 4.7 designs the grid (what's worth testing vs redundant) → Sonnet 4.6 (high) codes and runs it.
- **Output:** One results row per combination.

### Step 6 — Robustness review
- **Do:** Don't pick the single best Sharpe. Check whether good results cluster around neighboring parameter values (real edge) vs. one isolated spike (overfit/noise). Bootstrap the top candidates' trade sequences to check if they're statistically distinguishable from random.
- **Model:** GPT-5.5 for the bootstrap/statistical math → Opus 4.8 for the final judgment call.
- **Output:** 1 (max 2) candidate strategy + parameter set, with written rationale for why it's robust.

### Step 7 — Walk-forward validation
- **Do:** Split data ~70/30 by time. Re-run the grid on the first 70%, take the winning params, test untouched on the last 30%. Performance should hold, not collapse.
- **Model:** Sonnet 4.6 (max thinking) for the harness/logic → Opus 4.8 for go/no-go interpretation.
- **Output:** Pass → proceed to Step 8. Fail → back to Step 1 with a different/adjusted variant.

### Step 8 — Path to funded
- **Do:** Paper trade the validated strategy (NQ/MNQ) on Topstep/Apex sim for 1–2 weeks to confirm live execution matches backtest. Confirm your country is eligible. Find a current discount code, buy an evaluation, and pass it — at this point it's a discipline test, not a strategy test. Get funded, sustain.
- **Model:** Sonnet 4.6 (high) only if execution-script tweaks are needed.
- **Output:** Funded account.

## Phase 4 (do not start until Step 8 is done)

Add a second strategy/instrument within the same futures account (GC, 6E, etc.) or London Breakout via FTMO as a second leg. Then: adaptive parameter switching, agentic risk/execution layers, and portfolio-level diversification — built on real trade data from Step 8, not hypothetically.
