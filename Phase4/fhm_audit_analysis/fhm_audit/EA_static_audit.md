# EA static audit — original unchanged

## paid-use blocker
PositionModify/PositionClose boolean results are treated as execution confirmation without checking successful server retcodes.

SetExactBracket and ForceFlatAt1555; MQL5 documentation explicitly distinguishes basic request validation from server execution.

Static code finding; not a reproduced broker failure.

## paid-use blocker
After reported entry success but missing fill/position, code clears pending and returns without setting traded_today; a timer tick can retry during10:31 without a fresh live-position/order reconciliation.

EnterAt1031 actual<=0 || !FindOurPosition path; ProcessClock can invoke again.

Potential duplicate-entry race; not demonstrated live.

## sizing blocker
No account-equity/daily/remaining-floor guard or target/floor sizing caps are implemented.

InpLots is fixed and normalized; no equity-limit checks before Buy/Sell.

Confirmed absent; prior plan's floor_cap policy is NOT in this EA.

## state/logging
Persistent state keys contain symbol+magic but not account login/server; stale expected_exit is not cleared for a new position.

KeyPrefix,LoadState,OnTradeTransaction.

Potential stale state/misleading audit logs after account switches/restarts.

## measurement
CSV lacks executed volume, commission/swap/fees, millisecond execution timing, and entry/exit bid+ask snapshots.

WriteLog header and arguments.

Trade-history export remains necessary; log alone cannot establish all-in execution costs.

## timing
Entry attempts can occur throughout the10:31 minute, including recovery/retry; exact-open backtest is not equivalent to arbitrary within-minute fills.

ProcessClock and EnterAt1031.

Already intentional recovery comment; latency must be measured.

## calendar
EA does not enforce verified Nasdaq cash sessions/early closes.

Clock-time based ProcessClock only.

Any session filter or early-close policy is a proposed strategy/execution change requiring consent.

## limits
Static review/Python DST translation cannot establish compiled MT5 behavior, broker acceptance, restart recovery or network outage safety.



Needs MetaEditor compile plus demo tests.